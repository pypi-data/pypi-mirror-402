# python
from __future__ import annotations

import threading
from websockets.protocol import State
from websockets.sync.client import connect
from websockets.exceptions import WebSocketException, ConnectionClosedOK, ConnectionClosedError

# cache of clients keyed by URI
_clients: dict[str, WebSocketClient] = {}
_clients_lock = threading.Lock()


class WebSocketClient:
    def __init__(self, uri: str):
        self.uri = uri
        self._send_receive_lock = threading.Lock()
        self._disposed = False
        # disable frame size limit
        self.ws = connect(uri=uri, max_size=None)

    @staticmethod
    def create_or_get_client(uri: str, expected_current: WebSocketClient | None = None) -> WebSocketClient:
        """
        If expected_current is None -> add-or-get semantics.
        If expected_current is not None -> recreate semantics (always create new, but dispose old only if it's the expected one).
        """
        with _clients_lock:
            if expected_current is None:
                current = _clients.get(uri)
                if current is not None:
                    if current.ws is not None and current.ws.protocol.state == State.OPEN:
                        return current
                    # Replace stale/broken client
                    try:
                        current.close()
                    except Exception:
                        pass
                    created = WebSocketClient(uri)
                    _clients[uri] = created
                    return created
                # No existing client
                created = WebSocketClient(uri)
                _clients[uri] = created
                return created
            else:
                # Recreate behavior: dispose old only if it matches expected_current, but always create new and store it
                current = _clients.get(uri)
                try:
                    if current is not None and current is expected_current:
                        current.close()
                        _clients.pop(uri, None)
                except Exception:
                    pass
                new_client = WebSocketClient(uri)
                _clients[uri] = new_client
                return new_client

    @staticmethod
    def send_message(uri: str, message: bytes) -> bytes:
        if message is None:
            raise ValueError("message must not be None")

        client = WebSocketClient.create_or_get_client(uri, None)

        last_ex = None
        max_attempts = 2  # initial try + one reconnect attempt

        for attempt in range(max_attempts):
            try:
                with client._send_receive_lock:
                    client.send_byte_array(message)
                    return client.receive_byte_array()
            except (WebSocketException, OSError, RuntimeError, ConnectionClosedOK, ConnectionClosedError) as ex:
                last_ex = ex
                if attempt == max_attempts - 1:
                    break
                client = WebSocketClient.create_or_get_client(uri, client)

        raise last_ex or RuntimeError("SendMessage failed after retries.")

    def send_byte_array(self, message: bytes) -> None:
        if self.ws is None:
            raise RuntimeError("WebSocket is not opened")
        if message is None:
            raise ValueError("message must not be None")
        try:
            # websockets sync client will send full message
            self.ws.send(message)
        except (ConnectionClosedOK, ConnectionClosedError) as ex:
            raise WebSocketException(f"WebSocket send failed: {ex}") from ex

    def receive_byte_array(self) -> bytes:
        if self.ws is None:
            raise RuntimeError("WebSocket is not opened")
        try:
            response = self.ws.recv()
        except (ConnectionClosedOK, ConnectionClosedError) as ex:
            # Mirror C# behavior: close and raise WebSocketException
            try:
                self.close()
            except Exception:
                pass
            raise WebSocketException(f"WebSocket closed by remote endpoint: {ex}") from ex

        if isinstance(response, str):
            return response.encode("utf-8")
        return response

    def close(self) -> None:
        if self.ws is not None:
            try:
                # attempt graceful close; ignore errors
                try:
                    # best-effort close if state suggests open/closing
                    state = None
                    try:
                        state = self.ws.protocol.state
                    except Exception:
                        state = None
                    if state in (State.OPEN, State.CLOSING):
                        try:
                            self.ws.close()
                        except Exception:
                            pass
                    else:
                        try:
                            self.ws.close()
                        except Exception:
                            pass
                finally:
                    pass
            finally:
                self.ws = None
        self._disposed = True

    @staticmethod
    def close_client(uri: str) -> None:
        with _clients_lock:
            client = _clients.pop(uri, None)
        if client is not None:
            client.close()

    @staticmethod
    def get_state(uri: str):
        with _clients_lock:
            client = _clients.get(uri)
        if client is None or client.ws is None:
            return None
        return client.ws.protocol.state

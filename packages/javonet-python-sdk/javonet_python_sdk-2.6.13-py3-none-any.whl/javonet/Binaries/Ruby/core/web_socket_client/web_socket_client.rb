require 'uri'
require 'socket'
require 'openssl'
require 'websocket'

class WebSocketClient
  # Cache: URI(string) -> WebSocketClient
  @clients = {}
  @clients_lock = Mutex.new

  class << self
    # Equivalent to C# SendMessage(Uri, byte[])
    # message can be String (bytes) or Array<Integer 0..255>
    def send_message(url, message)
      raise ArgumentError, "message cannot be nil" if message.nil?

      client = create_or_get_client(url, expected_current: nil)

      last_ex = nil
      max_attempts = 2 # initial try + one reconnect attempt

      max_attempts.times do |attempt|
        begin
          # Serialize send+receive per connection instance (like _sendReceiveLock)
          client.with_send_receive_lock do
            client.send_bytes(message)
            return client.receive_bytes
          end
        rescue Errno::EPIPE, Errno::ECONNRESET, Errno::ETIMEDOUT, IOError, SystemCallError,
          WebSocket::Error => ex
          last_ex = ex
          break if attempt == max_attempts - 1

          # Recreate semantics: only replace if the cached instance equals the one that failed
          client = create_or_get_client(url, expected_current: client)
        end
      end

      raise(last_ex || RuntimeError.new("send_message failed after retries"))
    end

    # Equivalent to C# Close(uri)
    # suppress_close_frame can emulate "do not send CLOSE" during reconnect handling
    def close(url, suppress_close_frame: false)
      @clients_lock.synchronize do
        if (client = @clients[url])
          begin
            client.close(suppress_close_frame: suppress_close_frame)
          ensure
            @clients.delete(url)
          end
        end
      end
    end

    # Equivalent to C# GetState(uri, out state)
    # Returns :OPEN, :CLOSED, or nil if no cached client
    def get_state(url)
      @clients_lock.synchronize do
        c = @clients[url]
        return nil unless c
        c.open? ? :OPEN : :CLOSED
      end
    end

    private

    # Mirrors the C# consolidated CreateOrGetClient(uri, expectedCurrent)
    def create_or_get_client(url, expected_current:)
      @clients_lock.synchronize do
        if expected_current.nil?
          # add-or-get
          if (current = @clients[url])
            if current.open?
              return current
            else
              # Replace stale/broken
              begin current.close(suppress_close_frame: true) rescue nil end
              new_client = new(url)
              @clients[url] = new_client
              return new_client
            end
          end

          created = new(url)
          @clients[url] = created
          created
        else
          # recreate semantics (force replace only if the cached instance is the same object)
          if (current = @clients[url]) && current.equal?(expected_current)
            begin current.close(suppress_close_frame: true) rescue nil end
            @clients.delete(url)
          end

          new_client = new(url)
          @clients[url] = new_client
          new_client
        end
      end
    end
  end

  def initialize(url)
    @uri = URI.parse(url)
    raise "Only ws:// or wss:// URLs are supported" unless %w[ws wss].include?(@uri.scheme)

    @host = @uri.host
    @port = @uri.port || default_port
    @path = (@uri.path.nil? || @uri.path.empty?) ? '/' : @uri.path
    @path += "?#{@uri.query}" if @uri.query

    @send_receive_lock = Mutex.new

    @socket = open_socket
    @handshake = WebSocket::Handshake::Client.new(url: url)
    perform_handshake

    @incoming = WebSocket::Frame::Incoming::Client.new(version: @handshake.version)
  end

  # Serialize send+receive for this connection instance
  def with_send_receive_lock
    @send_receive_lock.synchronize { yield }
  end

  # Send bytes (String bytes or Array of bytes)
  def send_bytes(message)
    data =
      case message
      when String then message.b
      when Array  then message.pack('C*')
      else raise ArgumentError, "Unsupported message type: #{message.class}"
      end

    frame = WebSocket::Frame::Outgoing::Client.new(
      version: @handshake.version,
      data: data,
      type: :binary
    )
    write_all(frame.to_s)
    true
  end

  # Receive a full message payload as Array<Integer> (bytes)
  # Raises on CLOSE like the C# code (instead of returning nil).
  def receive_bytes(timeout: 5)
    deadline = Time.now + timeout
    payload_chunks = []

    loop do
      if (frame = @incoming.next)
        case frame.type
        when :binary, :text, :continuation
          payload_chunks << frame.data
          # Note: if you want to support fragmented continuation properly, you’d track FIN;
          # the websocket gem’s Incoming client typically handles reassembly at this layer.
          return payload_chunks.join.bytes
        when :ping
          send_pong(frame.data)
        when :close
          # Mirror C#: close and throw
          send_close_reply
          raise WebSocket::Error, "WebSocket closed by remote endpoint"
        end
        next
      end

      remaining = deadline - Time.now
      raise Timeout::Error, "WebSocket receive timeout" if remaining <= 0

      if IO.select([@socket], nil, nil, [remaining, 0.05].max)
        chunk = @socket.read_nonblock(64 * 1024, exception: false)
        case chunk
        when nil
          raise EOFError, "peer closed"
        when :wait_readable
          next
        else
          @incoming << chunk
        end
      end
    end
  end

  def open?
    return false if @socket.closed?
    true
  rescue IOError, SystemCallError
    false
  end

  def close(suppress_close_frame: false)
    begin
      send_close_reply unless suppress_close_frame || @socket.closed?
    rescue Errno::EPIPE, Errno::ECONNRESET, IOError, SystemCallError, WebSocket::Error
      # ignore
    ensure
      @socket.close unless @socket.closed?
    end
  end

  private

  def default_port
    @uri.scheme == 'wss' ? 443 : 80
  end

  def open_socket
    tcp = TCPSocket.new(@host, @port)
    tcp.sync = true
    return tcp unless @uri.scheme == 'wss'

    ctx = OpenSSL::SSL::SSLContext.new
    # Production: VERIFY_PEER and trust store/ca_file.
    ctx.set_params(verify_mode: OpenSSL::SSL::VERIFY_NONE)

    ssl = OpenSSL::SSL::SSLSocket.new(tcp, ctx)
    ssl.sync_close = true
    ssl.hostname = @host if ssl.respond_to?(:hostname=)
    ssl.connect
    ssl
  end

  def perform_handshake
    write_all(@handshake.to_s)
    loop do
      break if @handshake.finished?
      raise "WebSocket handshake timeout" unless IO.select([@socket], nil, nil, 5)

      data = @socket.read_nonblock(4096, exception: false)
      case data
      when nil
        break
      when :wait_readable
        next
      else
        @handshake << data
      end
    end

    raise "WebSocket handshake failed!" unless @handshake.finished? && @handshake.valid?
  end

  def write_all(data)
    total = 0
    while total < data.bytesize
      written = @socket.write_nonblock(data.byteslice(total..-1), exception: false)
      case written
      when :wait_writable
        IO.select(nil, [@socket])
      when 0, nil
        raise IOError, "socket closed while writing"
      else
        total += written
      end
    end
  rescue IO::WaitWritable
    IO.select(nil, [@socket])
    retry
  end

  def send_pong(data)
    pong = WebSocket::Frame::Outgoing::Client.new(
      version: @handshake.version, type: :pong, data: data
    )
    write_all(pong.to_s)
  rescue Errno::EPIPE, Errno::ECONNRESET, IOError, SystemCallError
    # ignore
  end

  def send_close_reply
    return if @socket.closed?
    frame = WebSocket::Frame::Outgoing::Client.new(
      version: @handshake.version, type: :close
    )
    write_all(frame.to_s)
  rescue Errno::EPIPE, Errno::ECONNRESET, IOError, SystemCallError
    # ignore
  end
end

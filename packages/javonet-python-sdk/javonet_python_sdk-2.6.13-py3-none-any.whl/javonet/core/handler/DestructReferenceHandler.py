from javonet.core.referenceCache.ReferencesCache import ReferencesCache
from javonet.core.handler.AbstractCommandHandler import *


class DestructReferenceHandler(AbstractCommandHandler):
    def __init__(self):
        self._required_parameters_count = 1

    def process(self, command):
        try:
            payload = command.payload
            if payload is None or len(payload) < self._required_parameters_count:
                return False

            reference_id = payload[0]
            if reference_id is None or not isinstance(reference_id, str):
                return False

            return ReferencesCache().delete_reference(reference_id)
        except Exception:
            raise

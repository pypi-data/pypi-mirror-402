from enum import Enum


class GetSequenceLoadResponse400Error(str, Enum):
    SEQUENCE_IS_ALREADY_RUNNING = "Sequence is already running"
    SEQUENCE_IS_NOT_INITIALIZED = "Sequence is not initialized"
    SEQUENCE_NOT_FOUND = "Sequence not found"

    def __str__(self) -> str:
        return str(self.value)

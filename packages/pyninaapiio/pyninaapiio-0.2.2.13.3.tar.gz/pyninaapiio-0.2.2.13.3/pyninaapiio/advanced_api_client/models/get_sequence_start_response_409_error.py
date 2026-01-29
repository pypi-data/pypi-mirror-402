from enum import Enum


class GetSequenceStartResponse409Error(str, Enum):
    SEQUENCE_IS_ALREADY_RUNNING = "Sequence is already running"
    SEQUENCE_IS_NOT_INITIALIZED = "Sequence is not initialized"

    def __str__(self) -> str:
        return str(self.value)

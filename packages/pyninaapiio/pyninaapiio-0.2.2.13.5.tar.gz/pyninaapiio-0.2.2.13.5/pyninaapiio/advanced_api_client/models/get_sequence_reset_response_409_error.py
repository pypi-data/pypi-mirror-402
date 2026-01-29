from enum import Enum


class GetSequenceResetResponse409Error(str, Enum):
    SEQUENCE_IS_NOT_INITIALIZED = "Sequence is not initialized"

    def __str__(self) -> str:
        return str(self.value)

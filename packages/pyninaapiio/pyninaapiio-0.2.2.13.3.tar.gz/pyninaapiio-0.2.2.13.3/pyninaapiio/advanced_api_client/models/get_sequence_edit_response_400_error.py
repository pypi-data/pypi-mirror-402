from enum import Enum


class GetSequenceEditResponse400Error(str, Enum):
    INVALID_PATH = "Invalid path"
    NEW_VALUE_CANT_BE_NULL = "New value can't be null"
    SEQUENCE_IS_NOT_INITIALIZED = "Sequence is not initialized"

    def __str__(self) -> str:
        return str(self.value)

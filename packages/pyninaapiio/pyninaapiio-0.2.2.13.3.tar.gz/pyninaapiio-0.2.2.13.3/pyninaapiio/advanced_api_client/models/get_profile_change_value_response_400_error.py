from enum import Enum


class GetProfileChangeValueResponse400Error(str, Enum):
    INVALID_PATH = "Invalid path"
    NEW_VALUE_CANT_BE_NULL = "New value can't be null"

    def __str__(self) -> str:
        return str(self.value)

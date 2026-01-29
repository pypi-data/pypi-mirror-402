from enum import Enum


class GetImageIndexImageType(str, Enum):
    BIAS = "BIAS"
    DARK = "DARK"
    FLAT = "FLAT"
    LIGHT = "LIGHT"
    SNAPSHOT = "SNAPSHOT"

    def __str__(self) -> str:
        return str(self.value)

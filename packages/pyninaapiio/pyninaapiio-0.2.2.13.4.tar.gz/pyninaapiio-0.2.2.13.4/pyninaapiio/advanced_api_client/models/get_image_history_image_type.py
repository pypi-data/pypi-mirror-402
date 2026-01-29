from enum import Enum


class GetImageHistoryImageType(str, Enum):
    BIAS = "BIAS"
    DARK = "DARK"
    FLAT = "FLAT"
    LIGHT = "LIGHT"
    SNAPSHOT = "SNAPSHOT"

    def __str__(self) -> str:
        return str(self.value)

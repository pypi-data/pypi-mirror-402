from enum import Enum


class GetImageHistoryResponse200ResponseType0ItemImageType(str, Enum):
    BIAS = "BIAS"
    DARK = "DARK"
    FLAT = "FLAT"
    LIGHT = "LIGHT"
    SNAPSHOT = "SNAPSHOT"

    def __str__(self) -> str:
        return str(self.value)

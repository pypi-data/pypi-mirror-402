from enum import Enum


class ProfileInfoResponseImageFileSettingsXISFCompressionType(str, Enum):
    LZ4 = "LZ4"
    LZ4HC = "LZ4HC"
    NONE = "NONE"
    ZLIB = "ZLIB"

    def __str__(self) -> str:
        return str(self.value)

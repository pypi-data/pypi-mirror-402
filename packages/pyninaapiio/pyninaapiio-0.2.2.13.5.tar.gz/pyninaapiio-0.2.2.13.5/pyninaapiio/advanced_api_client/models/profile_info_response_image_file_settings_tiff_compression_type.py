from enum import Enum


class ProfileInfoResponseImageFileSettingsTIFFCompressionType(str, Enum):
    LZW = "LZW"
    NONE = "NONE"
    ZIP = "ZIP"

    def __str__(self) -> str:
        return str(self.value)

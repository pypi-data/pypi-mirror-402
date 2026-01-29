from enum import Enum


class ProfileInfoResponseImageFileSettingsFITSCompressionType(str, Enum):
    GZIP1 = "GZIP1"
    GZIP2 = "GZIP2"
    HCOMPRESS = "HCOMPRESS"
    NONE = "NONE"
    PLIO = "PLIO"
    RICE = "RICE"

    def __str__(self) -> str:
        return str(self.value)

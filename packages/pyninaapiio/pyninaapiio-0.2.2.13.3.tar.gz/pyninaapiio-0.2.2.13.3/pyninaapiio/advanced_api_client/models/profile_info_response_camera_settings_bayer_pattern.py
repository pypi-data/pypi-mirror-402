from enum import Enum


class ProfileInfoResponseCameraSettingsBayerPattern(str, Enum):
    AUTO = "Auto"
    BGGR = "BGGR"
    BGRG = "BGRG"
    GBGR = "GBGR"
    GBRG = "GBRG"
    GRBG = "GRBG"
    GRGB = "GRGB"
    NONE = "None"
    RGBG = "RGBG"
    RGGB = "RGGB"

    def __str__(self) -> str:
        return str(self.value)

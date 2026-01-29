from enum import Enum


class CameraInfoResponseSensorType(str, Enum):
    BGGR = "BGGR"
    BGRG = "BGRG"
    CMYG = "CMYG"
    CMYG2 = "CMYG2"
    COLOR = "Color"
    GBGR = "GBGR"
    GBRG = "GBRG"
    GRBG = "GRBG"
    GRGB = "GRGB"
    LRGB = "LRGB"
    MONOCHROME = "Monochrome"
    RGBG = "RGBG"
    RGGB = "RGGB"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class MountInfoResponseAlignmentMode(str, Enum):
    ALTAZ = "AltAz"
    GERMANPOLAR = "GermanPolar"
    POLAR = "Polar"

    def __str__(self) -> str:
        return str(self.value)

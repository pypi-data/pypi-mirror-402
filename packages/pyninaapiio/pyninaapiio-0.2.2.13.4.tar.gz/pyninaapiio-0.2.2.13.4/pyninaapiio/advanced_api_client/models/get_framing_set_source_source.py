from enum import Enum


class GetFramingSetSourceSource(str, Enum):
    CACHE = "CACHE"
    ESO = "ESO"
    FILE = "FILE"
    HIPS2FITS = "HIPS2FITS"
    NASA = "NASA"
    SKYATLAS = "SKYATLAS"
    SKYSERVER = "SKYSERVER"
    STSCI = "STSCI"

    def __str__(self) -> str:
        return str(self.value)

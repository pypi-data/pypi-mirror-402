from enum import Enum


class ProfileInfoResponsePlateSolveSettingsPlateSolverType(str, Enum):
    ASPS = "ASPS"
    ASTAP = "ASTAP"
    ASTROMETRY_NET = "ASTROMETRY_NET"
    LOCAL = "LOCAL"
    PINPONT = "PINPONT"
    PLATESOLVE2 = "PLATESOLVE2"
    PLATESOLVE3 = "PLATESOLVE3"
    TSX_IMAGELINK = "TSX_IMAGELINK"

    def __str__(self) -> str:
        return str(self.value)

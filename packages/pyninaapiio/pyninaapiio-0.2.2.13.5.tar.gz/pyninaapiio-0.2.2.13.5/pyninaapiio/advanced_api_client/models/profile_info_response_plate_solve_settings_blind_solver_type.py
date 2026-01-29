from enum import Enum


class ProfileInfoResponsePlateSolveSettingsBlindSolverType(str, Enum):
    ASPS = "ASPS"
    ASTAP = "ASTAP"
    ASTROMETRY_NET = "ASTROMETRY_NET"
    LOCAL = "LOCAL"
    PINPOINT = "PINPOINT"
    PLATESOLVE3 = "PLATESOLVE3"

    def __str__(self) -> str:
        return str(self.value)

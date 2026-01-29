from enum import Enum


class GetAstroUtilMoonSeparationResponse200ResponseMoonPhase(str, Enum):
    FIRSTQUARTER = "FirstQuarter"
    FULLMOON = "FullMoon"
    LASTQUARTER = "LastQuarter"
    NEWMOON = "NewMoon"
    UNKNOWN = "Unknown"
    WANINGCRESCENT = "WaningCrescent"
    WANINGGIBBOUS = "WaningGibbous"
    WAXINGCRESCENT = "WaxingCrescent"
    WAXINGGIBBOUS = "WaxingGibbous"

    def __str__(self) -> str:
        return str(self.value)

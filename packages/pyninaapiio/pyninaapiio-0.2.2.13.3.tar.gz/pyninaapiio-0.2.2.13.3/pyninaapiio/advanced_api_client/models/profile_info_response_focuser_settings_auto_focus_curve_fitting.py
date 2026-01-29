from enum import Enum


class ProfileInfoResponseFocuserSettingsAutoFocusCurveFitting(str, Enum):
    HYPERBOLIC = "HYPERBOLIC"
    PARABOLIC = "PARABOLIC"
    TRENDHYPERBOLIC = "TRENDHYPERBOLIC"
    TRENDLINES = "TRENDLINES"
    TRENDPARABOLIC = "TRENDPARABOLIC"

    def __str__(self) -> str:
        return str(self.value)

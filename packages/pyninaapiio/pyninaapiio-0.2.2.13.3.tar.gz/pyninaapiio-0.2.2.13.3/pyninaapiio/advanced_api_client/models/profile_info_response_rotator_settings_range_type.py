from enum import Enum


class ProfileInfoResponseRotatorSettingsRangeType(str, Enum):
    FULL = "FULL"
    HALF = "HALF"
    QUARTER = "QUARTER"

    def __str__(self) -> str:
        return str(self.value)

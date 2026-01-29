from enum import Enum


class MountInfoResponseTrackingMode(str, Enum):
    CUSTOM = "Custom"
    KING = "King"
    LUNAR = "Lunar"
    SIDERIAL = "Siderial"
    SOLAR = "Solar"
    STOPPED = "Stopped"

    def __str__(self) -> str:
        return str(self.value)

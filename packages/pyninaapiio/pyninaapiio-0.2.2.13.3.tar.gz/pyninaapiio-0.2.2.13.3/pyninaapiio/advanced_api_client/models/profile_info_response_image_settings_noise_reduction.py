from enum import Enum


class ProfileInfoResponseImageSettingsNoiseReduction(str, Enum):
    HIGH = "High"
    HIGHEST = "Highest"
    MEDIAN = "Median"
    NONE = "None"
    NORMAL = "Normal"

    def __str__(self) -> str:
        return str(self.value)

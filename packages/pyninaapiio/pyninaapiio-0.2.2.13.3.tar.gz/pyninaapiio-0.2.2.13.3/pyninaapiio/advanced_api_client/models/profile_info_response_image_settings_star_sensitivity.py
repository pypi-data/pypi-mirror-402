from enum import Enum


class ProfileInfoResponseImageSettingsStarSensitivity(str, Enum):
    HIGH = "High"
    HIGHEST = "Highest"
    NORMAL = "Normal"

    def __str__(self) -> str:
        return str(self.value)

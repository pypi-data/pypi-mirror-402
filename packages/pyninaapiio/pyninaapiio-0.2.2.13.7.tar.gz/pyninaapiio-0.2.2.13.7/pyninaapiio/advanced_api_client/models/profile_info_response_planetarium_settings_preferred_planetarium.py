from enum import Enum


class ProfileInfoResponsePlanetariumSettingsPreferredPlanetarium(str, Enum):
    C2A = "C2A"
    CDC = "CDC"
    HNSKY = "HNSKY"
    SKYTECHX = "SKYTECHX"
    STELLARIUM = "STELLARIUM"
    THESKYX = "THESKYX"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class ProfileInfoResponseTelescopeSettingsTelescopeLocationSyncDirection(str, Enum):
    NOSYNC = "NOSYNC"
    PROMPT = "PROMPT"
    TOAPPLICATION = "TOAPPLICATION"
    TOTELESCOPE = "TOTELESCOPE"

    def __str__(self) -> str:
        return str(self.value)

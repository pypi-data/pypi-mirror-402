from enum import Enum


class ProfileInfoResponseFocuserSettingsBacklashCompensationModel(str, Enum):
    ABSOLUTE = "ABSOLUTE"
    OVERSHOOT = "OVERSHOOT"

    def __str__(self) -> str:
        return str(self.value)

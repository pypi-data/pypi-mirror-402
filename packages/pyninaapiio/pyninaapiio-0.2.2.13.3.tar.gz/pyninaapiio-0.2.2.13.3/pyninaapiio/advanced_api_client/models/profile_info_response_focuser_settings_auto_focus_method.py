from enum import Enum


class ProfileInfoResponseFocuserSettingsAutoFocusMethod(str, Enum):
    CONTRASTDETECTION = "CONTRASTDETECTION"
    STARHFR = "STARHFR"

    def __str__(self) -> str:
        return str(self.value)

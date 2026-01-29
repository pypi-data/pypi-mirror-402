from enum import Enum


class ProfileInfoResponseCameraSettingsRawConverter(str, Enum):
    DCRAW = "DCRAW"
    FREEIMAGE = "FREEIMAGE"

    def __str__(self) -> str:
        return str(self.value)

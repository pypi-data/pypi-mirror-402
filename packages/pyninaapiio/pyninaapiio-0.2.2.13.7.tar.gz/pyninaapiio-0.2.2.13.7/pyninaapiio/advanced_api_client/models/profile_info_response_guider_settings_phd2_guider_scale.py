from enum import Enum


class ProfileInfoResponseGuiderSettingsPHD2GuiderScale(str, Enum):
    ARCSECONDS = "ARCSECONDS"
    PIXELS = "PIXELS"

    def __str__(self) -> str:
        return str(self.value)

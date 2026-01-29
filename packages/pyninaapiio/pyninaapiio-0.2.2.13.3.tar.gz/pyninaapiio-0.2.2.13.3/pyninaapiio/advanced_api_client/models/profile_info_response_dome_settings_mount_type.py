from enum import Enum


class ProfileInfoResponseDomeSettingsMountType(str, Enum):
    EQUATORIAL = "EQUATORIAL"
    FORK_ON_WEDGE = "FORK_ON_WEDGE"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class ProfileInfoResponseCameraSettingsBulbMode(str, Enum):
    NATIVE = "NATIVE"
    SERIALPORT = "SERIALPORT"
    SERIALRELAY = "SERIALRELAY"
    TELESCOPESNAPPORT = "TELESCOPESNAPPORT"

    def __str__(self) -> str:
        return str(self.value)

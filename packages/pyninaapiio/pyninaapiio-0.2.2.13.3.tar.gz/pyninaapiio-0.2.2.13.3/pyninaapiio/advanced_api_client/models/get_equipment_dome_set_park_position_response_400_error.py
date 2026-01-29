from enum import Enum


class GetEquipmentDomeSetParkPositionResponse400Error(str, Enum):
    DOME_CAN_NOT_SET_PARK_POSITION = "Dome can not set park position"
    DOME_NOT_CONNECTED = "Dome not connected"

    def __str__(self) -> str:
        return str(self.value)

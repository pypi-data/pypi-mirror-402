from enum import Enum


class GetEquipmentMountSetParkPositionResponse400Error(str, Enum):
    MOUNT_CAN_NOT_SET_PARK_POSITION = "Mount can not set park position"
    MOUNT_NOT_CONNECTED = "Mount not connected"
    PARK_POSITION_UPDATE_FAILED = "Park position update failed"

    def __str__(self) -> str:
        return str(self.value)

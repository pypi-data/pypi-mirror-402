from enum import Enum


class GetEquipmentMountHomeResponse409Error(str, Enum):
    MOUNT_NOT_CONNECTED = "Mount not connected"
    MOUNT_PARKED = "Mount parked"

    def __str__(self) -> str:
        return str(self.value)

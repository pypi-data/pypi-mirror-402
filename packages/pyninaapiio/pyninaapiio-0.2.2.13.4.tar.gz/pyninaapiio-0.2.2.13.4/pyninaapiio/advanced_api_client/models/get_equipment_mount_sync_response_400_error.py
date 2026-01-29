from enum import Enum


class GetEquipmentMountSyncResponse400Error(str, Enum):
    MOUNT_IS_PARKED = "Mount is parked"
    MOUNT_NOT_CONNECTED = "Mount not connected"

    def __str__(self) -> str:
        return str(self.value)

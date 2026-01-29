from enum import Enum


class GetEquipmentMountTrackingResponse409Error(str, Enum):
    INVALID_TRACKING_MODE = "Invalid tracking mode"
    MOUNT_NOT_CONNECTED = "Mount not connected"
    MOUNT_PARKED = "Mount parked"

    def __str__(self) -> str:
        return str(self.value)

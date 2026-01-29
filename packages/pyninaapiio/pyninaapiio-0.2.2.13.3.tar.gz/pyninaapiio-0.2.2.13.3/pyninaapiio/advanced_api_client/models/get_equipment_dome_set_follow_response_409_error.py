from enum import Enum


class GetEquipmentDomeSetFollowResponse409Error(str, Enum):
    DOME_NOT_CONNECTED = "Dome not connected"
    DOME_SHUTTER_NOT_OPEN = "Dome shutter not open"
    MOUNT_NOT_CONNECTED = "Mount not connected"

    def __str__(self) -> str:
        return str(self.value)

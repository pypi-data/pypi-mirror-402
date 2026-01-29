from enum import Enum


class GetEquipmentMountHomeResponse200Response(str, Enum):
    HOMING = "Homing"
    MOUNT_ALREADY_HOMED = "Mount already homed"

    def __str__(self) -> str:
        return str(self.value)

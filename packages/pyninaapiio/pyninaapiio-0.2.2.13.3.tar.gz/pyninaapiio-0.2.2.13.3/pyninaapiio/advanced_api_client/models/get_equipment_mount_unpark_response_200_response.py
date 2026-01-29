from enum import Enum


class GetEquipmentMountUnparkResponse200Response(str, Enum):
    MOUNT_NOT_PARKED = "Mount not parked"
    UNPARKING = "Unparking"

    def __str__(self) -> str:
        return str(self.value)

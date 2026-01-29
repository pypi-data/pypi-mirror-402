from enum import Enum


class GetEquipmentMountParkResponse200Response(str, Enum):
    MOUNT_ALREADY_PARKED = "Mount already parked"
    PARKING = "Parking"

    def __str__(self) -> str:
        return str(self.value)

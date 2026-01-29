from enum import Enum


class GetEquipmentDomeHomeResponse200Response(str, Enum):
    DOME_ALREADY_HOMED = "Dome already homed"
    HOMING = "Homing"

    def __str__(self) -> str:
        return str(self.value)

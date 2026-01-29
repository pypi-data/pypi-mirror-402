from enum import Enum


class GetEquipmentDomeOpenResponse200Response(str, Enum):
    SHUTTER_ALREADY_OPEN = "Shutter already open"
    SHUTTER_OPENING = "Shutter opening"

    def __str__(self) -> str:
        return str(self.value)

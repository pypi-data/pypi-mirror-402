from enum import Enum


class GetEquipmentDomeSlewResponse409Error(str, Enum):
    DOME_IS_PARKED = "Dome is parked"
    DOME_NOT_CONNECTED = "Dome not connected"

    def __str__(self) -> str:
        return str(self.value)

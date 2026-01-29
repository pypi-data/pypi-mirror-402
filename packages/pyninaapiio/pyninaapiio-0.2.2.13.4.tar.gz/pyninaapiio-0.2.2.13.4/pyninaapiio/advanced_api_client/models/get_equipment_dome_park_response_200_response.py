from enum import Enum


class GetEquipmentDomeParkResponse200Response(str, Enum):
    DOME_ALREADY_PARKED = "Dome already parked"
    PARKING = "Parking"

    def __str__(self) -> str:
        return str(self.value)

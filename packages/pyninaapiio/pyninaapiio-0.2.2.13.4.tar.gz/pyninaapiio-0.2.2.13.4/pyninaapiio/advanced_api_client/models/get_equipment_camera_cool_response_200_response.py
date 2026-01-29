from enum import Enum


class GetEquipmentCameraCoolResponse200Response(str, Enum):
    COOLING_CANCELED = "Cooling canceled"
    COOLING_STARTED = "Cooling started"

    def __str__(self) -> str:
        return str(self.value)

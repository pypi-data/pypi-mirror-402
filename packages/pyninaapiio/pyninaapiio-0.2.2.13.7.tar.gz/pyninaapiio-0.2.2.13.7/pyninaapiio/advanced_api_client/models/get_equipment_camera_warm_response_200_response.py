from enum import Enum


class GetEquipmentCameraWarmResponse200Response(str, Enum):
    WARMING_CANCELED = "Warming canceled"
    WARMING_STARTED = "Warming started"

    def __str__(self) -> str:
        return str(self.value)

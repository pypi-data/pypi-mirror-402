from enum import Enum


class GetEquipmentCameraWarmResponse409Error(str, Enum):
    CAMERA_HAS_NO_TEMPERATURE_CONTROL = "Camera has no temperature control"
    CAMERA_NOT_CONNECTED = "Camera not connected"

    def __str__(self) -> str:
        return str(self.value)

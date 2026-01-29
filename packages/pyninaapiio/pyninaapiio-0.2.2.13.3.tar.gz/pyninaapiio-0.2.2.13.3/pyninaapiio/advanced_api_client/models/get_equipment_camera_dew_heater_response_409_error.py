from enum import Enum


class GetEquipmentCameraDewHeaterResponse409Error(str, Enum):
    CAMERA_HAS_NO_DEW_HEATER = "Camera has no dew heater"
    CAMERA_NOT_CONNECTED = "Camera not connected"

    def __str__(self) -> str:
        return str(self.value)

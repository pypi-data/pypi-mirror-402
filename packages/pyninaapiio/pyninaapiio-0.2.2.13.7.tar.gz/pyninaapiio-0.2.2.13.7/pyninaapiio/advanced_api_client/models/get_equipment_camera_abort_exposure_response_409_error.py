from enum import Enum


class GetEquipmentCameraAbortExposureResponse409Error(str, Enum):
    CAMERA_NOT_CONNECTED = "Camera not connected"
    CAMERA_NOT_EXPOSING = "Camera not exposing"

    def __str__(self) -> str:
        return str(self.value)

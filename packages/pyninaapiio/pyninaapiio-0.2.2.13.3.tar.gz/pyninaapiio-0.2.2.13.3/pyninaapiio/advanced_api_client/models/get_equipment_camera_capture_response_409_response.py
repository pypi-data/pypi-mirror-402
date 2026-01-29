from enum import Enum


class GetEquipmentCameraCaptureResponse409Response(str, Enum):
    CAMERA_CURRENTLY_EXPOSING = "Camera currently exposing"
    CAMERA_NOT_CONNECTED = "Camera not connected"

    def __str__(self) -> str:
        return str(self.value)

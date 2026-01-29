from enum import Enum


class GetEquipmentCameraCaptureResponse200ResponseType0(str, Enum):
    CAPTURE_ALREADY_IN_PROGRESS = "Capture already in progress"
    CAPTURE_STARTED = "Capture started"

    def __str__(self) -> str:
        return str(self.value)

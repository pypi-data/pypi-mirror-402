from enum import Enum


class GetEquipmentCameraAbortExposureResponse200Response(str, Enum):
    CAMERA_NOT_EXPOSING = "Camera not exposing"
    EXPOSURE_ABORTED = "Exposure aborted"

    def __str__(self) -> str:
        return str(self.value)

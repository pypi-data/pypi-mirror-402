from enum import Enum


class GetEquipmentCameraSetBinningResponse409Error(str, Enum):
    BINNING_MUST_BE_SPECIFIED = "Binning must be specified"
    CAMERA_NOT_CONNECTED = "Camera not connected"
    INVALID_BINNING_MODE = "Invalid binning mode"

    def __str__(self) -> str:
        return str(self.value)

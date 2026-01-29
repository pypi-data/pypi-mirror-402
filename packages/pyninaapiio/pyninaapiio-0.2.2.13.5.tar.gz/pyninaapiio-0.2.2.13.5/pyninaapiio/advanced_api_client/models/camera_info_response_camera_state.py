from enum import Enum


class CameraInfoResponseCameraState(str, Enum):
    DOWNLOAD = "Download"
    ERROR = "Error"
    EXPOSING = "Exposing"
    IDLE = "Idle"
    LOADINGFILE = "LoadingFile"
    NOSTATE = "NoState"
    READING = "Reading"
    WAITING = "Waiting"

    def __str__(self) -> str:
        return str(self.value)

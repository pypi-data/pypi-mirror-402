from enum import Enum


class DomeInfoResponseShutterStatus(str, Enum):
    SHUTTERCLOSED = "ShutterClosed"
    SHUTTERCLOSING = "ShutterClosing"
    SHUTTERERROR = "ShutterError"
    SHUTTERNONE = "ShutterNone"
    SHUTTEROPEN = "ShutterOpen"
    SHUTTEROPENING = "ShutterOpening"

    def __str__(self) -> str:
        return str(self.value)

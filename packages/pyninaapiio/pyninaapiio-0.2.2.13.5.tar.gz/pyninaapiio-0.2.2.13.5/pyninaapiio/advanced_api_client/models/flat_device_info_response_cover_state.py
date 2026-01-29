from enum import Enum


class FlatDeviceInfoResponseCoverState(str, Enum):
    CLOSED = "Closed"
    ERROR = "Error"
    NEITHEROPENNORCLOSED = "NeitherOpenNorClosed"
    NOTPRESENT = "NotPresent"
    OPEN = "Open"
    UNKNOWN = "Unknown"

    def __str__(self) -> str:
        return str(self.value)

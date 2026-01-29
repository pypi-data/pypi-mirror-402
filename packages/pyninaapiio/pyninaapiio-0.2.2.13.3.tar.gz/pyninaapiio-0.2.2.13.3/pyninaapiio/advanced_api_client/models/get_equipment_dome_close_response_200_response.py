from enum import Enum


class GetEquipmentDomeCloseResponse200Response(str, Enum):
    SHUTTER_ALREADY_CLOSED = "Shutter already closed"
    SHUTTER_CLOSING = "Shutter closing"

    def __str__(self) -> str:
        return str(self.value)

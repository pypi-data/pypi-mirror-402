from enum import Enum


class GetEquipmentFocuserAutoFocusResponse200Response(str, Enum):
    AUTOFOCUS_CANCELED = "Autofocus canceled"
    AUTOFOCUS_STARTED = "Autofocus started"

    def __str__(self) -> str:
        return str(self.value)

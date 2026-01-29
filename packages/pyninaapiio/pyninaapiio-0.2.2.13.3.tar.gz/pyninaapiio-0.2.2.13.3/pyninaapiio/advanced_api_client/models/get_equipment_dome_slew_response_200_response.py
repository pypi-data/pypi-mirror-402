from enum import Enum


class GetEquipmentDomeSlewResponse200Response(str, Enum):
    DOME_SLEW_FINISHED = "Dome Slew finished"
    DOME_SLEW_STARTED = "Dome Slew Started"

    def __str__(self) -> str:
        return str(self.value)

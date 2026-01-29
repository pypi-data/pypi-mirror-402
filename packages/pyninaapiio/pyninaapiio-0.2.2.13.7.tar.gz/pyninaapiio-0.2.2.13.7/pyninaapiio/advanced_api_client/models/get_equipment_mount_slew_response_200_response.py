from enum import Enum


class GetEquipmentMountSlewResponse200Response(str, Enum):
    SLEW_FAILED = "Slew failed"
    SLEW_FINISHED = "Slew finished"
    STARTED_SLEW = "Started Slew"

    def __str__(self) -> str:
        return str(self.value)

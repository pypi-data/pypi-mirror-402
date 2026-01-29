from enum import Enum


class GetFramingSlewResponse200Response(str, Enum):
    SLEW_FINISHED = "Slew finished"
    SLEW_STARTED = "Slew started"

    def __str__(self) -> str:
        return str(self.value)

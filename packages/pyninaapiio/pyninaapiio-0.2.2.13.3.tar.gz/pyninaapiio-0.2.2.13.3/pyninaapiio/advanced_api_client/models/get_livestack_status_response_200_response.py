from enum import Enum


class GetLivestackStatusResponse200Response(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return str(self.value)

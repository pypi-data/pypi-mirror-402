from enum import Enum


class GetFlatsStatusResponse200ResponseState(str, Enum):
    FINISHED = "Finished"
    RUNNING = "Running"

    def __str__(self) -> str:
        return str(self.value)

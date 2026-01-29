from enum import Enum


class MountInfoResponseSideOfPier(str, Enum):
    PIEREAST = "pierEast"
    PIERUNKNOWN = "pierUnknown"
    PIERWEST = "pierWest"

    def __str__(self) -> str:
        return str(self.value)

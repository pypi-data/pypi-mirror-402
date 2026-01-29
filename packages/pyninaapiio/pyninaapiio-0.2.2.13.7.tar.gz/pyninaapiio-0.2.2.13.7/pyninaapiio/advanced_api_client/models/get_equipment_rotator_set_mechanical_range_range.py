from enum import Enum


class GetEquipmentRotatorSetMechanicalRangeRange(str, Enum):
    FULL = "full"
    HALF = "half"
    QUARTER = "quarter"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class GetEquipmentFilterwheelChangeFilterResponse409Error(str, Enum):
    FILTERWHEEL_NOT_CONNECTED = "Filterwheel not connected"
    FILTER_NOT_AVAILABLE = "Filter not available"

    def __str__(self) -> str:
        return str(self.value)

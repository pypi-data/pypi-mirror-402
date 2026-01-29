from enum import Enum


class GetFlatsTrainedFlatResponse400Error(str, Enum):
    BINNING_NOT_AVAILABLE = "Binning not available"
    FILTER_NOT_AVAILABLE = "Filter not available"
    INVALID_GAIN = "Invalid gain"
    INVALID_OFFSET = "Invalid offset"
    ISSUES_FOUND = "Issues found"
    PROCESS_ALREADY_RUNNING = "Process already running"

    def __str__(self) -> str:
        return str(self.value)

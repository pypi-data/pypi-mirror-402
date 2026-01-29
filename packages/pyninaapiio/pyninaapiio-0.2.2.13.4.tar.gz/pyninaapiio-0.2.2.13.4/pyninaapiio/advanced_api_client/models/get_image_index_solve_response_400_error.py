from enum import Enum


class GetImageIndexSolveResponse400Error(str, Enum):
    INDEX_OUT_OF_RANGE = "Index out of range"
    NO_IMAGES_AVAILABLE = "No images available"

    def __str__(self) -> str:
        return str(self.value)

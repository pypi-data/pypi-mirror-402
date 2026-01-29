from enum import Enum


class GetFramingSlewSlewOption(str, Enum):
    CENTER = "Center"
    ROTATE = "Rotate"

    def __str__(self) -> str:
        return str(self.value)

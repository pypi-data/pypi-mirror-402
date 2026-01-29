from enum import Enum


class GuiderInfoResponseState(str, Enum):
    CALIBRATING = "Calibrating"
    GUIDING = "Guiding"
    LOOPING = "Looping"
    LOSTLOCK = "LostLock"
    STOPPED = "Stopped"

    def __str__(self) -> str:
        return str(self.value)

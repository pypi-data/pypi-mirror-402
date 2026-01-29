from enum import Enum


class MountInfoResponseCoordinatesEpoch(str, Enum):
    B1950 = "B1950"
    J2000 = "J2000"
    J2050 = "J2050"
    JNOW = "JNOW"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class ProfileInfoResponseFocuserSettingsContrastDetectionMethod(str, Enum):
    LAPLACE = "Laplace"
    SOBEL = "Sobel"
    STATISTICS = "Statistics"

    def __str__(self) -> str:
        return str(self.value)

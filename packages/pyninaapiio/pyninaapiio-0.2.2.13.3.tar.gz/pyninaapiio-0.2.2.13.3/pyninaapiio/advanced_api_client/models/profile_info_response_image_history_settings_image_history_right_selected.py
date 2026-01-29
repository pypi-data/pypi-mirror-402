from enum import Enum


class ProfileInfoResponseImageHistorySettingsImageHistoryRightSelected(str, Enum):
    HFR = "HFR"
    MAD = "MAD"
    MEAN = "Mean"
    MEDIAN = "Median"
    NONE = "NONE"
    RMS = "Rms"
    STARS = "Stars"
    STDEV = "StDev"
    TEMPERATURE = "Temperature"

    def __str__(self) -> str:
        return str(self.value)

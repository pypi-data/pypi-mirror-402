from enum import Enum


class GetApplicationSwitchTabTab(str, Enum):
    EQUIPMENT = "equipment"
    FLATWIZARD = "flatwizard"
    FRAMING = "framing"
    IMAGING = "imaging"
    OPTIONS = "options"
    SEQUENCER = "sequencer"
    SKYATLAS = "skyatlas"

    def __str__(self) -> str:
        return str(self.value)

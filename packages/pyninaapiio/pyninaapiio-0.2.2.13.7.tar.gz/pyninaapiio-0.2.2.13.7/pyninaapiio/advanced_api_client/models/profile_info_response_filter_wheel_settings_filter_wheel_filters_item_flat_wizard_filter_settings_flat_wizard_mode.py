from enum import Enum


class ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsFlatWizardMode(str, Enum):
    DYNAMICBRIGHTNESS = "DYNAMICBRIGHTNESS"
    DYNAMICEXPOSURE = "DYNAMICEXPOSURE"
    SKYFLAT = "SKYFLAT"

    def __str__(self) -> str:
        return str(self.value)

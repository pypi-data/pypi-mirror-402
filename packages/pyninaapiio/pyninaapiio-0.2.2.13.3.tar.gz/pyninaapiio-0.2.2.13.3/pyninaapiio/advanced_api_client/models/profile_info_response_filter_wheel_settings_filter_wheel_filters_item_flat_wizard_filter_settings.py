from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item_flat_wizard_filter_settings_flat_wizard_mode import (
    ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsFlatWizardMode,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item_flat_wizard_filter_settings_binning import (
        ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsBinning,
    )


T = TypeVar("T", bound="ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettings")


@_attrs_define
class ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettings:
    """
    Attributes:
        flat_wizard_mode (Union[Unset,
            ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsFlatWizardMode]):
        histogram_mean_target (Union[Unset, float]):
        histogram_tolerance (Union[Unset, float]):
        max_flat_exposure_time (Union[Unset, int]):
        min_flat_exposure_time (Union[Unset, float]):
        max_absolute_flat_device_brightness (Union[Unset, int]):
        min_absolute_flat_device_brightness (Union[Unset, int]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):
        binning (Union[Unset,
            ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsBinning]):
    """

    flat_wizard_mode: Union[
        Unset, ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsFlatWizardMode
    ] = UNSET
    histogram_mean_target: Union[Unset, float] = UNSET
    histogram_tolerance: Union[Unset, float] = UNSET
    max_flat_exposure_time: Union[Unset, int] = UNSET
    min_flat_exposure_time: Union[Unset, float] = UNSET
    max_absolute_flat_device_brightness: Union[Unset, int] = UNSET
    min_absolute_flat_device_brightness: Union[Unset, int] = UNSET
    gain: Union[Unset, int] = UNSET
    offset: Union[Unset, int] = UNSET
    binning: Union[
        Unset, "ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsBinning"
    ] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        flat_wizard_mode: Union[Unset, str] = UNSET
        if not isinstance(self.flat_wizard_mode, Unset):
            flat_wizard_mode = self.flat_wizard_mode.value

        histogram_mean_target = self.histogram_mean_target

        histogram_tolerance = self.histogram_tolerance

        max_flat_exposure_time = self.max_flat_exposure_time

        min_flat_exposure_time = self.min_flat_exposure_time

        max_absolute_flat_device_brightness = self.max_absolute_flat_device_brightness

        min_absolute_flat_device_brightness = self.min_absolute_flat_device_brightness

        gain = self.gain

        offset = self.offset

        binning: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.binning, Unset):
            binning = self.binning.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if flat_wizard_mode is not UNSET:
            field_dict["FlatWizardMode"] = flat_wizard_mode
        if histogram_mean_target is not UNSET:
            field_dict["HistogramMeanTarget"] = histogram_mean_target
        if histogram_tolerance is not UNSET:
            field_dict["HistogramTolerance"] = histogram_tolerance
        if max_flat_exposure_time is not UNSET:
            field_dict["MaxFlatExposureTime"] = max_flat_exposure_time
        if min_flat_exposure_time is not UNSET:
            field_dict["MinFlatExposureTime"] = min_flat_exposure_time
        if max_absolute_flat_device_brightness is not UNSET:
            field_dict["MaxAbsoluteFlatDeviceBrightness"] = max_absolute_flat_device_brightness
        if min_absolute_flat_device_brightness is not UNSET:
            field_dict["MinAbsoluteFlatDeviceBrightness"] = min_absolute_flat_device_brightness
        if gain is not UNSET:
            field_dict["Gain"] = gain
        if offset is not UNSET:
            field_dict["Offset"] = offset
        if binning is not UNSET:
            field_dict["Binning"] = binning

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item_flat_wizard_filter_settings_binning import (
            ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsBinning,
        )

        d = src_dict.copy()
        _flat_wizard_mode = d.pop("FlatWizardMode", UNSET)
        flat_wizard_mode: Union[
            Unset, ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsFlatWizardMode
        ]
        if isinstance(_flat_wizard_mode, Unset):
            flat_wizard_mode = UNSET
        else:
            flat_wizard_mode = (
                ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsFlatWizardMode(
                    _flat_wizard_mode
                )
            )

        histogram_mean_target = d.pop("HistogramMeanTarget", UNSET)

        histogram_tolerance = d.pop("HistogramTolerance", UNSET)

        max_flat_exposure_time = d.pop("MaxFlatExposureTime", UNSET)

        min_flat_exposure_time = d.pop("MinFlatExposureTime", UNSET)

        max_absolute_flat_device_brightness = d.pop("MaxAbsoluteFlatDeviceBrightness", UNSET)

        min_absolute_flat_device_brightness = d.pop("MinAbsoluteFlatDeviceBrightness", UNSET)

        gain = d.pop("Gain", UNSET)

        offset = d.pop("Offset", UNSET)

        _binning = d.pop("Binning", UNSET)
        binning: Union[
            Unset, ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsBinning
        ]
        if isinstance(_binning, Unset):
            binning = UNSET
        else:
            binning = (
                ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettingsBinning.from_dict(
                    _binning
                )
            )

        profile_info_response_filter_wheel_settings_filter_wheel_filters_item_flat_wizard_filter_settings = cls(
            flat_wizard_mode=flat_wizard_mode,
            histogram_mean_target=histogram_mean_target,
            histogram_tolerance=histogram_tolerance,
            max_flat_exposure_time=max_flat_exposure_time,
            min_flat_exposure_time=min_flat_exposure_time,
            max_absolute_flat_device_brightness=max_absolute_flat_device_brightness,
            min_absolute_flat_device_brightness=min_absolute_flat_device_brightness,
            gain=gain,
            offset=offset,
            binning=binning,
        )

        profile_info_response_filter_wheel_settings_filter_wheel_filters_item_flat_wizard_filter_settings.additional_properties = d
        return profile_info_response_filter_wheel_settings_filter_wheel_filters_item_flat_wizard_filter_settings

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

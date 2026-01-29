from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.filter_info_response_flat_wizard_filter_settings_binning import (
        FilterInfoResponseFlatWizardFilterSettingsBinning,
    )


T = TypeVar("T", bound="FilterInfoResponseFlatWizardFilterSettings")


@_attrs_define
class FilterInfoResponseFlatWizardFilterSettings:
    """
    Attributes:
        flat_wizard_mode (int):
        histogram_mean_target (float):
        histogram_tolerance (float):
        max_flat_exposure_time (int):
        min_flat_exposure_time (float):
        max_absolute_flat_device_brightness (int):
        min_absolute_flat_device_brightness (int):
        gain (int):
        offset (int):
        binning (FilterInfoResponseFlatWizardFilterSettingsBinning):
    """

    flat_wizard_mode: int
    histogram_mean_target: float
    histogram_tolerance: float
    max_flat_exposure_time: int
    min_flat_exposure_time: float
    max_absolute_flat_device_brightness: int
    min_absolute_flat_device_brightness: int
    gain: int
    offset: int
    binning: "FilterInfoResponseFlatWizardFilterSettingsBinning"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        flat_wizard_mode = self.flat_wizard_mode

        histogram_mean_target = self.histogram_mean_target

        histogram_tolerance = self.histogram_tolerance

        max_flat_exposure_time = self.max_flat_exposure_time

        min_flat_exposure_time = self.min_flat_exposure_time

        max_absolute_flat_device_brightness = self.max_absolute_flat_device_brightness

        min_absolute_flat_device_brightness = self.min_absolute_flat_device_brightness

        gain = self.gain

        offset = self.offset

        binning = self.binning.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "FlatWizardMode": flat_wizard_mode,
                "HistogramMeanTarget": histogram_mean_target,
                "HistogramTolerance": histogram_tolerance,
                "MaxFlatExposureTime": max_flat_exposure_time,
                "MinFlatExposureTime": min_flat_exposure_time,
                "MaxAbsoluteFlatDeviceBrightness": max_absolute_flat_device_brightness,
                "MinAbsoluteFlatDeviceBrightness": min_absolute_flat_device_brightness,
                "Gain": gain,
                "Offset": offset,
                "Binning": binning,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.filter_info_response_flat_wizard_filter_settings_binning import (
            FilterInfoResponseFlatWizardFilterSettingsBinning,
        )

        d = src_dict.copy()
        flat_wizard_mode = d.pop("FlatWizardMode")

        histogram_mean_target = d.pop("HistogramMeanTarget")

        histogram_tolerance = d.pop("HistogramTolerance")

        max_flat_exposure_time = d.pop("MaxFlatExposureTime")

        min_flat_exposure_time = d.pop("MinFlatExposureTime")

        max_absolute_flat_device_brightness = d.pop("MaxAbsoluteFlatDeviceBrightness")

        min_absolute_flat_device_brightness = d.pop("MinAbsoluteFlatDeviceBrightness")

        gain = d.pop("Gain")

        offset = d.pop("Offset")

        binning = FilterInfoResponseFlatWizardFilterSettingsBinning.from_dict(d.pop("Binning"))

        filter_info_response_flat_wizard_filter_settings = cls(
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

        filter_info_response_flat_wizard_filter_settings.additional_properties = d
        return filter_info_response_flat_wizard_filter_settings

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

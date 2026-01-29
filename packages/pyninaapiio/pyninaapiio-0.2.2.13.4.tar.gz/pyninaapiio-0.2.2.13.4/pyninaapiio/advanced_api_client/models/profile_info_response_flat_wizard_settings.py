from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_flat_wizard_settings_flat_wizard_mode import (
    ProfileInfoResponseFlatWizardSettingsFlatWizardMode,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseFlatWizardSettings")


@_attrs_define
class ProfileInfoResponseFlatWizardSettings:
    """
    Attributes:
        flat_count (Union[Unset, int]):
        histogram_mean_target (Union[Unset, float]):
        histogram_tolerance (Union[Unset, float]):
        dark_flat_count (Union[Unset, int]):
        open_for_dark_flats (Union[Unset, bool]):
        altitude_site (Union[Unset, int]):
        flat_wizard_mode (Union[Unset, ProfileInfoResponseFlatWizardSettingsFlatWizardMode]):
    """

    flat_count: Union[Unset, int] = UNSET
    histogram_mean_target: Union[Unset, float] = UNSET
    histogram_tolerance: Union[Unset, float] = UNSET
    dark_flat_count: Union[Unset, int] = UNSET
    open_for_dark_flats: Union[Unset, bool] = UNSET
    altitude_site: Union[Unset, int] = UNSET
    flat_wizard_mode: Union[Unset, ProfileInfoResponseFlatWizardSettingsFlatWizardMode] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        flat_count = self.flat_count

        histogram_mean_target = self.histogram_mean_target

        histogram_tolerance = self.histogram_tolerance

        dark_flat_count = self.dark_flat_count

        open_for_dark_flats = self.open_for_dark_flats

        altitude_site = self.altitude_site

        flat_wizard_mode: Union[Unset, str] = UNSET
        if not isinstance(self.flat_wizard_mode, Unset):
            flat_wizard_mode = self.flat_wizard_mode.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if flat_count is not UNSET:
            field_dict["FlatCount"] = flat_count
        if histogram_mean_target is not UNSET:
            field_dict["HistogramMeanTarget"] = histogram_mean_target
        if histogram_tolerance is not UNSET:
            field_dict["HistogramTolerance"] = histogram_tolerance
        if dark_flat_count is not UNSET:
            field_dict["DarkFlatCount"] = dark_flat_count
        if open_for_dark_flats is not UNSET:
            field_dict["OpenForDarkFlats"] = open_for_dark_flats
        if altitude_site is not UNSET:
            field_dict["AltitudeSite"] = altitude_site
        if flat_wizard_mode is not UNSET:
            field_dict["FlatWizardMode"] = flat_wizard_mode

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        flat_count = d.pop("FlatCount", UNSET)

        histogram_mean_target = d.pop("HistogramMeanTarget", UNSET)

        histogram_tolerance = d.pop("HistogramTolerance", UNSET)

        dark_flat_count = d.pop("DarkFlatCount", UNSET)

        open_for_dark_flats = d.pop("OpenForDarkFlats", UNSET)

        altitude_site = d.pop("AltitudeSite", UNSET)

        _flat_wizard_mode = d.pop("FlatWizardMode", UNSET)
        flat_wizard_mode: Union[Unset, ProfileInfoResponseFlatWizardSettingsFlatWizardMode]
        if isinstance(_flat_wizard_mode, Unset):
            flat_wizard_mode = UNSET
        else:
            flat_wizard_mode = ProfileInfoResponseFlatWizardSettingsFlatWizardMode(_flat_wizard_mode)

        profile_info_response_flat_wizard_settings = cls(
            flat_count=flat_count,
            histogram_mean_target=histogram_mean_target,
            histogram_tolerance=histogram_tolerance,
            dark_flat_count=dark_flat_count,
            open_for_dark_flats=open_for_dark_flats,
            altitude_site=altitude_site,
            flat_wizard_mode=flat_wizard_mode,
        )

        profile_info_response_flat_wizard_settings.additional_properties = d
        return profile_info_response_flat_wizard_settings

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

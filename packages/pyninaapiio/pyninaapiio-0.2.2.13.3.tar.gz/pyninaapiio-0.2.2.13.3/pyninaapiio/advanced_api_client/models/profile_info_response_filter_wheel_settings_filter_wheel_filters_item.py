from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item_auto_focus_binning import (
        ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemAutoFocusBinning,
    )
    from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item_flat_wizard_filter_settings import (
        ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettings,
    )


T = TypeVar("T", bound="ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItem")


@_attrs_define
class ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItem:
    """
    Attributes:
        name (Union[Unset, str]):
        focus_offset (Union[Unset, int]):
        position (Union[Unset, int]):
        auto_focus_exposure_time (Union[Unset, int]):
        auto_focus_filter (Union[Unset, bool]):
        flat_wizard_filter_settings (Union[Unset,
            ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettings]):
        auto_focus_binning (Union[Unset, ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemAutoFocusBinning]):
        auto_focus_gain (Union[Unset, int]):
        auto_focus_offset (Union[Unset, int]):
    """

    name: Union[Unset, str] = UNSET
    focus_offset: Union[Unset, int] = UNSET
    position: Union[Unset, int] = UNSET
    auto_focus_exposure_time: Union[Unset, int] = UNSET
    auto_focus_filter: Union[Unset, bool] = UNSET
    flat_wizard_filter_settings: Union[
        Unset, "ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettings"
    ] = UNSET
    auto_focus_binning: Union[Unset, "ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemAutoFocusBinning"] = (
        UNSET
    )
    auto_focus_gain: Union[Unset, int] = UNSET
    auto_focus_offset: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        focus_offset = self.focus_offset

        position = self.position

        auto_focus_exposure_time = self.auto_focus_exposure_time

        auto_focus_filter = self.auto_focus_filter

        flat_wizard_filter_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.flat_wizard_filter_settings, Unset):
            flat_wizard_filter_settings = self.flat_wizard_filter_settings.to_dict()

        auto_focus_binning: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.auto_focus_binning, Unset):
            auto_focus_binning = self.auto_focus_binning.to_dict()

        auto_focus_gain = self.auto_focus_gain

        auto_focus_offset = self.auto_focus_offset

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["Name"] = name
        if focus_offset is not UNSET:
            field_dict["FocusOffset"] = focus_offset
        if position is not UNSET:
            field_dict["Position"] = position
        if auto_focus_exposure_time is not UNSET:
            field_dict["AutoFocusExposureTime"] = auto_focus_exposure_time
        if auto_focus_filter is not UNSET:
            field_dict["AutoFocusFilter"] = auto_focus_filter
        if flat_wizard_filter_settings is not UNSET:
            field_dict["FlatWizardFilterSettings"] = flat_wizard_filter_settings
        if auto_focus_binning is not UNSET:
            field_dict["AutoFocusBinning"] = auto_focus_binning
        if auto_focus_gain is not UNSET:
            field_dict["AutoFocusGain"] = auto_focus_gain
        if auto_focus_offset is not UNSET:
            field_dict["AutoFocusOffset"] = auto_focus_offset

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item_auto_focus_binning import (
            ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemAutoFocusBinning,
        )
        from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item_flat_wizard_filter_settings import (
            ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettings,
        )

        d = src_dict.copy()
        name = d.pop("Name", UNSET)

        focus_offset = d.pop("FocusOffset", UNSET)

        position = d.pop("Position", UNSET)

        auto_focus_exposure_time = d.pop("AutoFocusExposureTime", UNSET)

        auto_focus_filter = d.pop("AutoFocusFilter", UNSET)

        _flat_wizard_filter_settings = d.pop("FlatWizardFilterSettings", UNSET)
        flat_wizard_filter_settings: Union[
            Unset, ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettings
        ]
        if isinstance(_flat_wizard_filter_settings, Unset):
            flat_wizard_filter_settings = UNSET
        else:
            flat_wizard_filter_settings = (
                ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemFlatWizardFilterSettings.from_dict(
                    _flat_wizard_filter_settings
                )
            )

        _auto_focus_binning = d.pop("AutoFocusBinning", UNSET)
        auto_focus_binning: Union[Unset, ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemAutoFocusBinning]
        if isinstance(_auto_focus_binning, Unset):
            auto_focus_binning = UNSET
        else:
            auto_focus_binning = ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItemAutoFocusBinning.from_dict(
                _auto_focus_binning
            )

        auto_focus_gain = d.pop("AutoFocusGain", UNSET)

        auto_focus_offset = d.pop("AutoFocusOffset", UNSET)

        profile_info_response_filter_wheel_settings_filter_wheel_filters_item = cls(
            name=name,
            focus_offset=focus_offset,
            position=position,
            auto_focus_exposure_time=auto_focus_exposure_time,
            auto_focus_filter=auto_focus_filter,
            flat_wizard_filter_settings=flat_wizard_filter_settings,
            auto_focus_binning=auto_focus_binning,
            auto_focus_gain=auto_focus_gain,
            auto_focus_offset=auto_focus_offset,
        )

        profile_info_response_filter_wheel_settings_filter_wheel_filters_item.additional_properties = d
        return profile_info_response_filter_wheel_settings_filter_wheel_filters_item

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

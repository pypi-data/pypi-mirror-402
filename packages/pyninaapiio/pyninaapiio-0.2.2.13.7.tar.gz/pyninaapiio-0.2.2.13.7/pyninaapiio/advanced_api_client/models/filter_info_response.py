from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.filter_info_response_auto_focus_binning import FilterInfoResponseAutoFocusBinning
    from ..models.filter_info_response_flat_wizard_filter_settings import FilterInfoResponseFlatWizardFilterSettings


T = TypeVar("T", bound="FilterInfoResponse")


@_attrs_define
class FilterInfoResponse:
    """
    Attributes:
        name (str):
        focus_offset (int):
        position (int):
        auto_focus_exposure_time (int):
        auto_focus_filter (bool):
        flat_wizard_filter_settings (FilterInfoResponseFlatWizardFilterSettings):
        auto_focus_binning (FilterInfoResponseAutoFocusBinning):
        auto_focus_gain (int):
        auto_focus_offset (int):
    """

    name: str
    focus_offset: int
    position: int
    auto_focus_exposure_time: int
    auto_focus_filter: bool
    flat_wizard_filter_settings: "FilterInfoResponseFlatWizardFilterSettings"
    auto_focus_binning: "FilterInfoResponseAutoFocusBinning"
    auto_focus_gain: int
    auto_focus_offset: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        focus_offset = self.focus_offset

        position = self.position

        auto_focus_exposure_time = self.auto_focus_exposure_time

        auto_focus_filter = self.auto_focus_filter

        flat_wizard_filter_settings = self.flat_wizard_filter_settings.to_dict()

        auto_focus_binning = self.auto_focus_binning.to_dict()

        auto_focus_gain = self.auto_focus_gain

        auto_focus_offset = self.auto_focus_offset

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Name": name,
                "FocusOffset": focus_offset,
                "Position": position,
                "AutoFocusExposureTime": auto_focus_exposure_time,
                "AutoFocusFilter": auto_focus_filter,
                "FlatWizardFilterSettings": flat_wizard_filter_settings,
                "AutoFocusBinning": auto_focus_binning,
                "AutoFocusGain": auto_focus_gain,
                "AutoFocusOffset": auto_focus_offset,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.filter_info_response_auto_focus_binning import FilterInfoResponseAutoFocusBinning
        from ..models.filter_info_response_flat_wizard_filter_settings import FilterInfoResponseFlatWizardFilterSettings

        d = src_dict.copy()
        name = d.pop("Name")

        focus_offset = d.pop("FocusOffset")

        position = d.pop("Position")

        auto_focus_exposure_time = d.pop("AutoFocusExposureTime")

        auto_focus_filter = d.pop("AutoFocusFilter")

        flat_wizard_filter_settings = FilterInfoResponseFlatWizardFilterSettings.from_dict(
            d.pop("FlatWizardFilterSettings")
        )

        auto_focus_binning = FilterInfoResponseAutoFocusBinning.from_dict(d.pop("AutoFocusBinning"))

        auto_focus_gain = d.pop("AutoFocusGain")

        auto_focus_offset = d.pop("AutoFocusOffset")

        filter_info_response = cls(
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

        filter_info_response.additional_properties = d
        return filter_info_response

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

from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_image_history_settings_image_history_left_selected import (
    ProfileInfoResponseImageHistorySettingsImageHistoryLeftSelected,
)
from ..models.profile_info_response_image_history_settings_image_history_right_selected import (
    ProfileInfoResponseImageHistorySettingsImageHistoryRightSelected,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseImageHistorySettings")


@_attrs_define
class ProfileInfoResponseImageHistorySettings:
    """
    Attributes:
        image_history_left_selected (Union[Unset, ProfileInfoResponseImageHistorySettingsImageHistoryLeftSelected]):
        image_history_right_selected (Union[Unset, ProfileInfoResponseImageHistorySettingsImageHistoryRightSelected]):
    """

    image_history_left_selected: Union[Unset, ProfileInfoResponseImageHistorySettingsImageHistoryLeftSelected] = UNSET
    image_history_right_selected: Union[Unset, ProfileInfoResponseImageHistorySettingsImageHistoryRightSelected] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        image_history_left_selected: Union[Unset, str] = UNSET
        if not isinstance(self.image_history_left_selected, Unset):
            image_history_left_selected = self.image_history_left_selected.value

        image_history_right_selected: Union[Unset, str] = UNSET
        if not isinstance(self.image_history_right_selected, Unset):
            image_history_right_selected = self.image_history_right_selected.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if image_history_left_selected is not UNSET:
            field_dict["ImageHistoryLeftSelected"] = image_history_left_selected
        if image_history_right_selected is not UNSET:
            field_dict["ImageHistoryRightSelected"] = image_history_right_selected

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        _image_history_left_selected = d.pop("ImageHistoryLeftSelected", UNSET)
        image_history_left_selected: Union[Unset, ProfileInfoResponseImageHistorySettingsImageHistoryLeftSelected]
        if isinstance(_image_history_left_selected, Unset):
            image_history_left_selected = UNSET
        else:
            image_history_left_selected = ProfileInfoResponseImageHistorySettingsImageHistoryLeftSelected(
                _image_history_left_selected
            )

        _image_history_right_selected = d.pop("ImageHistoryRightSelected", UNSET)
        image_history_right_selected: Union[Unset, ProfileInfoResponseImageHistorySettingsImageHistoryRightSelected]
        if isinstance(_image_history_right_selected, Unset):
            image_history_right_selected = UNSET
        else:
            image_history_right_selected = ProfileInfoResponseImageHistorySettingsImageHistoryRightSelected(
                _image_history_right_selected
            )

        profile_info_response_image_history_settings = cls(
            image_history_left_selected=image_history_left_selected,
            image_history_right_selected=image_history_right_selected,
        )

        profile_info_response_image_history_settings.additional_properties = d
        return profile_info_response_image_history_settings

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

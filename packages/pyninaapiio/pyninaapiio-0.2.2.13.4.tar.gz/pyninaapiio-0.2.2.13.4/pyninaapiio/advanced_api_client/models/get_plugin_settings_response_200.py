from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetPluginSettingsResponse200")


@_attrs_define
class GetPluginSettingsResponse200:
    """
    Attributes:
        access_control_header_enabled (Union[Unset, bool]):  Example: True.
        should_create_thumbnails (Union[Unset, bool]):  Example: True.
    """

    access_control_header_enabled: Union[Unset, bool] = UNSET
    should_create_thumbnails: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        access_control_header_enabled = self.access_control_header_enabled

        should_create_thumbnails = self.should_create_thumbnails

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if access_control_header_enabled is not UNSET:
            field_dict["AccessControlHeaderEnabled"] = access_control_header_enabled
        if should_create_thumbnails is not UNSET:
            field_dict["ShouldCreateThumbnails"] = should_create_thumbnails

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        access_control_header_enabled = d.pop("AccessControlHeaderEnabled", UNSET)

        should_create_thumbnails = d.pop("ShouldCreateThumbnails", UNSET)

        get_plugin_settings_response_200 = cls(
            access_control_header_enabled=access_control_header_enabled,
            should_create_thumbnails=should_create_thumbnails,
        )

        get_plugin_settings_response_200.additional_properties = d
        return get_plugin_settings_response_200

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

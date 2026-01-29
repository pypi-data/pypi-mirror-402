from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseColorSchemaSettings")


@_attrs_define
class ProfileInfoResponseColorSchemaSettings:
    """
    Attributes:
        alt_color_schema (Union[Unset, str]):
        color_schema (Union[Unset, str]):
    """

    alt_color_schema: Union[Unset, str] = UNSET
    color_schema: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        alt_color_schema = self.alt_color_schema

        color_schema = self.color_schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if alt_color_schema is not UNSET:
            field_dict["AltColorSchema"] = alt_color_schema
        if color_schema is not UNSET:
            field_dict["ColorSchema"] = color_schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        alt_color_schema = d.pop("AltColorSchema", UNSET)

        color_schema = d.pop("ColorSchema", UNSET)

        profile_info_response_color_schema_settings = cls(
            alt_color_schema=alt_color_schema,
            color_schema=color_schema,
        )

        profile_info_response_color_schema_settings.additional_properties = d
        return profile_info_response_color_schema_settings

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

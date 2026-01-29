from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetLivestackImageAvailableResponse200ResponseItem")


@_attrs_define
class GetLivestackImageAvailableResponse200ResponseItem:
    """
    Attributes:
        filter_ (Union[Unset, str]):  Example: RGB.
        target (Union[Unset, str]):  Example: M31.
    """

    filter_: Union[Unset, str] = UNSET
    target: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        filter_ = self.filter_

        target = self.target

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if filter_ is not UNSET:
            field_dict["Filter"] = filter_
        if target is not UNSET:
            field_dict["Target"] = target

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        filter_ = d.pop("Filter", UNSET)

        target = d.pop("Target", UNSET)

        get_livestack_image_available_response_200_response_item = cls(
            filter_=filter_,
            target=target,
        )

        get_livestack_image_available_response_200_response_item.additional_properties = d
        return get_livestack_image_available_response_200_response_item

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

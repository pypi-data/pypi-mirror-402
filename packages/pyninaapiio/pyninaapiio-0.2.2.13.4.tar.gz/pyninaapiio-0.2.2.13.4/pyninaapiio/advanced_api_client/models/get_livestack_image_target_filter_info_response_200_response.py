from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetLivestackImageTargetFilterInfoResponse200Response")


@_attrs_define
class GetLivestackImageTargetFilterInfoResponse200Response:
    """
    Attributes:
        is_monochrome (Union[Unset, bool]):  Example: True.
        stack_count (Union[Unset, int]): Only present if IsMonochrome is true Example: 10.
        red_stack_count (Union[Unset, int]): Only present if IsMonochrome is false Example: 10.
        green_stack_count (Union[Unset, int]): Only present if IsMonochrome is false Example: 10.
        blue_stack_count (Union[Unset, int]): Only present if IsMonochrome is false Example: 10.
        filter_ (Union[Unset, str]):  Example: RGB.
        target (Union[Unset, str]):  Example: M31.
    """

    is_monochrome: Union[Unset, bool] = UNSET
    stack_count: Union[Unset, int] = UNSET
    red_stack_count: Union[Unset, int] = UNSET
    green_stack_count: Union[Unset, int] = UNSET
    blue_stack_count: Union[Unset, int] = UNSET
    filter_: Union[Unset, str] = UNSET
    target: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        is_monochrome = self.is_monochrome

        stack_count = self.stack_count

        red_stack_count = self.red_stack_count

        green_stack_count = self.green_stack_count

        blue_stack_count = self.blue_stack_count

        filter_ = self.filter_

        target = self.target

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_monochrome is not UNSET:
            field_dict["IsMonochrome"] = is_monochrome
        if stack_count is not UNSET:
            field_dict["StackCount"] = stack_count
        if red_stack_count is not UNSET:
            field_dict["RedStackCount"] = red_stack_count
        if green_stack_count is not UNSET:
            field_dict["GreenStackCount"] = green_stack_count
        if blue_stack_count is not UNSET:
            field_dict["BlueStackCount"] = blue_stack_count
        if filter_ is not UNSET:
            field_dict["Filter"] = filter_
        if target is not UNSET:
            field_dict["Target"] = target

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        is_monochrome = d.pop("IsMonochrome", UNSET)

        stack_count = d.pop("StackCount", UNSET)

        red_stack_count = d.pop("RedStackCount", UNSET)

        green_stack_count = d.pop("GreenStackCount", UNSET)

        blue_stack_count = d.pop("BlueStackCount", UNSET)

        filter_ = d.pop("Filter", UNSET)

        target = d.pop("Target", UNSET)

        get_livestack_image_target_filter_info_response_200_response = cls(
            is_monochrome=is_monochrome,
            stack_count=stack_count,
            red_stack_count=red_stack_count,
            green_stack_count=green_stack_count,
            blue_stack_count=blue_stack_count,
            filter_=filter_,
            target=target,
        )

        get_livestack_image_target_filter_info_response_200_response.additional_properties = d
        return get_livestack_image_target_filter_info_response_200_response

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

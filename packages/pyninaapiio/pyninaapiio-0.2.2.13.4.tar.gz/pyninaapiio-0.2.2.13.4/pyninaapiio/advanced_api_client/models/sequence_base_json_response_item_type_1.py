from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SequenceBaseJsonResponseItemType1")


@_attrs_define
class SequenceBaseJsonResponseItemType1:
    """
    Attributes:
        global_triggers (Union[Unset, List[Any]]):
    """

    global_triggers: Union[Unset, List[Any]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        global_triggers: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.global_triggers, Unset):
            global_triggers = self.global_triggers

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if global_triggers is not UNSET:
            field_dict["GlobalTriggers"] = global_triggers

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        global_triggers = cast(List[Any], d.pop("GlobalTriggers", UNSET))

        sequence_base_json_response_item_type_1 = cls(
            global_triggers=global_triggers,
        )

        sequence_base_json_response_item_type_1.additional_properties = d
        return sequence_base_json_response_item_type_1

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

from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetEventHistoryResponse200ResponseItem")


@_attrs_define
class GetEventHistoryResponse200ResponseItem:
    """
    Attributes:
        event (Union[Unset, str]):
        time (Union[Unset, str]):
    """

    event: Union[Unset, str] = UNSET
    time: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        event = self.event

        time = self.time

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if event is not UNSET:
            field_dict["Event"] = event
        if time is not UNSET:
            field_dict["Time"] = time

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        event = d.pop("Event", UNSET)

        time = d.pop("Time", UNSET)

        get_event_history_response_200_response_item = cls(
            event=event,
            time=time,
        )

        get_event_history_response_200_response_item.additional_properties = d
        return get_event_history_response_200_response_item

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

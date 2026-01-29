from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetApplicationLogsResponse200ResponseItem")


@_attrs_define
class GetApplicationLogsResponse200ResponseItem:
    """
    Attributes:
        timestamp (Union[Unset, str]):  Example: 2025-05-04T14:57:39.5079.
        level (Union[Unset, str]):  Example: INFO.
        source (Union[Unset, str]):  Example: CameraChooserVM.cs.
        member (Union[Unset, str]):  Example: GetEquipment.
        line (Union[Unset, str]):  Example: 279.
        message (Union[Unset, str]):  Example: Found 2 ASCOM Cameras.
    """

    timestamp: Union[Unset, str] = UNSET
    level: Union[Unset, str] = UNSET
    source: Union[Unset, str] = UNSET
    member: Union[Unset, str] = UNSET
    line: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        timestamp = self.timestamp

        level = self.level

        source = self.source

        member = self.member

        line = self.line

        message = self.message

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if timestamp is not UNSET:
            field_dict["Timestamp"] = timestamp
        if level is not UNSET:
            field_dict["Level"] = level
        if source is not UNSET:
            field_dict["Source"] = source
        if member is not UNSET:
            field_dict["Member"] = member
        if line is not UNSET:
            field_dict["Line"] = line
        if message is not UNSET:
            field_dict["Message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        timestamp = d.pop("Timestamp", UNSET)

        level = d.pop("Level", UNSET)

        source = d.pop("Source", UNSET)

        member = d.pop("Member", UNSET)

        line = d.pop("Line", UNSET)

        message = d.pop("Message", UNSET)

        get_application_logs_response_200_response_item = cls(
            timestamp=timestamp,
            level=level,
            source=source,
            member=member,
            line=line,
            message=message,
        )

        get_application_logs_response_200_response_item.additional_properties = d
        return get_application_logs_response_200_response_item

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

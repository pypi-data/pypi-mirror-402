from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SwitchInfoResponseWritableSwitchesItem")


@_attrs_define
class SwitchInfoResponseWritableSwitchesItem:
    """
    Attributes:
        maximum (int):
        minimum (int):
        step_size (float):
        target_value (int):
        id (int):
        name (str):
        description (str):
        value (int):
    """

    maximum: int
    minimum: int
    step_size: float
    target_value: int
    id: int
    name: str
    description: str
    value: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        maximum = self.maximum

        minimum = self.minimum

        step_size = self.step_size

        target_value = self.target_value

        id = self.id

        name = self.name

        description = self.description

        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Maximum": maximum,
                "Minimum": minimum,
                "StepSize": step_size,
                "TargetValue": target_value,
                "Id": id,
                "Name": name,
                "Description": description,
                "Value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        maximum = d.pop("Maximum")

        minimum = d.pop("Minimum")

        step_size = d.pop("StepSize")

        target_value = d.pop("TargetValue")

        id = d.pop("Id")

        name = d.pop("Name")

        description = d.pop("Description")

        value = d.pop("Value")

        switch_info_response_writable_switches_item = cls(
            maximum=maximum,
            minimum=minimum,
            step_size=step_size,
            target_value=target_value,
            id=id,
            name=name,
            description=description,
            value=value,
        )

        switch_info_response_writable_switches_item.additional_properties = d
        return switch_info_response_writable_switches_item

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

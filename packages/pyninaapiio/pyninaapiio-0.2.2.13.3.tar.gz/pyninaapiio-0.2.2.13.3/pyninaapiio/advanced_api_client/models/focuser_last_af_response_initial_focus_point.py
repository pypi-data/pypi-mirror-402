from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FocuserLastAFResponseInitialFocusPoint")


@_attrs_define
class FocuserLastAFResponseInitialFocusPoint:
    """
    Attributes:
        position (int):
        value (float):
        error (int):
    """

    position: int
    value: float
    error: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        position = self.position

        value = self.value

        error = self.error

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Position": position,
                "Value": value,
                "Error": error,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        position = d.pop("Position")

        value = d.pop("Value")

        error = d.pop("Error")

        focuser_last_af_response_initial_focus_point = cls(
            position=position,
            value=value,
            error=error,
        )

        focuser_last_af_response_initial_focus_point.additional_properties = d
        return focuser_last_af_response_initial_focus_point

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

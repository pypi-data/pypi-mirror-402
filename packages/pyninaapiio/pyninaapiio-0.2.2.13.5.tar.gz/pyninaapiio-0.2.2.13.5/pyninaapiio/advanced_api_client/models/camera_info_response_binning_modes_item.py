from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CameraInfoResponseBinningModesItem")


@_attrs_define
class CameraInfoResponseBinningModesItem:
    """
    Attributes:
        name (str):
        x (int):
        y (int):
    """

    name: str
    x: int
    y: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        x = self.x

        y = self.y

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Name": name,
                "X": x,
                "Y": y,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("Name")

        x = d.pop("X")

        y = d.pop("Y")

        camera_info_response_binning_modes_item = cls(
            name=name,
            x=x,
            y=y,
        )

        camera_info_response_binning_modes_item.additional_properties = d
        return camera_info_response_binning_modes_item

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

from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FramingAssistantInfoResponseRectangle")


@_attrs_define
class FramingAssistantInfoResponseRectangle:
    """
    Attributes:
        original_x (int):
        original_y (int):
        id (int):
        dso_position_angle (int):
        original_offset (int):
        rotation_offset (int):
        rotation (int):
        total_rotation (int):
        x (int):
        y (int):
        width (int):
        height (int):
    """

    original_x: int
    original_y: int
    id: int
    dso_position_angle: int
    original_offset: int
    rotation_offset: int
    rotation: int
    total_rotation: int
    x: int
    y: int
    width: int
    height: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        original_x = self.original_x

        original_y = self.original_y

        id = self.id

        dso_position_angle = self.dso_position_angle

        original_offset = self.original_offset

        rotation_offset = self.rotation_offset

        rotation = self.rotation

        total_rotation = self.total_rotation

        x = self.x

        y = self.y

        width = self.width

        height = self.height

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "OriginalX": original_x,
                "OriginalY": original_y,
                "Id": id,
                "DSOPositionAngle": dso_position_angle,
                "OriginalOffset": original_offset,
                "RotationOffset": rotation_offset,
                "Rotation": rotation,
                "TotalRotation": total_rotation,
                "X": x,
                "Y": y,
                "Width": width,
                "Height": height,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        original_x = d.pop("OriginalX")

        original_y = d.pop("OriginalY")

        id = d.pop("Id")

        dso_position_angle = d.pop("DSOPositionAngle")

        original_offset = d.pop("OriginalOffset")

        rotation_offset = d.pop("RotationOffset")

        rotation = d.pop("Rotation")

        total_rotation = d.pop("TotalRotation")

        x = d.pop("X")

        y = d.pop("Y")

        width = d.pop("Width")

        height = d.pop("Height")

        framing_assistant_info_response_rectangle = cls(
            original_x=original_x,
            original_y=original_y,
            id=id,
            dso_position_angle=dso_position_angle,
            original_offset=original_offset,
            rotation_offset=rotation_offset,
            rotation=rotation,
            total_rotation=total_rotation,
            x=x,
            y=y,
            width=width,
            height=height,
        )

        framing_assistant_info_response_rectangle.additional_properties = d
        return framing_assistant_info_response_rectangle

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

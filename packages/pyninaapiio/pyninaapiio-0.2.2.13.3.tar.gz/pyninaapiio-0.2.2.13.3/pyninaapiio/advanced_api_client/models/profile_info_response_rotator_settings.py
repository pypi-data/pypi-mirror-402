from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_rotator_settings_range_type import ProfileInfoResponseRotatorSettingsRangeType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseRotatorSettings")


@_attrs_define
class ProfileInfoResponseRotatorSettings:
    """
    Attributes:
        id (Union[Unset, str]):
        reverse_2 (Union[Unset, bool]):
        range_type (Union[Unset, ProfileInfoResponseRotatorSettingsRangeType]):
        range_start_mechanical_position (Union[Unset, int]):
    """

    id: Union[Unset, str] = UNSET
    reverse_2: Union[Unset, bool] = UNSET
    range_type: Union[Unset, ProfileInfoResponseRotatorSettingsRangeType] = UNSET
    range_start_mechanical_position: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        reverse_2 = self.reverse_2

        range_type: Union[Unset, str] = UNSET
        if not isinstance(self.range_type, Unset):
            range_type = self.range_type.value

        range_start_mechanical_position = self.range_start_mechanical_position

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["Id"] = id
        if reverse_2 is not UNSET:
            field_dict["Reverse2"] = reverse_2
        if range_type is not UNSET:
            field_dict["RangeType"] = range_type
        if range_start_mechanical_position is not UNSET:
            field_dict["RangeStartMechanicalPosition"] = range_start_mechanical_position

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("Id", UNSET)

        reverse_2 = d.pop("Reverse2", UNSET)

        _range_type = d.pop("RangeType", UNSET)
        range_type: Union[Unset, ProfileInfoResponseRotatorSettingsRangeType]
        if isinstance(_range_type, Unset):
            range_type = UNSET
        else:
            range_type = ProfileInfoResponseRotatorSettingsRangeType(_range_type)

        range_start_mechanical_position = d.pop("RangeStartMechanicalPosition", UNSET)

        profile_info_response_rotator_settings = cls(
            id=id,
            reverse_2=reverse_2,
            range_type=range_type,
            range_start_mechanical_position=range_start_mechanical_position,
        )

        profile_info_response_rotator_settings.additional_properties = d
        return profile_info_response_rotator_settings

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

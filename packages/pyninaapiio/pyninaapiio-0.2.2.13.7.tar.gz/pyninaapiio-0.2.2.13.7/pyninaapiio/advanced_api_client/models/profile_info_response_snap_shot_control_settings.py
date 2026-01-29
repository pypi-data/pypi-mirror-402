from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseSnapShotControlSettings")


@_attrs_define
class ProfileInfoResponseSnapShotControlSettings:
    """
    Attributes:
        exposure_duration (Union[Unset, int]):
        gain (Union[Unset, int]):
        save (Union[Unset, bool]):
        loop (Union[Unset, bool]):
    """

    exposure_duration: Union[Unset, int] = UNSET
    gain: Union[Unset, int] = UNSET
    save: Union[Unset, bool] = UNSET
    loop: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        exposure_duration = self.exposure_duration

        gain = self.gain

        save = self.save

        loop = self.loop

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if exposure_duration is not UNSET:
            field_dict["ExposureDuration"] = exposure_duration
        if gain is not UNSET:
            field_dict["Gain"] = gain
        if save is not UNSET:
            field_dict["Save"] = save
        if loop is not UNSET:
            field_dict["Loop"] = loop

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        exposure_duration = d.pop("ExposureDuration", UNSET)

        gain = d.pop("Gain", UNSET)

        save = d.pop("Save", UNSET)

        loop = d.pop("Loop", UNSET)

        profile_info_response_snap_shot_control_settings = cls(
            exposure_duration=exposure_duration,
            gain=gain,
            save=save,
            loop=loop,
        )

        profile_info_response_snap_shot_control_settings.additional_properties = d
        return profile_info_response_snap_shot_control_settings

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

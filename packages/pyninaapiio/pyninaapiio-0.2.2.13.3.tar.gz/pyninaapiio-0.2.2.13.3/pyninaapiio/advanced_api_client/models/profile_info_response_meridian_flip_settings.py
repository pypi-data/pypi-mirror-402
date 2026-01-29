from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseMeridianFlipSettings")


@_attrs_define
class ProfileInfoResponseMeridianFlipSettings:
    """
    Attributes:
        minutes_after_meridian (Union[Unset, int]):
        max_minutes_after_meridian (Union[Unset, int]):
        pause_time_before_meridian (Union[Unset, int]):
        recenter (Union[Unset, bool]):
        settle_time (Union[Unset, int]):
        use_side_of_pier (Union[Unset, bool]):
        auto_focus_after_flip (Union[Unset, bool]):
        rotate_image_after_flip (Union[Unset, bool]):
    """

    minutes_after_meridian: Union[Unset, int] = UNSET
    max_minutes_after_meridian: Union[Unset, int] = UNSET
    pause_time_before_meridian: Union[Unset, int] = UNSET
    recenter: Union[Unset, bool] = UNSET
    settle_time: Union[Unset, int] = UNSET
    use_side_of_pier: Union[Unset, bool] = UNSET
    auto_focus_after_flip: Union[Unset, bool] = UNSET
    rotate_image_after_flip: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        minutes_after_meridian = self.minutes_after_meridian

        max_minutes_after_meridian = self.max_minutes_after_meridian

        pause_time_before_meridian = self.pause_time_before_meridian

        recenter = self.recenter

        settle_time = self.settle_time

        use_side_of_pier = self.use_side_of_pier

        auto_focus_after_flip = self.auto_focus_after_flip

        rotate_image_after_flip = self.rotate_image_after_flip

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if minutes_after_meridian is not UNSET:
            field_dict["MinutesAfterMeridian"] = minutes_after_meridian
        if max_minutes_after_meridian is not UNSET:
            field_dict["MaxMinutesAfterMeridian"] = max_minutes_after_meridian
        if pause_time_before_meridian is not UNSET:
            field_dict["PauseTimeBeforeMeridian"] = pause_time_before_meridian
        if recenter is not UNSET:
            field_dict["Recenter"] = recenter
        if settle_time is not UNSET:
            field_dict["SettleTime"] = settle_time
        if use_side_of_pier is not UNSET:
            field_dict["UseSideOfPier"] = use_side_of_pier
        if auto_focus_after_flip is not UNSET:
            field_dict["AutoFocusAfterFlip"] = auto_focus_after_flip
        if rotate_image_after_flip is not UNSET:
            field_dict["RotateImageAfterFlip"] = rotate_image_after_flip

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        minutes_after_meridian = d.pop("MinutesAfterMeridian", UNSET)

        max_minutes_after_meridian = d.pop("MaxMinutesAfterMeridian", UNSET)

        pause_time_before_meridian = d.pop("PauseTimeBeforeMeridian", UNSET)

        recenter = d.pop("Recenter", UNSET)

        settle_time = d.pop("SettleTime", UNSET)

        use_side_of_pier = d.pop("UseSideOfPier", UNSET)

        auto_focus_after_flip = d.pop("AutoFocusAfterFlip", UNSET)

        rotate_image_after_flip = d.pop("RotateImageAfterFlip", UNSET)

        profile_info_response_meridian_flip_settings = cls(
            minutes_after_meridian=minutes_after_meridian,
            max_minutes_after_meridian=max_minutes_after_meridian,
            pause_time_before_meridian=pause_time_before_meridian,
            recenter=recenter,
            settle_time=settle_time,
            use_side_of_pier=use_side_of_pier,
            auto_focus_after_flip=auto_focus_after_flip,
            rotate_image_after_flip=rotate_image_after_flip,
        )

        profile_info_response_meridian_flip_settings.additional_properties = d
        return profile_info_response_meridian_flip_settings

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

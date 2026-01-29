from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GuideStepsHistoryResponseGuideStepsItem")


@_attrs_define
class GuideStepsHistoryResponseGuideStepsItem:
    """
    Attributes:
        id (Union[Unset, int]):
        id_offset_left (Union[Unset, float]):
        id_offset_right (Union[Unset, float]):
        ra_distance_raw (Union[Unset, float]):
        ra_distance_raw_display (Union[Unset, float]):
        ra_duration (Union[Unset, int]):
        dec_distance_raw (Union[Unset, float]):
        dec_distance_raw_display (Union[Unset, float]):
        dec_duration (Union[Unset, int]):
        dither (Union[Unset, str]):
    """

    id: Union[Unset, int] = UNSET
    id_offset_left: Union[Unset, float] = UNSET
    id_offset_right: Union[Unset, float] = UNSET
    ra_distance_raw: Union[Unset, float] = UNSET
    ra_distance_raw_display: Union[Unset, float] = UNSET
    ra_duration: Union[Unset, int] = UNSET
    dec_distance_raw: Union[Unset, float] = UNSET
    dec_distance_raw_display: Union[Unset, float] = UNSET
    dec_duration: Union[Unset, int] = UNSET
    dither: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        id_offset_left = self.id_offset_left

        id_offset_right = self.id_offset_right

        ra_distance_raw = self.ra_distance_raw

        ra_distance_raw_display = self.ra_distance_raw_display

        ra_duration = self.ra_duration

        dec_distance_raw = self.dec_distance_raw

        dec_distance_raw_display = self.dec_distance_raw_display

        dec_duration = self.dec_duration

        dither = self.dither

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["Id"] = id
        if id_offset_left is not UNSET:
            field_dict["IdOffsetLeft"] = id_offset_left
        if id_offset_right is not UNSET:
            field_dict["IdOffsetRight"] = id_offset_right
        if ra_distance_raw is not UNSET:
            field_dict["RADistanceRaw"] = ra_distance_raw
        if ra_distance_raw_display is not UNSET:
            field_dict["RADistanceRawDisplay"] = ra_distance_raw_display
        if ra_duration is not UNSET:
            field_dict["RADuration"] = ra_duration
        if dec_distance_raw is not UNSET:
            field_dict["DECDistanceRaw"] = dec_distance_raw
        if dec_distance_raw_display is not UNSET:
            field_dict["DECDistanceRawDisplay"] = dec_distance_raw_display
        if dec_duration is not UNSET:
            field_dict["DECDuration"] = dec_duration
        if dither is not UNSET:
            field_dict["Dither"] = dither

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("Id", UNSET)

        id_offset_left = d.pop("IdOffsetLeft", UNSET)

        id_offset_right = d.pop("IdOffsetRight", UNSET)

        ra_distance_raw = d.pop("RADistanceRaw", UNSET)

        ra_distance_raw_display = d.pop("RADistanceRawDisplay", UNSET)

        ra_duration = d.pop("RADuration", UNSET)

        dec_distance_raw = d.pop("DECDistanceRaw", UNSET)

        dec_distance_raw_display = d.pop("DECDistanceRawDisplay", UNSET)

        dec_duration = d.pop("DECDuration", UNSET)

        dither = d.pop("Dither", UNSET)

        guide_steps_history_response_guide_steps_item = cls(
            id=id,
            id_offset_left=id_offset_left,
            id_offset_right=id_offset_right,
            ra_distance_raw=ra_distance_raw,
            ra_distance_raw_display=ra_distance_raw_display,
            ra_duration=ra_duration,
            dec_distance_raw=dec_distance_raw,
            dec_distance_raw_display=dec_distance_raw_display,
            dec_duration=dec_duration,
            dither=dither,
        )

        guide_steps_history_response_guide_steps_item.additional_properties = d
        return guide_steps_history_response_guide_steps_item

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

from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GuiderInfoResponseLastGuideStep")


@_attrs_define
class GuiderInfoResponseLastGuideStep:
    """
    Attributes:
        ra_distance_raw (float):
        dec_distance_raw (float):
        ra_duration (float):
        dec_duration (float):
    """

    ra_distance_raw: float
    dec_distance_raw: float
    ra_duration: float
    dec_duration: float
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        ra_distance_raw = self.ra_distance_raw

        dec_distance_raw = self.dec_distance_raw

        ra_duration = self.ra_duration

        dec_duration = self.dec_duration

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "RADistanceRaw": ra_distance_raw,
                "DECDistanceRaw": dec_distance_raw,
                "RADuration": ra_duration,
                "DECDuration": dec_duration,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        ra_distance_raw = d.pop("RADistanceRaw")

        dec_distance_raw = d.pop("DECDistanceRaw")

        ra_duration = d.pop("RADuration")

        dec_duration = d.pop("DECDuration")

        guider_info_response_last_guide_step = cls(
            ra_distance_raw=ra_distance_raw,
            dec_distance_raw=dec_distance_raw,
            ra_duration=ra_duration,
            dec_duration=dec_duration,
        )

        guider_info_response_last_guide_step.additional_properties = d
        return guider_info_response_last_guide_step

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

from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_astro_util_moon_separation_response_200_response_moon_phase import (
    GetAstroUtilMoonSeparationResponse200ResponseMoonPhase,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetAstroUtilMoonSeparationResponse200Response")


@_attrs_define
class GetAstroUtilMoonSeparationResponse200Response:
    """
    Attributes:
        separation (Union[Unset, float]):
        moon_phase (Union[Unset, GetAstroUtilMoonSeparationResponse200ResponseMoonPhase]):
    """

    separation: Union[Unset, float] = UNSET
    moon_phase: Union[Unset, GetAstroUtilMoonSeparationResponse200ResponseMoonPhase] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        separation = self.separation

        moon_phase: Union[Unset, str] = UNSET
        if not isinstance(self.moon_phase, Unset):
            moon_phase = self.moon_phase.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if separation is not UNSET:
            field_dict["Separation"] = separation
        if moon_phase is not UNSET:
            field_dict["MoonPhase"] = moon_phase

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        separation = d.pop("Separation", UNSET)

        _moon_phase = d.pop("MoonPhase", UNSET)
        moon_phase: Union[Unset, GetAstroUtilMoonSeparationResponse200ResponseMoonPhase]
        if isinstance(_moon_phase, Unset):
            moon_phase = UNSET
        else:
            moon_phase = GetAstroUtilMoonSeparationResponse200ResponseMoonPhase(_moon_phase)

        get_astro_util_moon_separation_response_200_response = cls(
            separation=separation,
            moon_phase=moon_phase,
        )

        get_astro_util_moon_separation_response_200_response.additional_properties = d
        return get_astro_util_moon_separation_response_200_response

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

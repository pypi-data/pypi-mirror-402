from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetProfileHorizonResponse200Response")


@_attrs_define
class GetProfileHorizonResponse200Response:
    """
    Attributes:
        altitudes (Union[Unset, List[float]]):
        azimuths (Union[Unset, List[float]]):
    """

    altitudes: Union[Unset, List[float]] = UNSET
    azimuths: Union[Unset, List[float]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        altitudes: Union[Unset, List[float]] = UNSET
        if not isinstance(self.altitudes, Unset):
            altitudes = self.altitudes

        azimuths: Union[Unset, List[float]] = UNSET
        if not isinstance(self.azimuths, Unset):
            azimuths = self.azimuths

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if altitudes is not UNSET:
            field_dict["Altitudes"] = altitudes
        if azimuths is not UNSET:
            field_dict["Azimuths"] = azimuths

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        altitudes = cast(List[float], d.pop("Altitudes", UNSET))

        azimuths = cast(List[float], d.pop("Azimuths", UNSET))

        get_profile_horizon_response_200_response = cls(
            altitudes=altitudes,
            azimuths=azimuths,
        )

        get_profile_horizon_response_200_response.additional_properties = d
        return get_profile_horizon_response_200_response

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

from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseGuiderSettingsGuideChartDeclinationColor")


@_attrs_define
class ProfileInfoResponseGuiderSettingsGuideChartDeclinationColor:
    """
    Attributes:
        a (Union[Unset, int]):
        r (Union[Unset, int]):
        g (Union[Unset, int]):
        b (Union[Unset, int]):
        sc_a (Union[Unset, int]):
        sc_r (Union[Unset, int]):
        sc_g (Union[Unset, int]):
        sc_b (Union[Unset, int]):
    """

    a: Union[Unset, int] = UNSET
    r: Union[Unset, int] = UNSET
    g: Union[Unset, int] = UNSET
    b: Union[Unset, int] = UNSET
    sc_a: Union[Unset, int] = UNSET
    sc_r: Union[Unset, int] = UNSET
    sc_g: Union[Unset, int] = UNSET
    sc_b: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        a = self.a

        r = self.r

        g = self.g

        b = self.b

        sc_a = self.sc_a

        sc_r = self.sc_r

        sc_g = self.sc_g

        sc_b = self.sc_b

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if a is not UNSET:
            field_dict["A"] = a
        if r is not UNSET:
            field_dict["R"] = r
        if g is not UNSET:
            field_dict["G"] = g
        if b is not UNSET:
            field_dict["B"] = b
        if sc_a is not UNSET:
            field_dict["ScA"] = sc_a
        if sc_r is not UNSET:
            field_dict["ScR"] = sc_r
        if sc_g is not UNSET:
            field_dict["ScG"] = sc_g
        if sc_b is not UNSET:
            field_dict["ScB"] = sc_b

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        a = d.pop("A", UNSET)

        r = d.pop("R", UNSET)

        g = d.pop("G", UNSET)

        b = d.pop("B", UNSET)

        sc_a = d.pop("ScA", UNSET)

        sc_r = d.pop("ScR", UNSET)

        sc_g = d.pop("ScG", UNSET)

        sc_b = d.pop("ScB", UNSET)

        profile_info_response_guider_settings_guide_chart_declination_color = cls(
            a=a,
            r=r,
            g=g,
            b=b,
            sc_a=sc_a,
            sc_r=sc_r,
            sc_g=sc_g,
            sc_b=sc_b,
        )

        profile_info_response_guider_settings_guide_chart_declination_color.additional_properties = d
        return profile_info_response_guider_settings_guide_chart_declination_color

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

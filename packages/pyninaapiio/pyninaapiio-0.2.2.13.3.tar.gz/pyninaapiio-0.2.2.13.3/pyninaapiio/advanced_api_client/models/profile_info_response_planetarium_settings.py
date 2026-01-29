from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_planetarium_settings_preferred_planetarium import (
    ProfileInfoResponsePlanetariumSettingsPreferredPlanetarium,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponsePlanetariumSettings")


@_attrs_define
class ProfileInfoResponsePlanetariumSettings:
    """
    Attributes:
        stellarium_host (Union[Unset, str]):
        stellarium_port (Union[Unset, int]):
        cd_c_host (Union[Unset, str]):
        cd_c_port (Union[Unset, int]):
        tsx_host (Union[Unset, str]):
        tsx_port (Union[Unset, int]):
        tsx_use_selected_object (Union[Unset, bool]):
        hnsky_host (Union[Unset, str]):
        hnsky_port (Union[Unset, int]):
        c2a_host (Union[Unset, str]):
        c2a_port (Union[Unset, int]):
        skytech_x_host (Union[Unset, str]):
        skytech_x_port (Union[Unset, int]):
        preferred_planetarium (Union[Unset, ProfileInfoResponsePlanetariumSettingsPreferredPlanetarium]):
    """

    stellarium_host: Union[Unset, str] = UNSET
    stellarium_port: Union[Unset, int] = UNSET
    cd_c_host: Union[Unset, str] = UNSET
    cd_c_port: Union[Unset, int] = UNSET
    tsx_host: Union[Unset, str] = UNSET
    tsx_port: Union[Unset, int] = UNSET
    tsx_use_selected_object: Union[Unset, bool] = UNSET
    hnsky_host: Union[Unset, str] = UNSET
    hnsky_port: Union[Unset, int] = UNSET
    c2a_host: Union[Unset, str] = UNSET
    c2a_port: Union[Unset, int] = UNSET
    skytech_x_host: Union[Unset, str] = UNSET
    skytech_x_port: Union[Unset, int] = UNSET
    preferred_planetarium: Union[Unset, ProfileInfoResponsePlanetariumSettingsPreferredPlanetarium] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        stellarium_host = self.stellarium_host

        stellarium_port = self.stellarium_port

        cd_c_host = self.cd_c_host

        cd_c_port = self.cd_c_port

        tsx_host = self.tsx_host

        tsx_port = self.tsx_port

        tsx_use_selected_object = self.tsx_use_selected_object

        hnsky_host = self.hnsky_host

        hnsky_port = self.hnsky_port

        c2a_host = self.c2a_host

        c2a_port = self.c2a_port

        skytech_x_host = self.skytech_x_host

        skytech_x_port = self.skytech_x_port

        preferred_planetarium: Union[Unset, str] = UNSET
        if not isinstance(self.preferred_planetarium, Unset):
            preferred_planetarium = self.preferred_planetarium.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if stellarium_host is not UNSET:
            field_dict["StellariumHost"] = stellarium_host
        if stellarium_port is not UNSET:
            field_dict["StellariumPort"] = stellarium_port
        if cd_c_host is not UNSET:
            field_dict["CdCHost"] = cd_c_host
        if cd_c_port is not UNSET:
            field_dict["CdCPort"] = cd_c_port
        if tsx_host is not UNSET:
            field_dict["TSXHost"] = tsx_host
        if tsx_port is not UNSET:
            field_dict["TSXPort"] = tsx_port
        if tsx_use_selected_object is not UNSET:
            field_dict["TSXUseSelectedObject"] = tsx_use_selected_object
        if hnsky_host is not UNSET:
            field_dict["HNSKYHost"] = hnsky_host
        if hnsky_port is not UNSET:
            field_dict["HNSKYPort"] = hnsky_port
        if c2a_host is not UNSET:
            field_dict["C2AHost"] = c2a_host
        if c2a_port is not UNSET:
            field_dict["C2APort"] = c2a_port
        if skytech_x_host is not UNSET:
            field_dict["SkytechXHost"] = skytech_x_host
        if skytech_x_port is not UNSET:
            field_dict["SkytechXPort"] = skytech_x_port
        if preferred_planetarium is not UNSET:
            field_dict["PreferredPlanetarium"] = preferred_planetarium

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        stellarium_host = d.pop("StellariumHost", UNSET)

        stellarium_port = d.pop("StellariumPort", UNSET)

        cd_c_host = d.pop("CdCHost", UNSET)

        cd_c_port = d.pop("CdCPort", UNSET)

        tsx_host = d.pop("TSXHost", UNSET)

        tsx_port = d.pop("TSXPort", UNSET)

        tsx_use_selected_object = d.pop("TSXUseSelectedObject", UNSET)

        hnsky_host = d.pop("HNSKYHost", UNSET)

        hnsky_port = d.pop("HNSKYPort", UNSET)

        c2a_host = d.pop("C2AHost", UNSET)

        c2a_port = d.pop("C2APort", UNSET)

        skytech_x_host = d.pop("SkytechXHost", UNSET)

        skytech_x_port = d.pop("SkytechXPort", UNSET)

        _preferred_planetarium = d.pop("PreferredPlanetarium", UNSET)
        preferred_planetarium: Union[Unset, ProfileInfoResponsePlanetariumSettingsPreferredPlanetarium]
        if isinstance(_preferred_planetarium, Unset):
            preferred_planetarium = UNSET
        else:
            preferred_planetarium = ProfileInfoResponsePlanetariumSettingsPreferredPlanetarium(_preferred_planetarium)

        profile_info_response_planetarium_settings = cls(
            stellarium_host=stellarium_host,
            stellarium_port=stellarium_port,
            cd_c_host=cd_c_host,
            cd_c_port=cd_c_port,
            tsx_host=tsx_host,
            tsx_port=tsx_port,
            tsx_use_selected_object=tsx_use_selected_object,
            hnsky_host=hnsky_host,
            hnsky_port=hnsky_port,
            c2a_host=c2a_host,
            c2a_port=c2a_port,
            skytech_x_host=skytech_x_host,
            skytech_x_port=skytech_x_port,
            preferred_planetarium=preferred_planetarium,
        )

        profile_info_response_planetarium_settings.additional_properties = d
        return profile_info_response_planetarium_settings

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

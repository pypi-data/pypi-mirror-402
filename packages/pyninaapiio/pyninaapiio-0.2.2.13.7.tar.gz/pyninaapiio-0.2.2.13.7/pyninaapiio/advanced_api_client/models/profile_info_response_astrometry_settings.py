from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseAstrometrySettings")


@_attrs_define
class ProfileInfoResponseAstrometrySettings:
    """
    Attributes:
        latitude (Union[Unset, float]):
        longitude (Union[Unset, float]):
        elevation (Union[Unset, int]):
        horizon_file_path (Union[Unset, str]):
    """

    latitude: Union[Unset, float] = UNSET
    longitude: Union[Unset, float] = UNSET
    elevation: Union[Unset, int] = UNSET
    horizon_file_path: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        latitude = self.latitude

        longitude = self.longitude

        elevation = self.elevation

        horizon_file_path = self.horizon_file_path

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if latitude is not UNSET:
            field_dict["Latitude"] = latitude
        if longitude is not UNSET:
            field_dict["Longitude"] = longitude
        if elevation is not UNSET:
            field_dict["Elevation"] = elevation
        if horizon_file_path is not UNSET:
            field_dict["HorizonFilePath"] = horizon_file_path

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        latitude = d.pop("Latitude", UNSET)

        longitude = d.pop("Longitude", UNSET)

        elevation = d.pop("Elevation", UNSET)

        horizon_file_path = d.pop("HorizonFilePath", UNSET)

        profile_info_response_astrometry_settings = cls(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
            horizon_file_path=horizon_file_path,
        )

        profile_info_response_astrometry_settings.additional_properties = d
        return profile_info_response_astrometry_settings

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

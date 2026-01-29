from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseWeatherDataSettings")


@_attrs_define
class ProfileInfoResponseWeatherDataSettings:
    """
    Attributes:
        id (Union[Unset, str]):
        open_weather_map_api_key (Union[Unset, str]):
        the_weather_company_api_key (Union[Unset, str]):
        weather_underground_api_key (Union[Unset, str]):
        weather_underground_station (Union[Unset, str]):
    """

    id: Union[Unset, str] = UNSET
    open_weather_map_api_key: Union[Unset, str] = UNSET
    the_weather_company_api_key: Union[Unset, str] = UNSET
    weather_underground_api_key: Union[Unset, str] = UNSET
    weather_underground_station: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        open_weather_map_api_key = self.open_weather_map_api_key

        the_weather_company_api_key = self.the_weather_company_api_key

        weather_underground_api_key = self.weather_underground_api_key

        weather_underground_station = self.weather_underground_station

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["Id"] = id
        if open_weather_map_api_key is not UNSET:
            field_dict["OpenWeatherMapAPIKey"] = open_weather_map_api_key
        if the_weather_company_api_key is not UNSET:
            field_dict["TheWeatherCompanyAPIKey"] = the_weather_company_api_key
        if weather_underground_api_key is not UNSET:
            field_dict["WeatherUndergroundAPIKey"] = weather_underground_api_key
        if weather_underground_station is not UNSET:
            field_dict["WeatherUndergroundStation"] = weather_underground_station

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("Id", UNSET)

        open_weather_map_api_key = d.pop("OpenWeatherMapAPIKey", UNSET)

        the_weather_company_api_key = d.pop("TheWeatherCompanyAPIKey", UNSET)

        weather_underground_api_key = d.pop("WeatherUndergroundAPIKey", UNSET)

        weather_underground_station = d.pop("WeatherUndergroundStation", UNSET)

        profile_info_response_weather_data_settings = cls(
            id=id,
            open_weather_map_api_key=open_weather_map_api_key,
            the_weather_company_api_key=the_weather_company_api_key,
            weather_underground_api_key=weather_underground_api_key,
            weather_underground_station=weather_underground_station,
        )

        profile_info_response_weather_data_settings.additional_properties = d
        return profile_info_response_weather_data_settings

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

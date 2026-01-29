from typing import Any, Dict, List, Type, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="WeatherInfoResponse")


@_attrs_define
class WeatherInfoResponse:
    """
    Attributes:
        average_period (int):
        cloud_cover (int):
        dew_point (float):
        humidity (int):
        pressure (int):
        rain_rate (str):
        sky_brightness (str):
        sky_quality (str):
        sky_temperature (str):
        star_fwhm (str):
        temperature (float):
        wind_direction (int):
        wind_gust (str):
        wind_speed (float):
        supported_actions (List[Any]):
        connected (bool):
        name (str):
        display_name (str):
        description (str):
        driver_info (str):
        driver_version (str):
        device_id (str):
    """

    average_period: int
    cloud_cover: int
    dew_point: float
    humidity: int
    pressure: int
    rain_rate: str
    sky_brightness: str
    sky_quality: str
    sky_temperature: str
    star_fwhm: str
    temperature: float
    wind_direction: int
    wind_gust: str
    wind_speed: float
    supported_actions: List[Any]
    connected: bool
    name: str
    display_name: str
    description: str
    driver_info: str
    driver_version: str
    device_id: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        average_period = self.average_period

        cloud_cover = self.cloud_cover

        dew_point = self.dew_point

        humidity = self.humidity

        pressure = self.pressure

        rain_rate = self.rain_rate

        sky_brightness = self.sky_brightness

        sky_quality = self.sky_quality

        sky_temperature = self.sky_temperature

        star_fwhm = self.star_fwhm

        temperature = self.temperature

        wind_direction = self.wind_direction

        wind_gust = self.wind_gust

        wind_speed = self.wind_speed

        supported_actions = self.supported_actions

        connected = self.connected

        name = self.name

        display_name = self.display_name

        description = self.description

        driver_info = self.driver_info

        driver_version = self.driver_version

        device_id = self.device_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "AveragePeriod": average_period,
                "CloudCover": cloud_cover,
                "DewPoint": dew_point,
                "Humidity": humidity,
                "Pressure": pressure,
                "RainRate": rain_rate,
                "SkyBrightness": sky_brightness,
                "SkyQuality": sky_quality,
                "SkyTemperature": sky_temperature,
                "StarFWHM": star_fwhm,
                "Temperature": temperature,
                "WindDirection": wind_direction,
                "WindGust": wind_gust,
                "WindSpeed": wind_speed,
                "SupportedActions": supported_actions,
                "Connected": connected,
                "Name": name,
                "DisplayName": display_name,
                "Description": description,
                "DriverInfo": driver_info,
                "DriverVersion": driver_version,
                "DeviceId": device_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        average_period = d.pop("AveragePeriod")

        cloud_cover = d.pop("CloudCover")

        dew_point = d.pop("DewPoint")

        humidity = d.pop("Humidity")

        pressure = d.pop("Pressure")

        rain_rate = d.pop("RainRate")

        sky_brightness = d.pop("SkyBrightness")

        sky_quality = d.pop("SkyQuality")

        sky_temperature = d.pop("SkyTemperature")

        star_fwhm = d.pop("StarFWHM")

        temperature = d.pop("Temperature")

        wind_direction = d.pop("WindDirection")

        wind_gust = d.pop("WindGust")

        wind_speed = d.pop("WindSpeed")

        supported_actions = cast(List[Any], d.pop("SupportedActions"))

        connected = d.pop("Connected")

        name = d.pop("Name")

        display_name = d.pop("DisplayName")

        description = d.pop("Description")

        driver_info = d.pop("DriverInfo")

        driver_version = d.pop("DriverVersion")

        device_id = d.pop("DeviceId")

        weather_info_response = cls(
            average_period=average_period,
            cloud_cover=cloud_cover,
            dew_point=dew_point,
            humidity=humidity,
            pressure=pressure,
            rain_rate=rain_rate,
            sky_brightness=sky_brightness,
            sky_quality=sky_quality,
            sky_temperature=sky_temperature,
            star_fwhm=star_fwhm,
            temperature=temperature,
            wind_direction=wind_direction,
            wind_gust=wind_gust,
            wind_speed=wind_speed,
            supported_actions=supported_actions,
            connected=connected,
            name=name,
            display_name=display_name,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            device_id=device_id,
        )

        weather_info_response.additional_properties = d
        return weather_info_response

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

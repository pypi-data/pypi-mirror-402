from typing import Any, Dict, List, Type, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.flat_device_info_response_cover_state import FlatDeviceInfoResponseCoverState

T = TypeVar("T", bound="FlatDeviceInfoResponse")


@_attrs_define
class FlatDeviceInfoResponse:
    """
    Attributes:
        cover_state (FlatDeviceInfoResponseCoverState):
        localized_cover_state (str):
        localized_light_on_state (str):
        light_on (bool):
        brightness (int):
        supports_open_close (bool):
        min_brightness (int):
        max_brightness (int):
        supports_on_off (bool):
        supported_actions (List[Any]):
        connected (bool):
        name (str):
        display_name (str):
        description (str):
        driver_info (str):
        driver_version (str):
        device_id (str):
    """

    cover_state: FlatDeviceInfoResponseCoverState
    localized_cover_state: str
    localized_light_on_state: str
    light_on: bool
    brightness: int
    supports_open_close: bool
    min_brightness: int
    max_brightness: int
    supports_on_off: bool
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
        cover_state = self.cover_state.value

        localized_cover_state = self.localized_cover_state

        localized_light_on_state = self.localized_light_on_state

        light_on = self.light_on

        brightness = self.brightness

        supports_open_close = self.supports_open_close

        min_brightness = self.min_brightness

        max_brightness = self.max_brightness

        supports_on_off = self.supports_on_off

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
                "CoverState": cover_state,
                "LocalizedCoverState": localized_cover_state,
                "LocalizedLightOnState": localized_light_on_state,
                "LightOn": light_on,
                "Brightness": brightness,
                "SupportsOpenClose": supports_open_close,
                "MinBrightness": min_brightness,
                "MaxBrightness": max_brightness,
                "SupportsOnOff": supports_on_off,
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
        cover_state = FlatDeviceInfoResponseCoverState(d.pop("CoverState"))

        localized_cover_state = d.pop("LocalizedCoverState")

        localized_light_on_state = d.pop("LocalizedLightOnState")

        light_on = d.pop("LightOn")

        brightness = d.pop("Brightness")

        supports_open_close = d.pop("SupportsOpenClose")

        min_brightness = d.pop("MinBrightness")

        max_brightness = d.pop("MaxBrightness")

        supports_on_off = d.pop("SupportsOnOff")

        supported_actions = cast(List[Any], d.pop("SupportedActions"))

        connected = d.pop("Connected")

        name = d.pop("Name")

        display_name = d.pop("DisplayName")

        description = d.pop("Description")

        driver_info = d.pop("DriverInfo")

        driver_version = d.pop("DriverVersion")

        device_id = d.pop("DeviceId")

        flat_device_info_response = cls(
            cover_state=cover_state,
            localized_cover_state=localized_cover_state,
            localized_light_on_state=localized_light_on_state,
            light_on=light_on,
            brightness=brightness,
            supports_open_close=supports_open_close,
            min_brightness=min_brightness,
            max_brightness=max_brightness,
            supports_on_off=supports_on_off,
            supported_actions=supported_actions,
            connected=connected,
            name=name,
            display_name=display_name,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            device_id=device_id,
        )

        flat_device_info_response.additional_properties = d
        return flat_device_info_response

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

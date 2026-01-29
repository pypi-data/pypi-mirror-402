from typing import Any, Dict, List, Type, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FocuserInfoResponse")


@_attrs_define
class FocuserInfoResponse:
    """
    Attributes:
        position (int):
        step_size (int):
        temperature (float):
        is_moving (bool):
        is_settling (bool):
        temp_comp (bool):
        temp_comp_available (bool):
        supported_actions (List[Any]):
        connected (bool):
        name (str):
        display_name (str):
        description (str):
        driver_info (str):
        driver_version (str):
        device_id (str):
    """

    position: int
    step_size: int
    temperature: float
    is_moving: bool
    is_settling: bool
    temp_comp: bool
    temp_comp_available: bool
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
        position = self.position

        step_size = self.step_size

        temperature = self.temperature

        is_moving = self.is_moving

        is_settling = self.is_settling

        temp_comp = self.temp_comp

        temp_comp_available = self.temp_comp_available

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
                "Position": position,
                "StepSize": step_size,
                "Temperature": temperature,
                "IsMoving": is_moving,
                "IsSettling": is_settling,
                "TempComp": temp_comp,
                "TempCompAvailable": temp_comp_available,
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
        position = d.pop("Position")

        step_size = d.pop("StepSize")

        temperature = d.pop("Temperature")

        is_moving = d.pop("IsMoving")

        is_settling = d.pop("IsSettling")

        temp_comp = d.pop("TempComp")

        temp_comp_available = d.pop("TempCompAvailable")

        supported_actions = cast(List[Any], d.pop("SupportedActions"))

        connected = d.pop("Connected")

        name = d.pop("Name")

        display_name = d.pop("DisplayName")

        description = d.pop("Description")

        driver_info = d.pop("DriverInfo")

        driver_version = d.pop("DriverVersion")

        device_id = d.pop("DeviceId")

        focuser_info_response = cls(
            position=position,
            step_size=step_size,
            temperature=temperature,
            is_moving=is_moving,
            is_settling=is_settling,
            temp_comp=temp_comp,
            temp_comp_available=temp_comp_available,
            supported_actions=supported_actions,
            connected=connected,
            name=name,
            display_name=display_name,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            device_id=device_id,
        )

        focuser_info_response.additional_properties = d
        return focuser_info_response

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

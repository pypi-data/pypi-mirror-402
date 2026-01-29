from typing import Any, Dict, List, Type, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RotatorInfoResponse")


@_attrs_define
class RotatorInfoResponse:
    """
    Attributes:
        can_reverse (bool):
        reverse (bool):
        mechanical_position (int):
        position (int):
        step_size (float):
        is_moving (bool):
        synced (bool):
        supported_actions (List[Any]):
        connected (bool):
        name (str):
        display_name (str):
        description (str):
        driver_info (str):
        driver_version (str):
        device_id (str):
    """

    can_reverse: bool
    reverse: bool
    mechanical_position: int
    position: int
    step_size: float
    is_moving: bool
    synced: bool
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
        can_reverse = self.can_reverse

        reverse = self.reverse

        mechanical_position = self.mechanical_position

        position = self.position

        step_size = self.step_size

        is_moving = self.is_moving

        synced = self.synced

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
                "CanReverse": can_reverse,
                "Reverse": reverse,
                "MechanicalPosition": mechanical_position,
                "Position": position,
                "StepSize": step_size,
                "IsMoving": is_moving,
                "Synced": synced,
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
        can_reverse = d.pop("CanReverse")

        reverse = d.pop("Reverse")

        mechanical_position = d.pop("MechanicalPosition")

        position = d.pop("Position")

        step_size = d.pop("StepSize")

        is_moving = d.pop("IsMoving")

        synced = d.pop("Synced")

        supported_actions = cast(List[Any], d.pop("SupportedActions"))

        connected = d.pop("Connected")

        name = d.pop("Name")

        display_name = d.pop("DisplayName")

        description = d.pop("Description")

        driver_info = d.pop("DriverInfo")

        driver_version = d.pop("DriverVersion")

        device_id = d.pop("DeviceId")

        rotator_info_response = cls(
            can_reverse=can_reverse,
            reverse=reverse,
            mechanical_position=mechanical_position,
            position=position,
            step_size=step_size,
            is_moving=is_moving,
            synced=synced,
            supported_actions=supported_actions,
            connected=connected,
            name=name,
            display_name=display_name,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            device_id=device_id,
        )

        rotator_info_response.additional_properties = d
        return rotator_info_response

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

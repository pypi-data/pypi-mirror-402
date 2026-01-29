from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.switch_info_response_readonly_switches_item import SwitchInfoResponseReadonlySwitchesItem
    from ..models.switch_info_response_writable_switches_item import SwitchInfoResponseWritableSwitchesItem


T = TypeVar("T", bound="SwitchInfoResponse")


@_attrs_define
class SwitchInfoResponse:
    """
    Attributes:
        writable_switches (List['SwitchInfoResponseWritableSwitchesItem']):
        readonly_switches (List['SwitchInfoResponseReadonlySwitchesItem']):
        supported_actions (List[str]):
        connected (bool):
        name (str):
        display_name (str):
        description (str):
        driver_info (str):
        driver_version (str):
        device_id (str):
    """

    writable_switches: List["SwitchInfoResponseWritableSwitchesItem"]
    readonly_switches: List["SwitchInfoResponseReadonlySwitchesItem"]
    supported_actions: List[str]
    connected: bool
    name: str
    display_name: str
    description: str
    driver_info: str
    driver_version: str
    device_id: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        writable_switches = []
        for writable_switches_item_data in self.writable_switches:
            writable_switches_item = writable_switches_item_data.to_dict()
            writable_switches.append(writable_switches_item)

        readonly_switches = []
        for readonly_switches_item_data in self.readonly_switches:
            readonly_switches_item = readonly_switches_item_data.to_dict()
            readonly_switches.append(readonly_switches_item)

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
                "WritableSwitches": writable_switches,
                "ReadonlySwitches": readonly_switches,
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
        from ..models.switch_info_response_readonly_switches_item import SwitchInfoResponseReadonlySwitchesItem
        from ..models.switch_info_response_writable_switches_item import SwitchInfoResponseWritableSwitchesItem

        d = src_dict.copy()
        writable_switches = []
        _writable_switches = d.pop("WritableSwitches")
        for writable_switches_item_data in _writable_switches:
            writable_switches_item = SwitchInfoResponseWritableSwitchesItem.from_dict(writable_switches_item_data)

            writable_switches.append(writable_switches_item)

        readonly_switches = []
        _readonly_switches = d.pop("ReadonlySwitches")
        for readonly_switches_item_data in _readonly_switches:
            readonly_switches_item = SwitchInfoResponseReadonlySwitchesItem.from_dict(readonly_switches_item_data)

            readonly_switches.append(readonly_switches_item)

        supported_actions = cast(List[str], d.pop("SupportedActions"))

        connected = d.pop("Connected")

        name = d.pop("Name")

        display_name = d.pop("DisplayName")

        description = d.pop("Description")

        driver_info = d.pop("DriverInfo")

        driver_version = d.pop("DriverVersion")

        device_id = d.pop("DeviceId")

        switch_info_response = cls(
            writable_switches=writable_switches,
            readonly_switches=readonly_switches,
            supported_actions=supported_actions,
            connected=connected,
            name=name,
            display_name=display_name,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            device_id=device_id,
        )

        switch_info_response.additional_properties = d
        return switch_info_response

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

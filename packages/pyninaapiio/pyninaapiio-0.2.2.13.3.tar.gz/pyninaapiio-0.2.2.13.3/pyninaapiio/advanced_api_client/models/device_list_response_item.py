from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceListResponseItem")


@_attrs_define
class DeviceListResponseItem:
    """
    Attributes:
        has_setup_dialog (Union[Unset, bool]):
        id (Union[Unset, str]):
        name (Union[Unset, str]):
        display_name (Union[Unset, str]):
        category (Union[Unset, str]):
        connected (Union[Unset, bool]):
        description (Union[Unset, str]):
        driver_info (Union[Unset, str]):
        driver_version (Union[Unset, str]):
        supported_actions (Union[Unset, List[Any]]):
    """

    has_setup_dialog: Union[Unset, bool] = UNSET
    id: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    display_name: Union[Unset, str] = UNSET
    category: Union[Unset, str] = UNSET
    connected: Union[Unset, bool] = UNSET
    description: Union[Unset, str] = UNSET
    driver_info: Union[Unset, str] = UNSET
    driver_version: Union[Unset, str] = UNSET
    supported_actions: Union[Unset, List[Any]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        has_setup_dialog = self.has_setup_dialog

        id = self.id

        name = self.name

        display_name = self.display_name

        category = self.category

        connected = self.connected

        description = self.description

        driver_info = self.driver_info

        driver_version = self.driver_version

        supported_actions: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.supported_actions, Unset):
            supported_actions = self.supported_actions

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if has_setup_dialog is not UNSET:
            field_dict["HasSetupDialog"] = has_setup_dialog
        if id is not UNSET:
            field_dict["Id"] = id
        if name is not UNSET:
            field_dict["Name"] = name
        if display_name is not UNSET:
            field_dict["DisplayName"] = display_name
        if category is not UNSET:
            field_dict["Category"] = category
        if connected is not UNSET:
            field_dict["Connected"] = connected
        if description is not UNSET:
            field_dict["Description"] = description
        if driver_info is not UNSET:
            field_dict["DriverInfo"] = driver_info
        if driver_version is not UNSET:
            field_dict["DriverVersion"] = driver_version
        if supported_actions is not UNSET:
            field_dict["SupportedActions"] = supported_actions

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        has_setup_dialog = d.pop("HasSetupDialog", UNSET)

        id = d.pop("Id", UNSET)

        name = d.pop("Name", UNSET)

        display_name = d.pop("DisplayName", UNSET)

        category = d.pop("Category", UNSET)

        connected = d.pop("Connected", UNSET)

        description = d.pop("Description", UNSET)

        driver_info = d.pop("DriverInfo", UNSET)

        driver_version = d.pop("DriverVersion", UNSET)

        supported_actions = cast(List[Any], d.pop("SupportedActions", UNSET))

        device_list_response_item = cls(
            has_setup_dialog=has_setup_dialog,
            id=id,
            name=name,
            display_name=display_name,
            category=category,
            connected=connected,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            supported_actions=supported_actions,
        )

        device_list_response_item.additional_properties = d
        return device_list_response_item

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

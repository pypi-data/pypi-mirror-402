from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fw_info_response_available_filters_item import FWInfoResponseAvailableFiltersItem
    from ..models.fw_info_response_selected_filter import FWInfoResponseSelectedFilter


T = TypeVar("T", bound="FWInfoResponse")


@_attrs_define
class FWInfoResponse:
    """
    Attributes:
        connected (bool):
        name (str):
        display_name (str):
        description (str):
        driver_info (str):
        driver_version (str):
        device_id (str):
        is_moving (Union[Unset, bool]):
        supported_actions (Union[Unset, List[str]]):
        selected_filter (Union[Unset, FWInfoResponseSelectedFilter]):
        available_filters (Union[Unset, List['FWInfoResponseAvailableFiltersItem']]):
    """

    connected: bool
    name: str
    display_name: str
    description: str
    driver_info: str
    driver_version: str
    device_id: str
    is_moving: Union[Unset, bool] = UNSET
    supported_actions: Union[Unset, List[str]] = UNSET
    selected_filter: Union[Unset, "FWInfoResponseSelectedFilter"] = UNSET
    available_filters: Union[Unset, List["FWInfoResponseAvailableFiltersItem"]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        connected = self.connected

        name = self.name

        display_name = self.display_name

        description = self.description

        driver_info = self.driver_info

        driver_version = self.driver_version

        device_id = self.device_id

        is_moving = self.is_moving

        supported_actions: Union[Unset, List[str]] = UNSET
        if not isinstance(self.supported_actions, Unset):
            supported_actions = self.supported_actions

        selected_filter: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.selected_filter, Unset):
            selected_filter = self.selected_filter.to_dict()

        available_filters: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.available_filters, Unset):
            available_filters = []
            for available_filters_item_data in self.available_filters:
                available_filters_item = available_filters_item_data.to_dict()
                available_filters.append(available_filters_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Connected": connected,
                "Name": name,
                "DisplayName": display_name,
                "Description": description,
                "DriverInfo": driver_info,
                "DriverVersion": driver_version,
                "DeviceId": device_id,
            }
        )
        if is_moving is not UNSET:
            field_dict["IsMoving"] = is_moving
        if supported_actions is not UNSET:
            field_dict["SupportedActions"] = supported_actions
        if selected_filter is not UNSET:
            field_dict["SelectedFilter"] = selected_filter
        if available_filters is not UNSET:
            field_dict["AvailableFilters"] = available_filters

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.fw_info_response_available_filters_item import FWInfoResponseAvailableFiltersItem
        from ..models.fw_info_response_selected_filter import FWInfoResponseSelectedFilter

        d = src_dict.copy()
        connected = d.pop("Connected")

        name = d.pop("Name")

        display_name = d.pop("DisplayName")

        description = d.pop("Description")

        driver_info = d.pop("DriverInfo")

        driver_version = d.pop("DriverVersion")

        device_id = d.pop("DeviceId")

        is_moving = d.pop("IsMoving", UNSET)

        supported_actions = cast(List[str], d.pop("SupportedActions", UNSET))

        _selected_filter = d.pop("SelectedFilter", UNSET)
        selected_filter: Union[Unset, FWInfoResponseSelectedFilter]
        if isinstance(_selected_filter, Unset):
            selected_filter = UNSET
        else:
            selected_filter = FWInfoResponseSelectedFilter.from_dict(_selected_filter)

        available_filters = []
        _available_filters = d.pop("AvailableFilters", UNSET)
        for available_filters_item_data in _available_filters or []:
            available_filters_item = FWInfoResponseAvailableFiltersItem.from_dict(available_filters_item_data)

            available_filters.append(available_filters_item)

        fw_info_response = cls(
            connected=connected,
            name=name,
            display_name=display_name,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            device_id=device_id,
            is_moving=is_moving,
            supported_actions=supported_actions,
            selected_filter=selected_filter,
            available_filters=available_filters,
        )

        fw_info_response.additional_properties = d
        return fw_info_response

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

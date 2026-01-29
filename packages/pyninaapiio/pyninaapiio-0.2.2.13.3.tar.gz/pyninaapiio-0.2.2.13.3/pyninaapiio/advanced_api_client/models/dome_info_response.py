from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.dome_info_response_shutter_status import DomeInfoResponseShutterStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="DomeInfoResponse")


@_attrs_define
class DomeInfoResponse:
    """
    Attributes:
        shutter_status (Union[Unset, DomeInfoResponseShutterStatus]):
        driver_can_follow (Union[Unset, bool]):
        can_set_shutter (Union[Unset, bool]):
        can_set_park (Union[Unset, bool]):
        can_set_azimuth (Union[Unset, bool]):
        can_sync_azimuth (Union[Unset, bool]):
        can_park (Union[Unset, bool]):
        can_find_home (Union[Unset, bool]):
        at_park (Union[Unset, bool]):
        at_home (Union[Unset, bool]):
        driver_following (Union[Unset, bool]):
        slewing (Union[Unset, bool]):
        azimuth (Union[Unset, int]):
        supported_actions (Union[Unset, List[Any]]):
        connected (Union[Unset, bool]):
        name (Union[Unset, str]):
        display_name (Union[Unset, str]):
        description (Union[Unset, str]):
        driver_info (Union[Unset, str]):
        driver_version (Union[Unset, str]):
        device_id (Union[Unset, str]):
        is_following (Union[Unset, bool]):
        is_synchronized (Union[Unset, bool]):
    """

    shutter_status: Union[Unset, DomeInfoResponseShutterStatus] = UNSET
    driver_can_follow: Union[Unset, bool] = UNSET
    can_set_shutter: Union[Unset, bool] = UNSET
    can_set_park: Union[Unset, bool] = UNSET
    can_set_azimuth: Union[Unset, bool] = UNSET
    can_sync_azimuth: Union[Unset, bool] = UNSET
    can_park: Union[Unset, bool] = UNSET
    can_find_home: Union[Unset, bool] = UNSET
    at_park: Union[Unset, bool] = UNSET
    at_home: Union[Unset, bool] = UNSET
    driver_following: Union[Unset, bool] = UNSET
    slewing: Union[Unset, bool] = UNSET
    azimuth: Union[Unset, int] = UNSET
    supported_actions: Union[Unset, List[Any]] = UNSET
    connected: Union[Unset, bool] = UNSET
    name: Union[Unset, str] = UNSET
    display_name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    driver_info: Union[Unset, str] = UNSET
    driver_version: Union[Unset, str] = UNSET
    device_id: Union[Unset, str] = UNSET
    is_following: Union[Unset, bool] = UNSET
    is_synchronized: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        shutter_status: Union[Unset, str] = UNSET
        if not isinstance(self.shutter_status, Unset):
            shutter_status = self.shutter_status.value

        driver_can_follow = self.driver_can_follow

        can_set_shutter = self.can_set_shutter

        can_set_park = self.can_set_park

        can_set_azimuth = self.can_set_azimuth

        can_sync_azimuth = self.can_sync_azimuth

        can_park = self.can_park

        can_find_home = self.can_find_home

        at_park = self.at_park

        at_home = self.at_home

        driver_following = self.driver_following

        slewing = self.slewing

        azimuth = self.azimuth

        supported_actions: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.supported_actions, Unset):
            supported_actions = self.supported_actions

        connected = self.connected

        name = self.name

        display_name = self.display_name

        description = self.description

        driver_info = self.driver_info

        driver_version = self.driver_version

        device_id = self.device_id

        is_following = self.is_following

        is_synchronized = self.is_synchronized

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if shutter_status is not UNSET:
            field_dict["ShutterStatus"] = shutter_status
        if driver_can_follow is not UNSET:
            field_dict["DriverCanFollow"] = driver_can_follow
        if can_set_shutter is not UNSET:
            field_dict["CanSetShutter"] = can_set_shutter
        if can_set_park is not UNSET:
            field_dict["CanSetPark"] = can_set_park
        if can_set_azimuth is not UNSET:
            field_dict["CanSetAzimuth"] = can_set_azimuth
        if can_sync_azimuth is not UNSET:
            field_dict["CanSyncAzimuth"] = can_sync_azimuth
        if can_park is not UNSET:
            field_dict["CanPark"] = can_park
        if can_find_home is not UNSET:
            field_dict["CanFindHome"] = can_find_home
        if at_park is not UNSET:
            field_dict["AtPark"] = at_park
        if at_home is not UNSET:
            field_dict["AtHome"] = at_home
        if driver_following is not UNSET:
            field_dict["DriverFollowing"] = driver_following
        if slewing is not UNSET:
            field_dict["Slewing"] = slewing
        if azimuth is not UNSET:
            field_dict["Azimuth"] = azimuth
        if supported_actions is not UNSET:
            field_dict["SupportedActions"] = supported_actions
        if connected is not UNSET:
            field_dict["Connected"] = connected
        if name is not UNSET:
            field_dict["Name"] = name
        if display_name is not UNSET:
            field_dict["DisplayName"] = display_name
        if description is not UNSET:
            field_dict["Description"] = description
        if driver_info is not UNSET:
            field_dict["DriverInfo"] = driver_info
        if driver_version is not UNSET:
            field_dict["DriverVersion"] = driver_version
        if device_id is not UNSET:
            field_dict["DeviceId"] = device_id
        if is_following is not UNSET:
            field_dict["IsFollowing"] = is_following
        if is_synchronized is not UNSET:
            field_dict["IsSynchronized"] = is_synchronized

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        _shutter_status = d.pop("ShutterStatus", UNSET)
        shutter_status: Union[Unset, DomeInfoResponseShutterStatus]
        if isinstance(_shutter_status, Unset):
            shutter_status = UNSET
        else:
            shutter_status = DomeInfoResponseShutterStatus(_shutter_status)

        driver_can_follow = d.pop("DriverCanFollow", UNSET)

        can_set_shutter = d.pop("CanSetShutter", UNSET)

        can_set_park = d.pop("CanSetPark", UNSET)

        can_set_azimuth = d.pop("CanSetAzimuth", UNSET)

        can_sync_azimuth = d.pop("CanSyncAzimuth", UNSET)

        can_park = d.pop("CanPark", UNSET)

        can_find_home = d.pop("CanFindHome", UNSET)

        at_park = d.pop("AtPark", UNSET)

        at_home = d.pop("AtHome", UNSET)

        driver_following = d.pop("DriverFollowing", UNSET)

        slewing = d.pop("Slewing", UNSET)

        azimuth = d.pop("Azimuth", UNSET)

        supported_actions = cast(List[Any], d.pop("SupportedActions", UNSET))

        connected = d.pop("Connected", UNSET)

        name = d.pop("Name", UNSET)

        display_name = d.pop("DisplayName", UNSET)

        description = d.pop("Description", UNSET)

        driver_info = d.pop("DriverInfo", UNSET)

        driver_version = d.pop("DriverVersion", UNSET)

        device_id = d.pop("DeviceId", UNSET)

        is_following = d.pop("IsFollowing", UNSET)

        is_synchronized = d.pop("IsSynchronized", UNSET)

        dome_info_response = cls(
            shutter_status=shutter_status,
            driver_can_follow=driver_can_follow,
            can_set_shutter=can_set_shutter,
            can_set_park=can_set_park,
            can_set_azimuth=can_set_azimuth,
            can_sync_azimuth=can_sync_azimuth,
            can_park=can_park,
            can_find_home=can_find_home,
            at_park=at_park,
            at_home=at_home,
            driver_following=driver_following,
            slewing=slewing,
            azimuth=azimuth,
            supported_actions=supported_actions,
            connected=connected,
            name=name,
            display_name=display_name,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            device_id=device_id,
            is_following=is_following,
            is_synchronized=is_synchronized,
        )

        dome_info_response.additional_properties = d
        return dome_info_response

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

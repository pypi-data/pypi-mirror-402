from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_telescope_settings_telescope_location_sync_direction import (
    ProfileInfoResponseTelescopeSettingsTelescopeLocationSyncDirection,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseTelescopeSettings")


@_attrs_define
class ProfileInfoResponseTelescopeSettings:
    """
    Attributes:
        name (Union[Unset, str]):
        mount_name (Union[Unset, str]):
        focal_length (Union[Unset, int]):
        focal_ratio (Union[Unset, int]):
        id (Union[Unset, str]):
        settle_time (Union[Unset, int]):
        snap_port_start (Union[Unset, str]):
        snap_port_stop (Union[Unset, str]):
        no_sync (Union[Unset, bool]):
        time_sync (Union[Unset, bool]):
        primary_reversed (Union[Unset, bool]):
        secondary_reversed (Union[Unset, bool]):
        telescope_location_sync_direction (Union[Unset,
            ProfileInfoResponseTelescopeSettingsTelescopeLocationSyncDirection]):
    """

    name: Union[Unset, str] = UNSET
    mount_name: Union[Unset, str] = UNSET
    focal_length: Union[Unset, int] = UNSET
    focal_ratio: Union[Unset, int] = UNSET
    id: Union[Unset, str] = UNSET
    settle_time: Union[Unset, int] = UNSET
    snap_port_start: Union[Unset, str] = UNSET
    snap_port_stop: Union[Unset, str] = UNSET
    no_sync: Union[Unset, bool] = UNSET
    time_sync: Union[Unset, bool] = UNSET
    primary_reversed: Union[Unset, bool] = UNSET
    secondary_reversed: Union[Unset, bool] = UNSET
    telescope_location_sync_direction: Union[
        Unset, ProfileInfoResponseTelescopeSettingsTelescopeLocationSyncDirection
    ] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        mount_name = self.mount_name

        focal_length = self.focal_length

        focal_ratio = self.focal_ratio

        id = self.id

        settle_time = self.settle_time

        snap_port_start = self.snap_port_start

        snap_port_stop = self.snap_port_stop

        no_sync = self.no_sync

        time_sync = self.time_sync

        primary_reversed = self.primary_reversed

        secondary_reversed = self.secondary_reversed

        telescope_location_sync_direction: Union[Unset, str] = UNSET
        if not isinstance(self.telescope_location_sync_direction, Unset):
            telescope_location_sync_direction = self.telescope_location_sync_direction.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["Name"] = name
        if mount_name is not UNSET:
            field_dict["MountName"] = mount_name
        if focal_length is not UNSET:
            field_dict["FocalLength"] = focal_length
        if focal_ratio is not UNSET:
            field_dict["FocalRatio"] = focal_ratio
        if id is not UNSET:
            field_dict["Id"] = id
        if settle_time is not UNSET:
            field_dict["SettleTime"] = settle_time
        if snap_port_start is not UNSET:
            field_dict["SnapPortStart"] = snap_port_start
        if snap_port_stop is not UNSET:
            field_dict["SnapPortStop"] = snap_port_stop
        if no_sync is not UNSET:
            field_dict["NoSync"] = no_sync
        if time_sync is not UNSET:
            field_dict["TimeSync"] = time_sync
        if primary_reversed is not UNSET:
            field_dict["PrimaryReversed"] = primary_reversed
        if secondary_reversed is not UNSET:
            field_dict["SecondaryReversed"] = secondary_reversed
        if telescope_location_sync_direction is not UNSET:
            field_dict["TelescopeLocationSyncDirection"] = telescope_location_sync_direction

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("Name", UNSET)

        mount_name = d.pop("MountName", UNSET)

        focal_length = d.pop("FocalLength", UNSET)

        focal_ratio = d.pop("FocalRatio", UNSET)

        id = d.pop("Id", UNSET)

        settle_time = d.pop("SettleTime", UNSET)

        snap_port_start = d.pop("SnapPortStart", UNSET)

        snap_port_stop = d.pop("SnapPortStop", UNSET)

        no_sync = d.pop("NoSync", UNSET)

        time_sync = d.pop("TimeSync", UNSET)

        primary_reversed = d.pop("PrimaryReversed", UNSET)

        secondary_reversed = d.pop("SecondaryReversed", UNSET)

        _telescope_location_sync_direction = d.pop("TelescopeLocationSyncDirection", UNSET)
        telescope_location_sync_direction: Union[
            Unset, ProfileInfoResponseTelescopeSettingsTelescopeLocationSyncDirection
        ]
        if isinstance(_telescope_location_sync_direction, Unset):
            telescope_location_sync_direction = UNSET
        else:
            telescope_location_sync_direction = ProfileInfoResponseTelescopeSettingsTelescopeLocationSyncDirection(
                _telescope_location_sync_direction
            )

        profile_info_response_telescope_settings = cls(
            name=name,
            mount_name=mount_name,
            focal_length=focal_length,
            focal_ratio=focal_ratio,
            id=id,
            settle_time=settle_time,
            snap_port_start=snap_port_start,
            snap_port_stop=snap_port_stop,
            no_sync=no_sync,
            time_sync=time_sync,
            primary_reversed=primary_reversed,
            secondary_reversed=secondary_reversed,
            telescope_location_sync_direction=telescope_location_sync_direction,
        )

        profile_info_response_telescope_settings.additional_properties = d
        return profile_info_response_telescope_settings

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

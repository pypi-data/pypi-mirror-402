from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_dome_settings_mount_type import ProfileInfoResponseDomeSettingsMountType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseDomeSettings")


@_attrs_define
class ProfileInfoResponseDomeSettings:
    """
    Attributes:
        id (Union[Unset, str]):
        scope_position_east_west_mm (Union[Unset, int]):
        scope_position_north_south_mm (Union[Unset, int]):
        scope_position_up_down_mm (Union[Unset, int]):
        dome_radius_mm (Union[Unset, int]):
        gem_axis_mm (Union[Unset, int]):
        lateral_axis_mm (Union[Unset, int]):
        azimuth_tolerance_degrees (Union[Unset, int]):
        find_home_before_park (Union[Unset, bool]):
        dome_sync_timeout_seconds (Union[Unset, int]):
        synchronize_during_mount_slew (Union[Unset, bool]):
        sync_slew_dome_when_mount_slews (Union[Unset, bool]):
        rotate_degrees (Union[Unset, int]):
        close_on_unsafe (Union[Unset, bool]):
        park_mount_before_shutter_move (Union[Unset, bool]):
        refuse_unsafe_shutter_move (Union[Unset, bool]):
        refuse_unsafe_shutter_open_sans_safety_device (Union[Unset, bool]):
        park_dome_before_shutter_move (Union[Unset, bool]):
        mount_type (Union[Unset, ProfileInfoResponseDomeSettingsMountType]):
        dec_offset_horizontal_mm (Union[Unset, int]):
        settle_time_seconds (Union[Unset, int]):
    """

    id: Union[Unset, str] = UNSET
    scope_position_east_west_mm: Union[Unset, int] = UNSET
    scope_position_north_south_mm: Union[Unset, int] = UNSET
    scope_position_up_down_mm: Union[Unset, int] = UNSET
    dome_radius_mm: Union[Unset, int] = UNSET
    gem_axis_mm: Union[Unset, int] = UNSET
    lateral_axis_mm: Union[Unset, int] = UNSET
    azimuth_tolerance_degrees: Union[Unset, int] = UNSET
    find_home_before_park: Union[Unset, bool] = UNSET
    dome_sync_timeout_seconds: Union[Unset, int] = UNSET
    synchronize_during_mount_slew: Union[Unset, bool] = UNSET
    sync_slew_dome_when_mount_slews: Union[Unset, bool] = UNSET
    rotate_degrees: Union[Unset, int] = UNSET
    close_on_unsafe: Union[Unset, bool] = UNSET
    park_mount_before_shutter_move: Union[Unset, bool] = UNSET
    refuse_unsafe_shutter_move: Union[Unset, bool] = UNSET
    refuse_unsafe_shutter_open_sans_safety_device: Union[Unset, bool] = UNSET
    park_dome_before_shutter_move: Union[Unset, bool] = UNSET
    mount_type: Union[Unset, ProfileInfoResponseDomeSettingsMountType] = UNSET
    dec_offset_horizontal_mm: Union[Unset, int] = UNSET
    settle_time_seconds: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        scope_position_east_west_mm = self.scope_position_east_west_mm

        scope_position_north_south_mm = self.scope_position_north_south_mm

        scope_position_up_down_mm = self.scope_position_up_down_mm

        dome_radius_mm = self.dome_radius_mm

        gem_axis_mm = self.gem_axis_mm

        lateral_axis_mm = self.lateral_axis_mm

        azimuth_tolerance_degrees = self.azimuth_tolerance_degrees

        find_home_before_park = self.find_home_before_park

        dome_sync_timeout_seconds = self.dome_sync_timeout_seconds

        synchronize_during_mount_slew = self.synchronize_during_mount_slew

        sync_slew_dome_when_mount_slews = self.sync_slew_dome_when_mount_slews

        rotate_degrees = self.rotate_degrees

        close_on_unsafe = self.close_on_unsafe

        park_mount_before_shutter_move = self.park_mount_before_shutter_move

        refuse_unsafe_shutter_move = self.refuse_unsafe_shutter_move

        refuse_unsafe_shutter_open_sans_safety_device = self.refuse_unsafe_shutter_open_sans_safety_device

        park_dome_before_shutter_move = self.park_dome_before_shutter_move

        mount_type: Union[Unset, str] = UNSET
        if not isinstance(self.mount_type, Unset):
            mount_type = self.mount_type.value

        dec_offset_horizontal_mm = self.dec_offset_horizontal_mm

        settle_time_seconds = self.settle_time_seconds

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["Id"] = id
        if scope_position_east_west_mm is not UNSET:
            field_dict["ScopePositionEastWest_mm"] = scope_position_east_west_mm
        if scope_position_north_south_mm is not UNSET:
            field_dict["ScopePositionNorthSouth_mm"] = scope_position_north_south_mm
        if scope_position_up_down_mm is not UNSET:
            field_dict["ScopePositionUpDown_mm"] = scope_position_up_down_mm
        if dome_radius_mm is not UNSET:
            field_dict["DomeRadius_mm"] = dome_radius_mm
        if gem_axis_mm is not UNSET:
            field_dict["GemAxis_mm"] = gem_axis_mm
        if lateral_axis_mm is not UNSET:
            field_dict["LateralAxis_mm"] = lateral_axis_mm
        if azimuth_tolerance_degrees is not UNSET:
            field_dict["AzimuthTolerance_degrees"] = azimuth_tolerance_degrees
        if find_home_before_park is not UNSET:
            field_dict["FindHomeBeforePark"] = find_home_before_park
        if dome_sync_timeout_seconds is not UNSET:
            field_dict["DomeSyncTimeoutSeconds"] = dome_sync_timeout_seconds
        if synchronize_during_mount_slew is not UNSET:
            field_dict["SynchronizeDuringMountSlew"] = synchronize_during_mount_slew
        if sync_slew_dome_when_mount_slews is not UNSET:
            field_dict["SyncSlewDomeWhenMountSlews"] = sync_slew_dome_when_mount_slews
        if rotate_degrees is not UNSET:
            field_dict["RotateDegrees"] = rotate_degrees
        if close_on_unsafe is not UNSET:
            field_dict["CloseOnUnsafe"] = close_on_unsafe
        if park_mount_before_shutter_move is not UNSET:
            field_dict["ParkMountBeforeShutterMove"] = park_mount_before_shutter_move
        if refuse_unsafe_shutter_move is not UNSET:
            field_dict["RefuseUnsafeShutterMove"] = refuse_unsafe_shutter_move
        if refuse_unsafe_shutter_open_sans_safety_device is not UNSET:
            field_dict["RefuseUnsafeShutterOpenSansSafetyDevice"] = refuse_unsafe_shutter_open_sans_safety_device
        if park_dome_before_shutter_move is not UNSET:
            field_dict["ParkDomeBeforeShutterMove"] = park_dome_before_shutter_move
        if mount_type is not UNSET:
            field_dict["MountType"] = mount_type
        if dec_offset_horizontal_mm is not UNSET:
            field_dict["DecOffsetHorizontal_mm"] = dec_offset_horizontal_mm
        if settle_time_seconds is not UNSET:
            field_dict["SettleTimeSeconds"] = settle_time_seconds

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("Id", UNSET)

        scope_position_east_west_mm = d.pop("ScopePositionEastWest_mm", UNSET)

        scope_position_north_south_mm = d.pop("ScopePositionNorthSouth_mm", UNSET)

        scope_position_up_down_mm = d.pop("ScopePositionUpDown_mm", UNSET)

        dome_radius_mm = d.pop("DomeRadius_mm", UNSET)

        gem_axis_mm = d.pop("GemAxis_mm", UNSET)

        lateral_axis_mm = d.pop("LateralAxis_mm", UNSET)

        azimuth_tolerance_degrees = d.pop("AzimuthTolerance_degrees", UNSET)

        find_home_before_park = d.pop("FindHomeBeforePark", UNSET)

        dome_sync_timeout_seconds = d.pop("DomeSyncTimeoutSeconds", UNSET)

        synchronize_during_mount_slew = d.pop("SynchronizeDuringMountSlew", UNSET)

        sync_slew_dome_when_mount_slews = d.pop("SyncSlewDomeWhenMountSlews", UNSET)

        rotate_degrees = d.pop("RotateDegrees", UNSET)

        close_on_unsafe = d.pop("CloseOnUnsafe", UNSET)

        park_mount_before_shutter_move = d.pop("ParkMountBeforeShutterMove", UNSET)

        refuse_unsafe_shutter_move = d.pop("RefuseUnsafeShutterMove", UNSET)

        refuse_unsafe_shutter_open_sans_safety_device = d.pop("RefuseUnsafeShutterOpenSansSafetyDevice", UNSET)

        park_dome_before_shutter_move = d.pop("ParkDomeBeforeShutterMove", UNSET)

        _mount_type = d.pop("MountType", UNSET)
        mount_type: Union[Unset, ProfileInfoResponseDomeSettingsMountType]
        if isinstance(_mount_type, Unset):
            mount_type = UNSET
        else:
            mount_type = ProfileInfoResponseDomeSettingsMountType(_mount_type)

        dec_offset_horizontal_mm = d.pop("DecOffsetHorizontal_mm", UNSET)

        settle_time_seconds = d.pop("SettleTimeSeconds", UNSET)

        profile_info_response_dome_settings = cls(
            id=id,
            scope_position_east_west_mm=scope_position_east_west_mm,
            scope_position_north_south_mm=scope_position_north_south_mm,
            scope_position_up_down_mm=scope_position_up_down_mm,
            dome_radius_mm=dome_radius_mm,
            gem_axis_mm=gem_axis_mm,
            lateral_axis_mm=lateral_axis_mm,
            azimuth_tolerance_degrees=azimuth_tolerance_degrees,
            find_home_before_park=find_home_before_park,
            dome_sync_timeout_seconds=dome_sync_timeout_seconds,
            synchronize_during_mount_slew=synchronize_during_mount_slew,
            sync_slew_dome_when_mount_slews=sync_slew_dome_when_mount_slews,
            rotate_degrees=rotate_degrees,
            close_on_unsafe=close_on_unsafe,
            park_mount_before_shutter_move=park_mount_before_shutter_move,
            refuse_unsafe_shutter_move=refuse_unsafe_shutter_move,
            refuse_unsafe_shutter_open_sans_safety_device=refuse_unsafe_shutter_open_sans_safety_device,
            park_dome_before_shutter_move=park_dome_before_shutter_move,
            mount_type=mount_type,
            dec_offset_horizontal_mm=dec_offset_horizontal_mm,
            settle_time_seconds=settle_time_seconds,
        )

        profile_info_response_dome_settings.additional_properties = d
        return profile_info_response_dome_settings

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

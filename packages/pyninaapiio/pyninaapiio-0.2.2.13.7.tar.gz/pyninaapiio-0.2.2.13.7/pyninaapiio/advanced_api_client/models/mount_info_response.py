from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.mount_info_response_alignment_mode import MountInfoResponseAlignmentMode
from ..models.mount_info_response_equatorial_system import MountInfoResponseEquatorialSystem
from ..models.mount_info_response_side_of_pier import MountInfoResponseSideOfPier
from ..models.mount_info_response_tracking_mode import MountInfoResponseTrackingMode
from ..models.mount_info_response_tracking_modes_item import MountInfoResponseTrackingModesItem
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mount_info_response_coordinates import MountInfoResponseCoordinates
    from ..models.mount_info_response_primary_axis_rates_item import MountInfoResponsePrimaryAxisRatesItem
    from ..models.mount_info_response_secondary_axis_rates_item import MountInfoResponseSecondaryAxisRatesItem
    from ..models.mount_info_response_tracking_rate import MountInfoResponseTrackingRate


T = TypeVar("T", bound="MountInfoResponse")


@_attrs_define
class MountInfoResponse:
    """
    Attributes:
        connected (bool):
        name (str):
        display_name (str):
        device_id (str):
        tracking_mode (Union[Unset, MountInfoResponseTrackingMode]):
        sidereal_time (Union[Unset, float]):
        right_ascension (Union[Unset, float]):
        declination (Union[Unset, float]):
        site_latitude (Union[Unset, float]):
        site_longitude (Union[Unset, float]):
        site_elevation (Union[Unset, float]):
        right_ascension_string (Union[Unset, str]):
        declination_string (Union[Unset, str]):
        coordinates (Union[Unset, MountInfoResponseCoordinates]):
        time_to_meridian_flip (Union[Unset, float]):
        side_of_pier (Union[Unset, MountInfoResponseSideOfPier]):
        altitude (Union[Unset, float]):
        altitude_string (Union[Unset, str]):
        azimuth (Union[Unset, float]):
        azimuth_string (Union[Unset, str]):
        sidereal_time_string (Union[Unset, str]):
        hours_to_meridian_string (Union[Unset, str]):
        at_park (Union[Unset, bool]):
        tracking_rate (Union[Unset, MountInfoResponseTrackingRate]):
        tracking_enabled (Union[Unset, bool]):
        tracking_modes (Union[Unset, List[MountInfoResponseTrackingModesItem]]):
        at_home (Union[Unset, bool]):
        can_find_home (Union[Unset, bool]):
        can_park (Union[Unset, bool]):
        can_set_park (Union[Unset, bool]):
        can_set_tracking_enabled (Union[Unset, bool]):
        can_set_declination_rate (Union[Unset, bool]):
        can_set_right_ascension_rate (Union[Unset, bool]):
        equatorial_system (Union[Unset, MountInfoResponseEquatorialSystem]):
        has_unknown_epoch (Union[Unset, bool]):
        time_to_meridian_flip_string (Union[Unset, str]):
        slewing (Union[Unset, bool]):
        guide_rate_right_ascension_arcsec_per_sec (Union[Unset, float]):
        guide_rate_declination_arcsec_per_sec (Union[Unset, float]):
        can_move_primary_axis (Union[Unset, bool]):
        can_move_secondary_axis (Union[Unset, bool]):
        primary_axis_rates (Union[Unset, List['MountInfoResponsePrimaryAxisRatesItem']]):
        secondary_axis_rates (Union[Unset, List['MountInfoResponseSecondaryAxisRatesItem']]):
        supported_actions (Union[Unset, List[str]]):
        alignment_mode (Union[Unset, MountInfoResponseAlignmentMode]):
        can_pulse_guide (Union[Unset, bool]):
        is_pulse_guiding (Union[Unset, bool]):
        can_set_pier_side (Union[Unset, bool]):
        can_slew (Union[Unset, bool]):
        utc_date (Union[Unset, str]):
    """

    connected: bool
    name: str
    display_name: str
    device_id: str
    tracking_mode: Union[Unset, MountInfoResponseTrackingMode] = UNSET
    sidereal_time: Union[Unset, float] = UNSET
    right_ascension: Union[Unset, float] = UNSET
    declination: Union[Unset, float] = UNSET
    site_latitude: Union[Unset, float] = UNSET
    site_longitude: Union[Unset, float] = UNSET
    site_elevation: Union[Unset, float] = UNSET
    right_ascension_string: Union[Unset, str] = UNSET
    declination_string: Union[Unset, str] = UNSET
    coordinates: Union[Unset, "MountInfoResponseCoordinates"] = UNSET
    time_to_meridian_flip: Union[Unset, float] = UNSET
    side_of_pier: Union[Unset, MountInfoResponseSideOfPier] = UNSET
    altitude: Union[Unset, float] = UNSET
    altitude_string: Union[Unset, str] = UNSET
    azimuth: Union[Unset, float] = UNSET
    azimuth_string: Union[Unset, str] = UNSET
    sidereal_time_string: Union[Unset, str] = UNSET
    hours_to_meridian_string: Union[Unset, str] = UNSET
    at_park: Union[Unset, bool] = UNSET
    tracking_rate: Union[Unset, "MountInfoResponseTrackingRate"] = UNSET
    tracking_enabled: Union[Unset, bool] = UNSET
    tracking_modes: Union[Unset, List[MountInfoResponseTrackingModesItem]] = UNSET
    at_home: Union[Unset, bool] = UNSET
    can_find_home: Union[Unset, bool] = UNSET
    can_park: Union[Unset, bool] = UNSET
    can_set_park: Union[Unset, bool] = UNSET
    can_set_tracking_enabled: Union[Unset, bool] = UNSET
    can_set_declination_rate: Union[Unset, bool] = UNSET
    can_set_right_ascension_rate: Union[Unset, bool] = UNSET
    equatorial_system: Union[Unset, MountInfoResponseEquatorialSystem] = UNSET
    has_unknown_epoch: Union[Unset, bool] = UNSET
    time_to_meridian_flip_string: Union[Unset, str] = UNSET
    slewing: Union[Unset, bool] = UNSET
    guide_rate_right_ascension_arcsec_per_sec: Union[Unset, float] = UNSET
    guide_rate_declination_arcsec_per_sec: Union[Unset, float] = UNSET
    can_move_primary_axis: Union[Unset, bool] = UNSET
    can_move_secondary_axis: Union[Unset, bool] = UNSET
    primary_axis_rates: Union[Unset, List["MountInfoResponsePrimaryAxisRatesItem"]] = UNSET
    secondary_axis_rates: Union[Unset, List["MountInfoResponseSecondaryAxisRatesItem"]] = UNSET
    supported_actions: Union[Unset, List[str]] = UNSET
    alignment_mode: Union[Unset, MountInfoResponseAlignmentMode] = UNSET
    can_pulse_guide: Union[Unset, bool] = UNSET
    is_pulse_guiding: Union[Unset, bool] = UNSET
    can_set_pier_side: Union[Unset, bool] = UNSET
    can_slew: Union[Unset, bool] = UNSET
    utc_date: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        connected = self.connected

        name = self.name

        display_name = self.display_name

        device_id = self.device_id

        tracking_mode: Union[Unset, str] = UNSET
        if not isinstance(self.tracking_mode, Unset):
            tracking_mode = self.tracking_mode.value

        sidereal_time = self.sidereal_time

        right_ascension = self.right_ascension

        declination = self.declination

        site_latitude = self.site_latitude

        site_longitude = self.site_longitude

        site_elevation = self.site_elevation

        right_ascension_string = self.right_ascension_string

        declination_string = self.declination_string

        coordinates: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.coordinates, Unset):
            coordinates = self.coordinates.to_dict()

        time_to_meridian_flip = self.time_to_meridian_flip

        side_of_pier: Union[Unset, str] = UNSET
        if not isinstance(self.side_of_pier, Unset):
            side_of_pier = self.side_of_pier.value

        altitude = self.altitude

        altitude_string = self.altitude_string

        azimuth = self.azimuth

        azimuth_string = self.azimuth_string

        sidereal_time_string = self.sidereal_time_string

        hours_to_meridian_string = self.hours_to_meridian_string

        at_park = self.at_park

        tracking_rate: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tracking_rate, Unset):
            tracking_rate = self.tracking_rate.to_dict()

        tracking_enabled = self.tracking_enabled

        tracking_modes: Union[Unset, List[str]] = UNSET
        if not isinstance(self.tracking_modes, Unset):
            tracking_modes = []
            for tracking_modes_item_data in self.tracking_modes:
                tracking_modes_item = tracking_modes_item_data.value
                tracking_modes.append(tracking_modes_item)

        at_home = self.at_home

        can_find_home = self.can_find_home

        can_park = self.can_park

        can_set_park = self.can_set_park

        can_set_tracking_enabled = self.can_set_tracking_enabled

        can_set_declination_rate = self.can_set_declination_rate

        can_set_right_ascension_rate = self.can_set_right_ascension_rate

        equatorial_system: Union[Unset, str] = UNSET
        if not isinstance(self.equatorial_system, Unset):
            equatorial_system = self.equatorial_system.value

        has_unknown_epoch = self.has_unknown_epoch

        time_to_meridian_flip_string = self.time_to_meridian_flip_string

        slewing = self.slewing

        guide_rate_right_ascension_arcsec_per_sec = self.guide_rate_right_ascension_arcsec_per_sec

        guide_rate_declination_arcsec_per_sec = self.guide_rate_declination_arcsec_per_sec

        can_move_primary_axis = self.can_move_primary_axis

        can_move_secondary_axis = self.can_move_secondary_axis

        primary_axis_rates: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.primary_axis_rates, Unset):
            primary_axis_rates = []
            for primary_axis_rates_item_data in self.primary_axis_rates:
                primary_axis_rates_item = primary_axis_rates_item_data.to_dict()
                primary_axis_rates.append(primary_axis_rates_item)

        secondary_axis_rates: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.secondary_axis_rates, Unset):
            secondary_axis_rates = []
            for secondary_axis_rates_item_data in self.secondary_axis_rates:
                secondary_axis_rates_item = secondary_axis_rates_item_data.to_dict()
                secondary_axis_rates.append(secondary_axis_rates_item)

        supported_actions: Union[Unset, List[str]] = UNSET
        if not isinstance(self.supported_actions, Unset):
            supported_actions = self.supported_actions

        alignment_mode: Union[Unset, str] = UNSET
        if not isinstance(self.alignment_mode, Unset):
            alignment_mode = self.alignment_mode.value

        can_pulse_guide = self.can_pulse_guide

        is_pulse_guiding = self.is_pulse_guiding

        can_set_pier_side = self.can_set_pier_side

        can_slew = self.can_slew

        utc_date = self.utc_date

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Connected": connected,
                "Name": name,
                "DisplayName": display_name,
                "DeviceId": device_id,
            }
        )
        if tracking_mode is not UNSET:
            field_dict["TrackingMode"] = tracking_mode
        if sidereal_time is not UNSET:
            field_dict["SiderealTime"] = sidereal_time
        if right_ascension is not UNSET:
            field_dict["RightAscension"] = right_ascension
        if declination is not UNSET:
            field_dict["Declination"] = declination
        if site_latitude is not UNSET:
            field_dict["SiteLatitude"] = site_latitude
        if site_longitude is not UNSET:
            field_dict["SiteLongitude"] = site_longitude
        if site_elevation is not UNSET:
            field_dict["SiteElevation"] = site_elevation
        if right_ascension_string is not UNSET:
            field_dict["RightAscensionString"] = right_ascension_string
        if declination_string is not UNSET:
            field_dict["DeclinationString"] = declination_string
        if coordinates is not UNSET:
            field_dict["Coordinates"] = coordinates
        if time_to_meridian_flip is not UNSET:
            field_dict["TimeToMeridianFlip"] = time_to_meridian_flip
        if side_of_pier is not UNSET:
            field_dict["SideOfPier"] = side_of_pier
        if altitude is not UNSET:
            field_dict["Altitude"] = altitude
        if altitude_string is not UNSET:
            field_dict["AltitudeString"] = altitude_string
        if azimuth is not UNSET:
            field_dict["Azimuth"] = azimuth
        if azimuth_string is not UNSET:
            field_dict["AzimuthString"] = azimuth_string
        if sidereal_time_string is not UNSET:
            field_dict["SiderealTimeString"] = sidereal_time_string
        if hours_to_meridian_string is not UNSET:
            field_dict["HoursToMeridianString"] = hours_to_meridian_string
        if at_park is not UNSET:
            field_dict["AtPark"] = at_park
        if tracking_rate is not UNSET:
            field_dict["TrackingRate"] = tracking_rate
        if tracking_enabled is not UNSET:
            field_dict["TrackingEnabled"] = tracking_enabled
        if tracking_modes is not UNSET:
            field_dict["TrackingModes"] = tracking_modes
        if at_home is not UNSET:
            field_dict["AtHome"] = at_home
        if can_find_home is not UNSET:
            field_dict["CanFindHome"] = can_find_home
        if can_park is not UNSET:
            field_dict["CanPark"] = can_park
        if can_set_park is not UNSET:
            field_dict["CanSetPark"] = can_set_park
        if can_set_tracking_enabled is not UNSET:
            field_dict["CanSetTrackingEnabled"] = can_set_tracking_enabled
        if can_set_declination_rate is not UNSET:
            field_dict["CanSetDeclinationRate"] = can_set_declination_rate
        if can_set_right_ascension_rate is not UNSET:
            field_dict["CanSetRightAscensionRate"] = can_set_right_ascension_rate
        if equatorial_system is not UNSET:
            field_dict["EquatorialSystem"] = equatorial_system
        if has_unknown_epoch is not UNSET:
            field_dict["HasUnknownEpoch"] = has_unknown_epoch
        if time_to_meridian_flip_string is not UNSET:
            field_dict["TimeToMeridianFlipString"] = time_to_meridian_flip_string
        if slewing is not UNSET:
            field_dict["Slewing"] = slewing
        if guide_rate_right_ascension_arcsec_per_sec is not UNSET:
            field_dict["GuideRateRightAscensionArcsecPerSec"] = guide_rate_right_ascension_arcsec_per_sec
        if guide_rate_declination_arcsec_per_sec is not UNSET:
            field_dict["GuideRateDeclinationArcsecPerSec"] = guide_rate_declination_arcsec_per_sec
        if can_move_primary_axis is not UNSET:
            field_dict["CanMovePrimaryAxis"] = can_move_primary_axis
        if can_move_secondary_axis is not UNSET:
            field_dict["CanMoveSecondaryAxis"] = can_move_secondary_axis
        if primary_axis_rates is not UNSET:
            field_dict["PrimaryAxisRates"] = primary_axis_rates
        if secondary_axis_rates is not UNSET:
            field_dict["SecondaryAxisRates"] = secondary_axis_rates
        if supported_actions is not UNSET:
            field_dict["SupportedActions"] = supported_actions
        if alignment_mode is not UNSET:
            field_dict["AlignmentMode"] = alignment_mode
        if can_pulse_guide is not UNSET:
            field_dict["CanPulseGuide"] = can_pulse_guide
        if is_pulse_guiding is not UNSET:
            field_dict["IsPulseGuiding"] = is_pulse_guiding
        if can_set_pier_side is not UNSET:
            field_dict["CanSetPierSide"] = can_set_pier_side
        if can_slew is not UNSET:
            field_dict["CanSlew"] = can_slew
        if utc_date is not UNSET:
            field_dict["UTCDate"] = utc_date

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.mount_info_response_coordinates import MountInfoResponseCoordinates
        from ..models.mount_info_response_primary_axis_rates_item import MountInfoResponsePrimaryAxisRatesItem
        from ..models.mount_info_response_secondary_axis_rates_item import MountInfoResponseSecondaryAxisRatesItem
        from ..models.mount_info_response_tracking_rate import MountInfoResponseTrackingRate

        d = src_dict.copy()
        connected = d.pop("Connected")

        name = d.pop("Name")

        display_name = d.pop("DisplayName")

        device_id = d.pop("DeviceId")

        _tracking_mode = d.pop("TrackingMode", UNSET)
        tracking_mode: Union[Unset, MountInfoResponseTrackingMode]
        if isinstance(_tracking_mode, Unset):
            tracking_mode = UNSET
        else:
            tracking_mode = MountInfoResponseTrackingMode(_tracking_mode)

        sidereal_time = d.pop("SiderealTime", UNSET)

        right_ascension = d.pop("RightAscension", UNSET)

        declination = d.pop("Declination", UNSET)

        site_latitude = d.pop("SiteLatitude", UNSET)

        site_longitude = d.pop("SiteLongitude", UNSET)

        site_elevation = d.pop("SiteElevation", UNSET)

        right_ascension_string = d.pop("RightAscensionString", UNSET)

        declination_string = d.pop("DeclinationString", UNSET)

        _coordinates = d.pop("Coordinates", UNSET)
        coordinates: Union[Unset, MountInfoResponseCoordinates]
        if isinstance(_coordinates, Unset):
            coordinates = UNSET
        else:
            coordinates = MountInfoResponseCoordinates.from_dict(_coordinates)

        time_to_meridian_flip = d.pop("TimeToMeridianFlip", UNSET)

        _side_of_pier = d.pop("SideOfPier", UNSET)
        side_of_pier: Union[Unset, MountInfoResponseSideOfPier]
        if isinstance(_side_of_pier, Unset):
            side_of_pier = UNSET
        else:
            side_of_pier = MountInfoResponseSideOfPier(_side_of_pier)

        altitude = d.pop("Altitude", UNSET)

        altitude_string = d.pop("AltitudeString", UNSET)

        azimuth = d.pop("Azimuth", UNSET)

        azimuth_string = d.pop("AzimuthString", UNSET)

        sidereal_time_string = d.pop("SiderealTimeString", UNSET)

        hours_to_meridian_string = d.pop("HoursToMeridianString", UNSET)

        at_park = d.pop("AtPark", UNSET)

        _tracking_rate = d.pop("TrackingRate", UNSET)
        tracking_rate: Union[Unset, MountInfoResponseTrackingRate]
        if isinstance(_tracking_rate, Unset):
            tracking_rate = UNSET
        else:
            tracking_rate = MountInfoResponseTrackingRate.from_dict(_tracking_rate)

        tracking_enabled = d.pop("TrackingEnabled", UNSET)

        tracking_modes = []
        _tracking_modes = d.pop("TrackingModes", UNSET)
        for tracking_modes_item_data in _tracking_modes or []:
            tracking_modes_item = MountInfoResponseTrackingModesItem(tracking_modes_item_data)

            tracking_modes.append(tracking_modes_item)

        at_home = d.pop("AtHome", UNSET)

        can_find_home = d.pop("CanFindHome", UNSET)

        can_park = d.pop("CanPark", UNSET)

        can_set_park = d.pop("CanSetPark", UNSET)

        can_set_tracking_enabled = d.pop("CanSetTrackingEnabled", UNSET)

        can_set_declination_rate = d.pop("CanSetDeclinationRate", UNSET)

        can_set_right_ascension_rate = d.pop("CanSetRightAscensionRate", UNSET)

        _equatorial_system = d.pop("EquatorialSystem", UNSET)
        equatorial_system: Union[Unset, MountInfoResponseEquatorialSystem]
        if isinstance(_equatorial_system, Unset):
            equatorial_system = UNSET
        else:
            equatorial_system = MountInfoResponseEquatorialSystem(_equatorial_system)

        has_unknown_epoch = d.pop("HasUnknownEpoch", UNSET)

        time_to_meridian_flip_string = d.pop("TimeToMeridianFlipString", UNSET)

        slewing = d.pop("Slewing", UNSET)

        guide_rate_right_ascension_arcsec_per_sec = d.pop("GuideRateRightAscensionArcsecPerSec", UNSET)

        guide_rate_declination_arcsec_per_sec = d.pop("GuideRateDeclinationArcsecPerSec", UNSET)

        can_move_primary_axis = d.pop("CanMovePrimaryAxis", UNSET)

        can_move_secondary_axis = d.pop("CanMoveSecondaryAxis", UNSET)

        primary_axis_rates = []
        _primary_axis_rates = d.pop("PrimaryAxisRates", UNSET)
        for primary_axis_rates_item_data in _primary_axis_rates or []:
            primary_axis_rates_item = MountInfoResponsePrimaryAxisRatesItem.from_dict(primary_axis_rates_item_data)

            primary_axis_rates.append(primary_axis_rates_item)

        secondary_axis_rates = []
        _secondary_axis_rates = d.pop("SecondaryAxisRates", UNSET)
        for secondary_axis_rates_item_data in _secondary_axis_rates or []:
            secondary_axis_rates_item = MountInfoResponseSecondaryAxisRatesItem.from_dict(
                secondary_axis_rates_item_data
            )

            secondary_axis_rates.append(secondary_axis_rates_item)

        supported_actions = cast(List[str], d.pop("SupportedActions", UNSET))

        _alignment_mode = d.pop("AlignmentMode", UNSET)
        alignment_mode: Union[Unset, MountInfoResponseAlignmentMode]
        if isinstance(_alignment_mode, Unset):
            alignment_mode = UNSET
        else:
            alignment_mode = MountInfoResponseAlignmentMode(_alignment_mode)

        can_pulse_guide = d.pop("CanPulseGuide", UNSET)

        is_pulse_guiding = d.pop("IsPulseGuiding", UNSET)

        can_set_pier_side = d.pop("CanSetPierSide", UNSET)

        can_slew = d.pop("CanSlew", UNSET)

        utc_date = d.pop("UTCDate", UNSET)

        mount_info_response = cls(
            connected=connected,
            name=name,
            display_name=display_name,
            device_id=device_id,
            tracking_mode=tracking_mode,
            sidereal_time=sidereal_time,
            right_ascension=right_ascension,
            declination=declination,
            site_latitude=site_latitude,
            site_longitude=site_longitude,
            site_elevation=site_elevation,
            right_ascension_string=right_ascension_string,
            declination_string=declination_string,
            coordinates=coordinates,
            time_to_meridian_flip=time_to_meridian_flip,
            side_of_pier=side_of_pier,
            altitude=altitude,
            altitude_string=altitude_string,
            azimuth=azimuth,
            azimuth_string=azimuth_string,
            sidereal_time_string=sidereal_time_string,
            hours_to_meridian_string=hours_to_meridian_string,
            at_park=at_park,
            tracking_rate=tracking_rate,
            tracking_enabled=tracking_enabled,
            tracking_modes=tracking_modes,
            at_home=at_home,
            can_find_home=can_find_home,
            can_park=can_park,
            can_set_park=can_set_park,
            can_set_tracking_enabled=can_set_tracking_enabled,
            can_set_declination_rate=can_set_declination_rate,
            can_set_right_ascension_rate=can_set_right_ascension_rate,
            equatorial_system=equatorial_system,
            has_unknown_epoch=has_unknown_epoch,
            time_to_meridian_flip_string=time_to_meridian_flip_string,
            slewing=slewing,
            guide_rate_right_ascension_arcsec_per_sec=guide_rate_right_ascension_arcsec_per_sec,
            guide_rate_declination_arcsec_per_sec=guide_rate_declination_arcsec_per_sec,
            can_move_primary_axis=can_move_primary_axis,
            can_move_secondary_axis=can_move_secondary_axis,
            primary_axis_rates=primary_axis_rates,
            secondary_axis_rates=secondary_axis_rates,
            supported_actions=supported_actions,
            alignment_mode=alignment_mode,
            can_pulse_guide=can_pulse_guide,
            is_pulse_guiding=is_pulse_guiding,
            can_set_pier_side=can_set_pier_side,
            can_slew=can_slew,
            utc_date=utc_date,
        )

        mount_info_response.additional_properties = d
        return mount_info_response

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

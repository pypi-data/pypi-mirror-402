from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_plate_solve_settings_blind_solver_type import (
    ProfileInfoResponsePlateSolveSettingsBlindSolverType,
)
from ..models.profile_info_response_plate_solve_settings_pin_point_catalog_type import (
    ProfileInfoResponsePlateSolveSettingsPinPointCatalogType,
)
from ..models.profile_info_response_plate_solve_settings_plate_solver_type import (
    ProfileInfoResponsePlateSolveSettingsPlateSolverType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponsePlateSolveSettings")


@_attrs_define
class ProfileInfoResponsePlateSolveSettings:
    """
    Attributes:
        astrometry_url (Union[Unset, str]):
        astrometry_api_key (Union[Unset, str]):
        blind_solver_type (Union[Unset, ProfileInfoResponsePlateSolveSettingsBlindSolverType]):
        cygwin_location (Union[Unset, str]):
        exposure_time (Union[Unset, int]):
        gain (Union[Unset, int]):
        binning (Union[Unset, int]):
        plate_solver_type (Union[Unset, ProfileInfoResponsePlateSolveSettingsPlateSolverType]):
        ps2_location (Union[Unset, str]):
        ps3_location (Union[Unset, str]):
        regions (Union[Unset, int]):
        search_radius (Union[Unset, int]):
        threshold (Union[Unset, int]):
        rotation_tolerance (Union[Unset, int]):
        reattempt_delay (Union[Unset, int]):
        number_of_attempts (Union[Unset, int]):
        asps_location (Union[Unset, str]):
        astap_location (Union[Unset, str]):
        down_sample_factor (Union[Unset, int]):
        max_objects (Union[Unset, int]):
        sync (Union[Unset, bool]):
        slew_to_target (Union[Unset, bool]):
        blind_failover_enabled (Union[Unset, bool]):
        the_sky_x_host (Union[Unset, str]):
        the_sky_x_port (Union[Unset, int]):
        pin_point_catalog_type (Union[Unset, ProfileInfoResponsePlateSolveSettingsPinPointCatalogType]):
        pin_point_catalog_root (Union[Unset, str]):
        pin_point_max_magnitude (Union[Unset, int]):
        pin_point_expansion (Union[Unset, int]):
        pin_point_all_sky_api_key (Union[Unset, str]):
        pin_point_all_sky_api_host (Union[Unset, str]):
    """

    astrometry_url: Union[Unset, str] = UNSET
    astrometry_api_key: Union[Unset, str] = UNSET
    blind_solver_type: Union[Unset, ProfileInfoResponsePlateSolveSettingsBlindSolverType] = UNSET
    cygwin_location: Union[Unset, str] = UNSET
    exposure_time: Union[Unset, int] = UNSET
    gain: Union[Unset, int] = UNSET
    binning: Union[Unset, int] = UNSET
    plate_solver_type: Union[Unset, ProfileInfoResponsePlateSolveSettingsPlateSolverType] = UNSET
    ps2_location: Union[Unset, str] = UNSET
    ps3_location: Union[Unset, str] = UNSET
    regions: Union[Unset, int] = UNSET
    search_radius: Union[Unset, int] = UNSET
    threshold: Union[Unset, int] = UNSET
    rotation_tolerance: Union[Unset, int] = UNSET
    reattempt_delay: Union[Unset, int] = UNSET
    number_of_attempts: Union[Unset, int] = UNSET
    asps_location: Union[Unset, str] = UNSET
    astap_location: Union[Unset, str] = UNSET
    down_sample_factor: Union[Unset, int] = UNSET
    max_objects: Union[Unset, int] = UNSET
    sync: Union[Unset, bool] = UNSET
    slew_to_target: Union[Unset, bool] = UNSET
    blind_failover_enabled: Union[Unset, bool] = UNSET
    the_sky_x_host: Union[Unset, str] = UNSET
    the_sky_x_port: Union[Unset, int] = UNSET
    pin_point_catalog_type: Union[Unset, ProfileInfoResponsePlateSolveSettingsPinPointCatalogType] = UNSET
    pin_point_catalog_root: Union[Unset, str] = UNSET
    pin_point_max_magnitude: Union[Unset, int] = UNSET
    pin_point_expansion: Union[Unset, int] = UNSET
    pin_point_all_sky_api_key: Union[Unset, str] = UNSET
    pin_point_all_sky_api_host: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        astrometry_url = self.astrometry_url

        astrometry_api_key = self.astrometry_api_key

        blind_solver_type: Union[Unset, str] = UNSET
        if not isinstance(self.blind_solver_type, Unset):
            blind_solver_type = self.blind_solver_type.value

        cygwin_location = self.cygwin_location

        exposure_time = self.exposure_time

        gain = self.gain

        binning = self.binning

        plate_solver_type: Union[Unset, str] = UNSET
        if not isinstance(self.plate_solver_type, Unset):
            plate_solver_type = self.plate_solver_type.value

        ps2_location = self.ps2_location

        ps3_location = self.ps3_location

        regions = self.regions

        search_radius = self.search_radius

        threshold = self.threshold

        rotation_tolerance = self.rotation_tolerance

        reattempt_delay = self.reattempt_delay

        number_of_attempts = self.number_of_attempts

        asps_location = self.asps_location

        astap_location = self.astap_location

        down_sample_factor = self.down_sample_factor

        max_objects = self.max_objects

        sync = self.sync

        slew_to_target = self.slew_to_target

        blind_failover_enabled = self.blind_failover_enabled

        the_sky_x_host = self.the_sky_x_host

        the_sky_x_port = self.the_sky_x_port

        pin_point_catalog_type: Union[Unset, str] = UNSET
        if not isinstance(self.pin_point_catalog_type, Unset):
            pin_point_catalog_type = self.pin_point_catalog_type.value

        pin_point_catalog_root = self.pin_point_catalog_root

        pin_point_max_magnitude = self.pin_point_max_magnitude

        pin_point_expansion = self.pin_point_expansion

        pin_point_all_sky_api_key = self.pin_point_all_sky_api_key

        pin_point_all_sky_api_host = self.pin_point_all_sky_api_host

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if astrometry_url is not UNSET:
            field_dict["AstrometryURL"] = astrometry_url
        if astrometry_api_key is not UNSET:
            field_dict["AstrometryAPIKey"] = astrometry_api_key
        if blind_solver_type is not UNSET:
            field_dict["BlindSolverType"] = blind_solver_type
        if cygwin_location is not UNSET:
            field_dict["CygwinLocation"] = cygwin_location
        if exposure_time is not UNSET:
            field_dict["ExposureTime"] = exposure_time
        if gain is not UNSET:
            field_dict["Gain"] = gain
        if binning is not UNSET:
            field_dict["Binning"] = binning
        if plate_solver_type is not UNSET:
            field_dict["PlateSolverType"] = plate_solver_type
        if ps2_location is not UNSET:
            field_dict["PS2Location"] = ps2_location
        if ps3_location is not UNSET:
            field_dict["PS3Location"] = ps3_location
        if regions is not UNSET:
            field_dict["Regions"] = regions
        if search_radius is not UNSET:
            field_dict["SearchRadius"] = search_radius
        if threshold is not UNSET:
            field_dict["Threshold"] = threshold
        if rotation_tolerance is not UNSET:
            field_dict["RotationTolerance"] = rotation_tolerance
        if reattempt_delay is not UNSET:
            field_dict["ReattemptDelay"] = reattempt_delay
        if number_of_attempts is not UNSET:
            field_dict["NumberOfAttempts"] = number_of_attempts
        if asps_location is not UNSET:
            field_dict["AspsLocation"] = asps_location
        if astap_location is not UNSET:
            field_dict["ASTAPLocation"] = astap_location
        if down_sample_factor is not UNSET:
            field_dict["DownSampleFactor"] = down_sample_factor
        if max_objects is not UNSET:
            field_dict["MaxObjects"] = max_objects
        if sync is not UNSET:
            field_dict["Sync"] = sync
        if slew_to_target is not UNSET:
            field_dict["SlewToTarget"] = slew_to_target
        if blind_failover_enabled is not UNSET:
            field_dict["BlindFailoverEnabled"] = blind_failover_enabled
        if the_sky_x_host is not UNSET:
            field_dict["TheSkyXHost"] = the_sky_x_host
        if the_sky_x_port is not UNSET:
            field_dict["TheSkyXPort"] = the_sky_x_port
        if pin_point_catalog_type is not UNSET:
            field_dict["PinPointCatalogType"] = pin_point_catalog_type
        if pin_point_catalog_root is not UNSET:
            field_dict["PinPointCatalogRoot"] = pin_point_catalog_root
        if pin_point_max_magnitude is not UNSET:
            field_dict["PinPointMaxMagnitude"] = pin_point_max_magnitude
        if pin_point_expansion is not UNSET:
            field_dict["PinPointExpansion"] = pin_point_expansion
        if pin_point_all_sky_api_key is not UNSET:
            field_dict["PinPointAllSkyApiKey"] = pin_point_all_sky_api_key
        if pin_point_all_sky_api_host is not UNSET:
            field_dict["PinPointAllSkyApiHost"] = pin_point_all_sky_api_host

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        astrometry_url = d.pop("AstrometryURL", UNSET)

        astrometry_api_key = d.pop("AstrometryAPIKey", UNSET)

        _blind_solver_type = d.pop("BlindSolverType", UNSET)
        blind_solver_type: Union[Unset, ProfileInfoResponsePlateSolveSettingsBlindSolverType]
        if isinstance(_blind_solver_type, Unset):
            blind_solver_type = UNSET
        else:
            blind_solver_type = ProfileInfoResponsePlateSolveSettingsBlindSolverType(_blind_solver_type)

        cygwin_location = d.pop("CygwinLocation", UNSET)

        exposure_time = d.pop("ExposureTime", UNSET)

        gain = d.pop("Gain", UNSET)

        binning = d.pop("Binning", UNSET)

        _plate_solver_type = d.pop("PlateSolverType", UNSET)
        plate_solver_type: Union[Unset, ProfileInfoResponsePlateSolveSettingsPlateSolverType]
        if isinstance(_plate_solver_type, Unset):
            plate_solver_type = UNSET
        else:
            plate_solver_type = ProfileInfoResponsePlateSolveSettingsPlateSolverType(_plate_solver_type)

        ps2_location = d.pop("PS2Location", UNSET)

        ps3_location = d.pop("PS3Location", UNSET)

        regions = d.pop("Regions", UNSET)

        search_radius = d.pop("SearchRadius", UNSET)

        threshold = d.pop("Threshold", UNSET)

        rotation_tolerance = d.pop("RotationTolerance", UNSET)

        reattempt_delay = d.pop("ReattemptDelay", UNSET)

        number_of_attempts = d.pop("NumberOfAttempts", UNSET)

        asps_location = d.pop("AspsLocation", UNSET)

        astap_location = d.pop("ASTAPLocation", UNSET)

        down_sample_factor = d.pop("DownSampleFactor", UNSET)

        max_objects = d.pop("MaxObjects", UNSET)

        sync = d.pop("Sync", UNSET)

        slew_to_target = d.pop("SlewToTarget", UNSET)

        blind_failover_enabled = d.pop("BlindFailoverEnabled", UNSET)

        the_sky_x_host = d.pop("TheSkyXHost", UNSET)

        the_sky_x_port = d.pop("TheSkyXPort", UNSET)

        _pin_point_catalog_type = d.pop("PinPointCatalogType", UNSET)
        pin_point_catalog_type: Union[Unset, ProfileInfoResponsePlateSolveSettingsPinPointCatalogType]
        if isinstance(_pin_point_catalog_type, Unset):
            pin_point_catalog_type = UNSET
        else:
            pin_point_catalog_type = ProfileInfoResponsePlateSolveSettingsPinPointCatalogType(_pin_point_catalog_type)

        pin_point_catalog_root = d.pop("PinPointCatalogRoot", UNSET)

        pin_point_max_magnitude = d.pop("PinPointMaxMagnitude", UNSET)

        pin_point_expansion = d.pop("PinPointExpansion", UNSET)

        pin_point_all_sky_api_key = d.pop("PinPointAllSkyApiKey", UNSET)

        pin_point_all_sky_api_host = d.pop("PinPointAllSkyApiHost", UNSET)

        profile_info_response_plate_solve_settings = cls(
            astrometry_url=astrometry_url,
            astrometry_api_key=astrometry_api_key,
            blind_solver_type=blind_solver_type,
            cygwin_location=cygwin_location,
            exposure_time=exposure_time,
            gain=gain,
            binning=binning,
            plate_solver_type=plate_solver_type,
            ps2_location=ps2_location,
            ps3_location=ps3_location,
            regions=regions,
            search_radius=search_radius,
            threshold=threshold,
            rotation_tolerance=rotation_tolerance,
            reattempt_delay=reattempt_delay,
            number_of_attempts=number_of_attempts,
            asps_location=asps_location,
            astap_location=astap_location,
            down_sample_factor=down_sample_factor,
            max_objects=max_objects,
            sync=sync,
            slew_to_target=slew_to_target,
            blind_failover_enabled=blind_failover_enabled,
            the_sky_x_host=the_sky_x_host,
            the_sky_x_port=the_sky_x_port,
            pin_point_catalog_type=pin_point_catalog_type,
            pin_point_catalog_root=pin_point_catalog_root,
            pin_point_max_magnitude=pin_point_max_magnitude,
            pin_point_expansion=pin_point_expansion,
            pin_point_all_sky_api_key=pin_point_all_sky_api_key,
            pin_point_all_sky_api_host=pin_point_all_sky_api_host,
        )

        profile_info_response_plate_solve_settings.additional_properties = d
        return profile_info_response_plate_solve_settings

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

from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_camera_settings_bayer_pattern import ProfileInfoResponseCameraSettingsBayerPattern
from ..models.profile_info_response_camera_settings_bulb_mode import ProfileInfoResponseCameraSettingsBulbMode
from ..models.profile_info_response_camera_settings_raw_converter import ProfileInfoResponseCameraSettingsRawConverter
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseCameraSettings")


@_attrs_define
class ProfileInfoResponseCameraSettings:
    """
    Attributes:
        bit_depth (Union[Unset, int]):
        bulb_mode (Union[Unset, ProfileInfoResponseCameraSettingsBulbMode]):
        id (Union[Unset, str]):
        pixel_size (Union[Unset, int]):
        raw_converter (Union[Unset, ProfileInfoResponseCameraSettingsRawConverter]):
        serial_port (Union[Unset, str]):
        min_flat_exposure_time (Union[Unset, float]):
        max_flat_exposure_time (Union[Unset, int]):
        file_camera_folder (Union[Unset, str]):
        file_camera_use_bulb_mode (Union[Unset, bool]):
        file_camera_is_bayered (Union[Unset, bool]):
        file_camera_extension (Union[Unset, str]):
        file_camera_always_listen (Union[Unset, bool]):
        file_camera_download_delay (Union[Unset, int]):
        bayer_pattern (Union[Unset, ProfileInfoResponseCameraSettingsBayerPattern]):
        fli_enable_flood_flush (Union[Unset, bool]):
        fli_enable_snapshot_flood_flush (Union[Unset, bool]):
        fli_flood_duration (Union[Unset, int]):
        fli_flush_count (Union[Unset, int]):
        bit_scaling (Union[Unset, bool]):
        cooling_duration (Union[Unset, int]):
        warming_duration (Union[Unset, int]):
        temperature (Union[Unset, int]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):
        qhy_include_overscan (Union[Unset, bool]):
        timeout (Union[Unset, int]):
        dew_heater_on (Union[Unset, bool]):
        ascom_allow_uneven_pixel_dimension (Union[Unset, bool]):
        mirror_lockup_delay (Union[Unset, int]):
        bin_average_enabled (Union[Unset, bool]):
        tracking_camera_ascom_server_enabled (Union[Unset, bool]):
        tracking_camera_ascom_server_pipe_name (Union[Unset, str]):
        tracking_camera_ascom_server_logging_enabled (Union[Unset, bool]):
        sbig_use_external_ccd_tracker (Union[Unset, bool]):
        atik_gain_preset (Union[Unset, int]):
        atik_exposure_speed (Union[Unset, int]):
        atik_window_heater_power_level (Union[Unset, int]):
        touptek_alike_ultra_mode (Union[Unset, bool]):
        touptek_alike_high_fullwell (Union[Unset, bool]):
        touptek_alike_led_lights (Union[Unset, bool]):
        touptek_alike_dew_heater_strength (Union[Unset, int]):
        generic_camera_dew_heater_strength (Union[Unset, int]):
        generic_camera_fan_speed (Union[Unset, int]):
        zwo_asi_mono_bin_mode (Union[Unset, bool]):
        ascom_create_32_bit_data (Union[Unset, bool]):
        bad_pixel_correction (Union[Unset, bool]):
        bad_pixel_correction_threshold (Union[Unset, int]):
    """

    bit_depth: Union[Unset, int] = UNSET
    bulb_mode: Union[Unset, ProfileInfoResponseCameraSettingsBulbMode] = UNSET
    id: Union[Unset, str] = UNSET
    pixel_size: Union[Unset, int] = UNSET
    raw_converter: Union[Unset, ProfileInfoResponseCameraSettingsRawConverter] = UNSET
    serial_port: Union[Unset, str] = UNSET
    min_flat_exposure_time: Union[Unset, float] = UNSET
    max_flat_exposure_time: Union[Unset, int] = UNSET
    file_camera_folder: Union[Unset, str] = UNSET
    file_camera_use_bulb_mode: Union[Unset, bool] = UNSET
    file_camera_is_bayered: Union[Unset, bool] = UNSET
    file_camera_extension: Union[Unset, str] = UNSET
    file_camera_always_listen: Union[Unset, bool] = UNSET
    file_camera_download_delay: Union[Unset, int] = UNSET
    bayer_pattern: Union[Unset, ProfileInfoResponseCameraSettingsBayerPattern] = UNSET
    fli_enable_flood_flush: Union[Unset, bool] = UNSET
    fli_enable_snapshot_flood_flush: Union[Unset, bool] = UNSET
    fli_flood_duration: Union[Unset, int] = UNSET
    fli_flush_count: Union[Unset, int] = UNSET
    bit_scaling: Union[Unset, bool] = UNSET
    cooling_duration: Union[Unset, int] = UNSET
    warming_duration: Union[Unset, int] = UNSET
    temperature: Union[Unset, int] = UNSET
    gain: Union[Unset, int] = UNSET
    offset: Union[Unset, int] = UNSET
    qhy_include_overscan: Union[Unset, bool] = UNSET
    timeout: Union[Unset, int] = UNSET
    dew_heater_on: Union[Unset, bool] = UNSET
    ascom_allow_uneven_pixel_dimension: Union[Unset, bool] = UNSET
    mirror_lockup_delay: Union[Unset, int] = UNSET
    bin_average_enabled: Union[Unset, bool] = UNSET
    tracking_camera_ascom_server_enabled: Union[Unset, bool] = UNSET
    tracking_camera_ascom_server_pipe_name: Union[Unset, str] = UNSET
    tracking_camera_ascom_server_logging_enabled: Union[Unset, bool] = UNSET
    sbig_use_external_ccd_tracker: Union[Unset, bool] = UNSET
    atik_gain_preset: Union[Unset, int] = UNSET
    atik_exposure_speed: Union[Unset, int] = UNSET
    atik_window_heater_power_level: Union[Unset, int] = UNSET
    touptek_alike_ultra_mode: Union[Unset, bool] = UNSET
    touptek_alike_high_fullwell: Union[Unset, bool] = UNSET
    touptek_alike_led_lights: Union[Unset, bool] = UNSET
    touptek_alike_dew_heater_strength: Union[Unset, int] = UNSET
    generic_camera_dew_heater_strength: Union[Unset, int] = UNSET
    generic_camera_fan_speed: Union[Unset, int] = UNSET
    zwo_asi_mono_bin_mode: Union[Unset, bool] = UNSET
    ascom_create_32_bit_data: Union[Unset, bool] = UNSET
    bad_pixel_correction: Union[Unset, bool] = UNSET
    bad_pixel_correction_threshold: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        bit_depth = self.bit_depth

        bulb_mode: Union[Unset, str] = UNSET
        if not isinstance(self.bulb_mode, Unset):
            bulb_mode = self.bulb_mode.value

        id = self.id

        pixel_size = self.pixel_size

        raw_converter: Union[Unset, str] = UNSET
        if not isinstance(self.raw_converter, Unset):
            raw_converter = self.raw_converter.value

        serial_port = self.serial_port

        min_flat_exposure_time = self.min_flat_exposure_time

        max_flat_exposure_time = self.max_flat_exposure_time

        file_camera_folder = self.file_camera_folder

        file_camera_use_bulb_mode = self.file_camera_use_bulb_mode

        file_camera_is_bayered = self.file_camera_is_bayered

        file_camera_extension = self.file_camera_extension

        file_camera_always_listen = self.file_camera_always_listen

        file_camera_download_delay = self.file_camera_download_delay

        bayer_pattern: Union[Unset, str] = UNSET
        if not isinstance(self.bayer_pattern, Unset):
            bayer_pattern = self.bayer_pattern.value

        fli_enable_flood_flush = self.fli_enable_flood_flush

        fli_enable_snapshot_flood_flush = self.fli_enable_snapshot_flood_flush

        fli_flood_duration = self.fli_flood_duration

        fli_flush_count = self.fli_flush_count

        bit_scaling = self.bit_scaling

        cooling_duration = self.cooling_duration

        warming_duration = self.warming_duration

        temperature = self.temperature

        gain = self.gain

        offset = self.offset

        qhy_include_overscan = self.qhy_include_overscan

        timeout = self.timeout

        dew_heater_on = self.dew_heater_on

        ascom_allow_uneven_pixel_dimension = self.ascom_allow_uneven_pixel_dimension

        mirror_lockup_delay = self.mirror_lockup_delay

        bin_average_enabled = self.bin_average_enabled

        tracking_camera_ascom_server_enabled = self.tracking_camera_ascom_server_enabled

        tracking_camera_ascom_server_pipe_name = self.tracking_camera_ascom_server_pipe_name

        tracking_camera_ascom_server_logging_enabled = self.tracking_camera_ascom_server_logging_enabled

        sbig_use_external_ccd_tracker = self.sbig_use_external_ccd_tracker

        atik_gain_preset = self.atik_gain_preset

        atik_exposure_speed = self.atik_exposure_speed

        atik_window_heater_power_level = self.atik_window_heater_power_level

        touptek_alike_ultra_mode = self.touptek_alike_ultra_mode

        touptek_alike_high_fullwell = self.touptek_alike_high_fullwell

        touptek_alike_led_lights = self.touptek_alike_led_lights

        touptek_alike_dew_heater_strength = self.touptek_alike_dew_heater_strength

        generic_camera_dew_heater_strength = self.generic_camera_dew_heater_strength

        generic_camera_fan_speed = self.generic_camera_fan_speed

        zwo_asi_mono_bin_mode = self.zwo_asi_mono_bin_mode

        ascom_create_32_bit_data = self.ascom_create_32_bit_data

        bad_pixel_correction = self.bad_pixel_correction

        bad_pixel_correction_threshold = self.bad_pixel_correction_threshold

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bit_depth is not UNSET:
            field_dict["BitDepth"] = bit_depth
        if bulb_mode is not UNSET:
            field_dict["BulbMode"] = bulb_mode
        if id is not UNSET:
            field_dict["Id"] = id
        if pixel_size is not UNSET:
            field_dict["PixelSize"] = pixel_size
        if raw_converter is not UNSET:
            field_dict["RawConverter"] = raw_converter
        if serial_port is not UNSET:
            field_dict["SerialPort"] = serial_port
        if min_flat_exposure_time is not UNSET:
            field_dict["MinFlatExposureTime"] = min_flat_exposure_time
        if max_flat_exposure_time is not UNSET:
            field_dict["MaxFlatExposureTime"] = max_flat_exposure_time
        if file_camera_folder is not UNSET:
            field_dict["FileCameraFolder"] = file_camera_folder
        if file_camera_use_bulb_mode is not UNSET:
            field_dict["FileCameraUseBulbMode"] = file_camera_use_bulb_mode
        if file_camera_is_bayered is not UNSET:
            field_dict["FileCameraIsBayered"] = file_camera_is_bayered
        if file_camera_extension is not UNSET:
            field_dict["FileCameraExtension"] = file_camera_extension
        if file_camera_always_listen is not UNSET:
            field_dict["FileCameraAlwaysListen"] = file_camera_always_listen
        if file_camera_download_delay is not UNSET:
            field_dict["FileCameraDownloadDelay"] = file_camera_download_delay
        if bayer_pattern is not UNSET:
            field_dict["BayerPattern"] = bayer_pattern
        if fli_enable_flood_flush is not UNSET:
            field_dict["FLIEnableFloodFlush"] = fli_enable_flood_flush
        if fli_enable_snapshot_flood_flush is not UNSET:
            field_dict["FLIEnableSnapshotFloodFlush"] = fli_enable_snapshot_flood_flush
        if fli_flood_duration is not UNSET:
            field_dict["FLIFloodDuration"] = fli_flood_duration
        if fli_flush_count is not UNSET:
            field_dict["FLIFlushCount"] = fli_flush_count
        if bit_scaling is not UNSET:
            field_dict["BitScaling"] = bit_scaling
        if cooling_duration is not UNSET:
            field_dict["CoolingDuration"] = cooling_duration
        if warming_duration is not UNSET:
            field_dict["WarmingDuration"] = warming_duration
        if temperature is not UNSET:
            field_dict["Temperature"] = temperature
        if gain is not UNSET:
            field_dict["Gain"] = gain
        if offset is not UNSET:
            field_dict["Offset"] = offset
        if qhy_include_overscan is not UNSET:
            field_dict["QhyIncludeOverscan"] = qhy_include_overscan
        if timeout is not UNSET:
            field_dict["Timeout"] = timeout
        if dew_heater_on is not UNSET:
            field_dict["DewHeaterOn"] = dew_heater_on
        if ascom_allow_uneven_pixel_dimension is not UNSET:
            field_dict["ASCOMAllowUnevenPixelDimension"] = ascom_allow_uneven_pixel_dimension
        if mirror_lockup_delay is not UNSET:
            field_dict["MirrorLockupDelay"] = mirror_lockup_delay
        if bin_average_enabled is not UNSET:
            field_dict["BinAverageEnabled"] = bin_average_enabled
        if tracking_camera_ascom_server_enabled is not UNSET:
            field_dict["TrackingCameraASCOMServerEnabled"] = tracking_camera_ascom_server_enabled
        if tracking_camera_ascom_server_pipe_name is not UNSET:
            field_dict["TrackingCameraASCOMServerPipeName"] = tracking_camera_ascom_server_pipe_name
        if tracking_camera_ascom_server_logging_enabled is not UNSET:
            field_dict["TrackingCameraASCOMServerLoggingEnabled"] = tracking_camera_ascom_server_logging_enabled
        if sbig_use_external_ccd_tracker is not UNSET:
            field_dict["SBIGUseExternalCcdTracker"] = sbig_use_external_ccd_tracker
        if atik_gain_preset is not UNSET:
            field_dict["AtikGainPreset"] = atik_gain_preset
        if atik_exposure_speed is not UNSET:
            field_dict["AtikExposureSpeed"] = atik_exposure_speed
        if atik_window_heater_power_level is not UNSET:
            field_dict["AtikWindowHeaterPowerLevel"] = atik_window_heater_power_level
        if touptek_alike_ultra_mode is not UNSET:
            field_dict["TouptekAlikeUltraMode"] = touptek_alike_ultra_mode
        if touptek_alike_high_fullwell is not UNSET:
            field_dict["TouptekAlikeHighFullwell"] = touptek_alike_high_fullwell
        if touptek_alike_led_lights is not UNSET:
            field_dict["TouptekAlikeLEDLights"] = touptek_alike_led_lights
        if touptek_alike_dew_heater_strength is not UNSET:
            field_dict["TouptekAlikeDewHeaterStrength"] = touptek_alike_dew_heater_strength
        if generic_camera_dew_heater_strength is not UNSET:
            field_dict["GenericCameraDewHeaterStrength"] = generic_camera_dew_heater_strength
        if generic_camera_fan_speed is not UNSET:
            field_dict["GenericCameraFanSpeed"] = generic_camera_fan_speed
        if zwo_asi_mono_bin_mode is not UNSET:
            field_dict["ZwoAsiMonoBinMode"] = zwo_asi_mono_bin_mode
        if ascom_create_32_bit_data is not UNSET:
            field_dict["ASCOMCreate32BitData"] = ascom_create_32_bit_data
        if bad_pixel_correction is not UNSET:
            field_dict["BadPixelCorrection"] = bad_pixel_correction
        if bad_pixel_correction_threshold is not UNSET:
            field_dict["BadPixelCorrectionThreshold"] = bad_pixel_correction_threshold

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        bit_depth = d.pop("BitDepth", UNSET)

        _bulb_mode = d.pop("BulbMode", UNSET)
        bulb_mode: Union[Unset, ProfileInfoResponseCameraSettingsBulbMode]
        if isinstance(_bulb_mode, Unset):
            bulb_mode = UNSET
        else:
            bulb_mode = ProfileInfoResponseCameraSettingsBulbMode(_bulb_mode)

        id = d.pop("Id", UNSET)

        pixel_size = d.pop("PixelSize", UNSET)

        _raw_converter = d.pop("RawConverter", UNSET)
        raw_converter: Union[Unset, ProfileInfoResponseCameraSettingsRawConverter]
        if isinstance(_raw_converter, Unset):
            raw_converter = UNSET
        else:
            raw_converter = ProfileInfoResponseCameraSettingsRawConverter(_raw_converter)

        serial_port = d.pop("SerialPort", UNSET)

        min_flat_exposure_time = d.pop("MinFlatExposureTime", UNSET)

        max_flat_exposure_time = d.pop("MaxFlatExposureTime", UNSET)

        file_camera_folder = d.pop("FileCameraFolder", UNSET)

        file_camera_use_bulb_mode = d.pop("FileCameraUseBulbMode", UNSET)

        file_camera_is_bayered = d.pop("FileCameraIsBayered", UNSET)

        file_camera_extension = d.pop("FileCameraExtension", UNSET)

        file_camera_always_listen = d.pop("FileCameraAlwaysListen", UNSET)

        file_camera_download_delay = d.pop("FileCameraDownloadDelay", UNSET)

        _bayer_pattern = d.pop("BayerPattern", UNSET)
        bayer_pattern: Union[Unset, ProfileInfoResponseCameraSettingsBayerPattern]
        if isinstance(_bayer_pattern, Unset):
            bayer_pattern = UNSET
        else:
            bayer_pattern = ProfileInfoResponseCameraSettingsBayerPattern(_bayer_pattern)

        fli_enable_flood_flush = d.pop("FLIEnableFloodFlush", UNSET)

        fli_enable_snapshot_flood_flush = d.pop("FLIEnableSnapshotFloodFlush", UNSET)

        fli_flood_duration = d.pop("FLIFloodDuration", UNSET)

        fli_flush_count = d.pop("FLIFlushCount", UNSET)

        bit_scaling = d.pop("BitScaling", UNSET)

        cooling_duration = d.pop("CoolingDuration", UNSET)

        warming_duration = d.pop("WarmingDuration", UNSET)

        temperature = d.pop("Temperature", UNSET)

        gain = d.pop("Gain", UNSET)

        offset = d.pop("Offset", UNSET)

        qhy_include_overscan = d.pop("QhyIncludeOverscan", UNSET)

        timeout = d.pop("Timeout", UNSET)

        dew_heater_on = d.pop("DewHeaterOn", UNSET)

        ascom_allow_uneven_pixel_dimension = d.pop("ASCOMAllowUnevenPixelDimension", UNSET)

        mirror_lockup_delay = d.pop("MirrorLockupDelay", UNSET)

        bin_average_enabled = d.pop("BinAverageEnabled", UNSET)

        tracking_camera_ascom_server_enabled = d.pop("TrackingCameraASCOMServerEnabled", UNSET)

        tracking_camera_ascom_server_pipe_name = d.pop("TrackingCameraASCOMServerPipeName", UNSET)

        tracking_camera_ascom_server_logging_enabled = d.pop("TrackingCameraASCOMServerLoggingEnabled", UNSET)

        sbig_use_external_ccd_tracker = d.pop("SBIGUseExternalCcdTracker", UNSET)

        atik_gain_preset = d.pop("AtikGainPreset", UNSET)

        atik_exposure_speed = d.pop("AtikExposureSpeed", UNSET)

        atik_window_heater_power_level = d.pop("AtikWindowHeaterPowerLevel", UNSET)

        touptek_alike_ultra_mode = d.pop("TouptekAlikeUltraMode", UNSET)

        touptek_alike_high_fullwell = d.pop("TouptekAlikeHighFullwell", UNSET)

        touptek_alike_led_lights = d.pop("TouptekAlikeLEDLights", UNSET)

        touptek_alike_dew_heater_strength = d.pop("TouptekAlikeDewHeaterStrength", UNSET)

        generic_camera_dew_heater_strength = d.pop("GenericCameraDewHeaterStrength", UNSET)

        generic_camera_fan_speed = d.pop("GenericCameraFanSpeed", UNSET)

        zwo_asi_mono_bin_mode = d.pop("ZwoAsiMonoBinMode", UNSET)

        ascom_create_32_bit_data = d.pop("ASCOMCreate32BitData", UNSET)

        bad_pixel_correction = d.pop("BadPixelCorrection", UNSET)

        bad_pixel_correction_threshold = d.pop("BadPixelCorrectionThreshold", UNSET)

        profile_info_response_camera_settings = cls(
            bit_depth=bit_depth,
            bulb_mode=bulb_mode,
            id=id,
            pixel_size=pixel_size,
            raw_converter=raw_converter,
            serial_port=serial_port,
            min_flat_exposure_time=min_flat_exposure_time,
            max_flat_exposure_time=max_flat_exposure_time,
            file_camera_folder=file_camera_folder,
            file_camera_use_bulb_mode=file_camera_use_bulb_mode,
            file_camera_is_bayered=file_camera_is_bayered,
            file_camera_extension=file_camera_extension,
            file_camera_always_listen=file_camera_always_listen,
            file_camera_download_delay=file_camera_download_delay,
            bayer_pattern=bayer_pattern,
            fli_enable_flood_flush=fli_enable_flood_flush,
            fli_enable_snapshot_flood_flush=fli_enable_snapshot_flood_flush,
            fli_flood_duration=fli_flood_duration,
            fli_flush_count=fli_flush_count,
            bit_scaling=bit_scaling,
            cooling_duration=cooling_duration,
            warming_duration=warming_duration,
            temperature=temperature,
            gain=gain,
            offset=offset,
            qhy_include_overscan=qhy_include_overscan,
            timeout=timeout,
            dew_heater_on=dew_heater_on,
            ascom_allow_uneven_pixel_dimension=ascom_allow_uneven_pixel_dimension,
            mirror_lockup_delay=mirror_lockup_delay,
            bin_average_enabled=bin_average_enabled,
            tracking_camera_ascom_server_enabled=tracking_camera_ascom_server_enabled,
            tracking_camera_ascom_server_pipe_name=tracking_camera_ascom_server_pipe_name,
            tracking_camera_ascom_server_logging_enabled=tracking_camera_ascom_server_logging_enabled,
            sbig_use_external_ccd_tracker=sbig_use_external_ccd_tracker,
            atik_gain_preset=atik_gain_preset,
            atik_exposure_speed=atik_exposure_speed,
            atik_window_heater_power_level=atik_window_heater_power_level,
            touptek_alike_ultra_mode=touptek_alike_ultra_mode,
            touptek_alike_high_fullwell=touptek_alike_high_fullwell,
            touptek_alike_led_lights=touptek_alike_led_lights,
            touptek_alike_dew_heater_strength=touptek_alike_dew_heater_strength,
            generic_camera_dew_heater_strength=generic_camera_dew_heater_strength,
            generic_camera_fan_speed=generic_camera_fan_speed,
            zwo_asi_mono_bin_mode=zwo_asi_mono_bin_mode,
            ascom_create_32_bit_data=ascom_create_32_bit_data,
            bad_pixel_correction=bad_pixel_correction,
            bad_pixel_correction_threshold=bad_pixel_correction_threshold,
        )

        profile_info_response_camera_settings.additional_properties = d
        return profile_info_response_camera_settings

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

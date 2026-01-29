from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.camera_info_response_camera_state import CameraInfoResponseCameraState
from ..models.camera_info_response_sensor_type import CameraInfoResponseSensorType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.camera_info_response_binning_modes_item import CameraInfoResponseBinningModesItem


T = TypeVar("T", bound="CameraInfoResponse")


@_attrs_define
class CameraInfoResponse:
    """
    Attributes:
        target_temp (Union[Unset, float]):
        at_target_temp (Union[Unset, bool]):
        can_set_temperature (Union[Unset, bool]):
        has_shutter (Union[Unset, bool]):
        temperature (Union[Unset, float]):
        gain (Union[Unset, int]):
        default_gain (Union[Unset, int]):
        electrons_per_adu (Union[Unset, float]):
        bin_x (Union[Unset, int]):
        bit_depth (Union[Unset, int]):
        bin_y (Union[Unset, int]):
        can_set_offset (Union[Unset, bool]):
        can_get_gain (Union[Unset, bool]):
        offset_min (Union[Unset, int]):
        offset_max (Union[Unset, int]):
        offset (Union[Unset, int]):
        default_offset (Union[Unset, int]):
        usb_limit (Union[Unset, int]):
        is_sub_sample_enabled (Union[Unset, bool]):
        camera_state (Union[Unset, CameraInfoResponseCameraState]):
        x_size (Union[Unset, int]):
        y_size (Union[Unset, int]):
        pixel_size (Union[Unset, float]):
        battery (Union[Unset, int]):
        gain_min (Union[Unset, int]):
        gain_max (Union[Unset, int]):
        can_set_gain (Union[Unset, bool]):
        gains (Union[Unset, List[Any]]):
        cooler_on (Union[Unset, bool]):
        cooler_power (Union[Unset, float]):
        has_dew_heater (Union[Unset, bool]):
        dew_heater_on (Union[Unset, bool]):
        can_sub_sample (Union[Unset, bool]):
        sub_sample_x (Union[Unset, int]):
        sub_sample_y (Union[Unset, int]):
        sub_sample_width (Union[Unset, int]):
        sub_sample_height (Union[Unset, int]):
        temperature_set_point (Union[Unset, float]):
        readout_modes (Union[Unset, List[str]]):
        readout_mode (Union[Unset, int]):
        readout_mode_for_snap_images (Union[Unset, int]):
        readout_mode_for_normal_images (Union[Unset, int]):
        is_exposing (Union[Unset, bool]):
        exposure_end_time (Union[Unset, str]):
        last_download_time (Union[Unset, float]):
        sensor_type (Union[Unset, CameraInfoResponseSensorType]):
        bayer_offset_x (Union[Unset, int]):
        bayer_offset_y (Union[Unset, int]):
        binning_modes (Union[Unset, List['CameraInfoResponseBinningModesItem']]):
        exposure_max (Union[Unset, float]):
        exposure_min (Union[Unset, float]):
        live_view_enabled (Union[Unset, bool]):
        can_show_live_view (Union[Unset, bool]):
        supported_actions (Union[Unset, List[str]]):
        can_set_usb_limit (Union[Unset, bool]):
        usb_limit_min (Union[Unset, int]):
        usb_limit_max (Union[Unset, int]):
        connected (Union[Unset, bool]):
        name (Union[Unset, str]):
        display_name (Union[Unset, str]):
        device_id (Union[Unset, str]):
    """

    target_temp: Union[Unset, float] = UNSET
    at_target_temp: Union[Unset, bool] = UNSET
    can_set_temperature: Union[Unset, bool] = UNSET
    has_shutter: Union[Unset, bool] = UNSET
    temperature: Union[Unset, float] = UNSET
    gain: Union[Unset, int] = UNSET
    default_gain: Union[Unset, int] = UNSET
    electrons_per_adu: Union[Unset, float] = UNSET
    bin_x: Union[Unset, int] = UNSET
    bit_depth: Union[Unset, int] = UNSET
    bin_y: Union[Unset, int] = UNSET
    can_set_offset: Union[Unset, bool] = UNSET
    can_get_gain: Union[Unset, bool] = UNSET
    offset_min: Union[Unset, int] = UNSET
    offset_max: Union[Unset, int] = UNSET
    offset: Union[Unset, int] = UNSET
    default_offset: Union[Unset, int] = UNSET
    usb_limit: Union[Unset, int] = UNSET
    is_sub_sample_enabled: Union[Unset, bool] = UNSET
    camera_state: Union[Unset, CameraInfoResponseCameraState] = UNSET
    x_size: Union[Unset, int] = UNSET
    y_size: Union[Unset, int] = UNSET
    pixel_size: Union[Unset, float] = UNSET
    battery: Union[Unset, int] = UNSET
    gain_min: Union[Unset, int] = UNSET
    gain_max: Union[Unset, int] = UNSET
    can_set_gain: Union[Unset, bool] = UNSET
    gains: Union[Unset, List[Any]] = UNSET
    cooler_on: Union[Unset, bool] = UNSET
    cooler_power: Union[Unset, float] = UNSET
    has_dew_heater: Union[Unset, bool] = UNSET
    dew_heater_on: Union[Unset, bool] = UNSET
    can_sub_sample: Union[Unset, bool] = UNSET
    sub_sample_x: Union[Unset, int] = UNSET
    sub_sample_y: Union[Unset, int] = UNSET
    sub_sample_width: Union[Unset, int] = UNSET
    sub_sample_height: Union[Unset, int] = UNSET
    temperature_set_point: Union[Unset, float] = UNSET
    readout_modes: Union[Unset, List[str]] = UNSET
    readout_mode: Union[Unset, int] = UNSET
    readout_mode_for_snap_images: Union[Unset, int] = UNSET
    readout_mode_for_normal_images: Union[Unset, int] = UNSET
    is_exposing: Union[Unset, bool] = UNSET
    exposure_end_time: Union[Unset, str] = UNSET
    last_download_time: Union[Unset, float] = UNSET
    sensor_type: Union[Unset, CameraInfoResponseSensorType] = UNSET
    bayer_offset_x: Union[Unset, int] = UNSET
    bayer_offset_y: Union[Unset, int] = UNSET
    binning_modes: Union[Unset, List["CameraInfoResponseBinningModesItem"]] = UNSET
    exposure_max: Union[Unset, float] = UNSET
    exposure_min: Union[Unset, float] = UNSET
    live_view_enabled: Union[Unset, bool] = UNSET
    can_show_live_view: Union[Unset, bool] = UNSET
    supported_actions: Union[Unset, List[str]] = UNSET
    can_set_usb_limit: Union[Unset, bool] = UNSET
    usb_limit_min: Union[Unset, int] = UNSET
    usb_limit_max: Union[Unset, int] = UNSET
    connected: Union[Unset, bool] = UNSET
    name: Union[Unset, str] = UNSET
    display_name: Union[Unset, str] = UNSET
    device_id: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        target_temp = self.target_temp

        at_target_temp = self.at_target_temp

        can_set_temperature = self.can_set_temperature

        has_shutter = self.has_shutter

        temperature = self.temperature

        gain = self.gain

        default_gain = self.default_gain

        electrons_per_adu = self.electrons_per_adu

        bin_x = self.bin_x

        bit_depth = self.bit_depth

        bin_y = self.bin_y

        can_set_offset = self.can_set_offset

        can_get_gain = self.can_get_gain

        offset_min = self.offset_min

        offset_max = self.offset_max

        offset = self.offset

        default_offset = self.default_offset

        usb_limit = self.usb_limit

        is_sub_sample_enabled = self.is_sub_sample_enabled

        camera_state: Union[Unset, str] = UNSET
        if not isinstance(self.camera_state, Unset):
            camera_state = self.camera_state.value

        x_size = self.x_size

        y_size = self.y_size

        pixel_size = self.pixel_size

        battery = self.battery

        gain_min = self.gain_min

        gain_max = self.gain_max

        can_set_gain = self.can_set_gain

        gains: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.gains, Unset):
            gains = self.gains

        cooler_on = self.cooler_on

        cooler_power = self.cooler_power

        has_dew_heater = self.has_dew_heater

        dew_heater_on = self.dew_heater_on

        can_sub_sample = self.can_sub_sample

        sub_sample_x = self.sub_sample_x

        sub_sample_y = self.sub_sample_y

        sub_sample_width = self.sub_sample_width

        sub_sample_height = self.sub_sample_height

        temperature_set_point = self.temperature_set_point

        readout_modes: Union[Unset, List[str]] = UNSET
        if not isinstance(self.readout_modes, Unset):
            readout_modes = self.readout_modes

        readout_mode = self.readout_mode

        readout_mode_for_snap_images = self.readout_mode_for_snap_images

        readout_mode_for_normal_images = self.readout_mode_for_normal_images

        is_exposing = self.is_exposing

        exposure_end_time = self.exposure_end_time

        last_download_time = self.last_download_time

        sensor_type: Union[Unset, str] = UNSET
        if not isinstance(self.sensor_type, Unset):
            sensor_type = self.sensor_type.value

        bayer_offset_x = self.bayer_offset_x

        bayer_offset_y = self.bayer_offset_y

        binning_modes: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.binning_modes, Unset):
            binning_modes = []
            for binning_modes_item_data in self.binning_modes:
                binning_modes_item = binning_modes_item_data.to_dict()
                binning_modes.append(binning_modes_item)

        exposure_max = self.exposure_max

        exposure_min = self.exposure_min

        live_view_enabled = self.live_view_enabled

        can_show_live_view = self.can_show_live_view

        supported_actions: Union[Unset, List[str]] = UNSET
        if not isinstance(self.supported_actions, Unset):
            supported_actions = self.supported_actions

        can_set_usb_limit = self.can_set_usb_limit

        usb_limit_min = self.usb_limit_min

        usb_limit_max = self.usb_limit_max

        connected = self.connected

        name = self.name

        display_name = self.display_name

        device_id = self.device_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if target_temp is not UNSET:
            field_dict["TargetTemp"] = target_temp
        if at_target_temp is not UNSET:
            field_dict["AtTargetTemp"] = at_target_temp
        if can_set_temperature is not UNSET:
            field_dict["CanSetTemperature"] = can_set_temperature
        if has_shutter is not UNSET:
            field_dict["HasShutter"] = has_shutter
        if temperature is not UNSET:
            field_dict["Temperature"] = temperature
        if gain is not UNSET:
            field_dict["Gain"] = gain
        if default_gain is not UNSET:
            field_dict["DefaultGain"] = default_gain
        if electrons_per_adu is not UNSET:
            field_dict["ElectronsPerADU"] = electrons_per_adu
        if bin_x is not UNSET:
            field_dict["BinX"] = bin_x
        if bit_depth is not UNSET:
            field_dict["BitDepth"] = bit_depth
        if bin_y is not UNSET:
            field_dict["BinY"] = bin_y
        if can_set_offset is not UNSET:
            field_dict["CanSetOffset"] = can_set_offset
        if can_get_gain is not UNSET:
            field_dict["CanGetGain"] = can_get_gain
        if offset_min is not UNSET:
            field_dict["OffsetMin"] = offset_min
        if offset_max is not UNSET:
            field_dict["OffsetMax"] = offset_max
        if offset is not UNSET:
            field_dict["Offset"] = offset
        if default_offset is not UNSET:
            field_dict["DefaultOffset"] = default_offset
        if usb_limit is not UNSET:
            field_dict["USBLimit"] = usb_limit
        if is_sub_sample_enabled is not UNSET:
            field_dict["IsSubSampleEnabled"] = is_sub_sample_enabled
        if camera_state is not UNSET:
            field_dict["CameraState"] = camera_state
        if x_size is not UNSET:
            field_dict["XSize"] = x_size
        if y_size is not UNSET:
            field_dict["YSize"] = y_size
        if pixel_size is not UNSET:
            field_dict["PixelSize"] = pixel_size
        if battery is not UNSET:
            field_dict["Battery"] = battery
        if gain_min is not UNSET:
            field_dict["GainMin"] = gain_min
        if gain_max is not UNSET:
            field_dict["GainMax"] = gain_max
        if can_set_gain is not UNSET:
            field_dict["CanSetGain"] = can_set_gain
        if gains is not UNSET:
            field_dict["Gains"] = gains
        if cooler_on is not UNSET:
            field_dict["CoolerOn"] = cooler_on
        if cooler_power is not UNSET:
            field_dict["CoolerPower"] = cooler_power
        if has_dew_heater is not UNSET:
            field_dict["HasDewHeater"] = has_dew_heater
        if dew_heater_on is not UNSET:
            field_dict["DewHeaterOn"] = dew_heater_on
        if can_sub_sample is not UNSET:
            field_dict["CanSubSample"] = can_sub_sample
        if sub_sample_x is not UNSET:
            field_dict["SubSampleX"] = sub_sample_x
        if sub_sample_y is not UNSET:
            field_dict["SubSampleY"] = sub_sample_y
        if sub_sample_width is not UNSET:
            field_dict["SubSampleWidth"] = sub_sample_width
        if sub_sample_height is not UNSET:
            field_dict["SubSampleHeight"] = sub_sample_height
        if temperature_set_point is not UNSET:
            field_dict["TemperatureSetPoint"] = temperature_set_point
        if readout_modes is not UNSET:
            field_dict["ReadoutModes"] = readout_modes
        if readout_mode is not UNSET:
            field_dict["ReadoutMode"] = readout_mode
        if readout_mode_for_snap_images is not UNSET:
            field_dict["ReadoutModeForSnapImages"] = readout_mode_for_snap_images
        if readout_mode_for_normal_images is not UNSET:
            field_dict["ReadoutModeForNormalImages"] = readout_mode_for_normal_images
        if is_exposing is not UNSET:
            field_dict["IsExposing"] = is_exposing
        if exposure_end_time is not UNSET:
            field_dict["ExposureEndTime"] = exposure_end_time
        if last_download_time is not UNSET:
            field_dict["LastDownloadTime"] = last_download_time
        if sensor_type is not UNSET:
            field_dict["SensorType"] = sensor_type
        if bayer_offset_x is not UNSET:
            field_dict["BayerOffsetX"] = bayer_offset_x
        if bayer_offset_y is not UNSET:
            field_dict["BayerOffsetY"] = bayer_offset_y
        if binning_modes is not UNSET:
            field_dict["BinningModes"] = binning_modes
        if exposure_max is not UNSET:
            field_dict["ExposureMax"] = exposure_max
        if exposure_min is not UNSET:
            field_dict["ExposureMin"] = exposure_min
        if live_view_enabled is not UNSET:
            field_dict["LiveViewEnabled"] = live_view_enabled
        if can_show_live_view is not UNSET:
            field_dict["CanShowLiveView"] = can_show_live_view
        if supported_actions is not UNSET:
            field_dict["SupportedActions"] = supported_actions
        if can_set_usb_limit is not UNSET:
            field_dict["CanSetUSBLimit"] = can_set_usb_limit
        if usb_limit_min is not UNSET:
            field_dict["USBLimitMin"] = usb_limit_min
        if usb_limit_max is not UNSET:
            field_dict["USBLimitMax"] = usb_limit_max
        if connected is not UNSET:
            field_dict["Connected"] = connected
        if name is not UNSET:
            field_dict["Name"] = name
        if display_name is not UNSET:
            field_dict["DisplayName"] = display_name
        if device_id is not UNSET:
            field_dict["DeviceId"] = device_id

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.camera_info_response_binning_modes_item import CameraInfoResponseBinningModesItem

        d = src_dict.copy()
        target_temp = d.pop("TargetTemp", UNSET)

        at_target_temp = d.pop("AtTargetTemp", UNSET)

        can_set_temperature = d.pop("CanSetTemperature", UNSET)

        has_shutter = d.pop("HasShutter", UNSET)

        temperature = d.pop("Temperature", UNSET)

        gain = d.pop("Gain", UNSET)

        default_gain = d.pop("DefaultGain", UNSET)

        electrons_per_adu = d.pop("ElectronsPerADU", UNSET)

        bin_x = d.pop("BinX", UNSET)

        bit_depth = d.pop("BitDepth", UNSET)

        bin_y = d.pop("BinY", UNSET)

        can_set_offset = d.pop("CanSetOffset", UNSET)

        can_get_gain = d.pop("CanGetGain", UNSET)

        offset_min = d.pop("OffsetMin", UNSET)

        offset_max = d.pop("OffsetMax", UNSET)

        offset = d.pop("Offset", UNSET)

        default_offset = d.pop("DefaultOffset", UNSET)

        usb_limit = d.pop("USBLimit", UNSET)

        is_sub_sample_enabled = d.pop("IsSubSampleEnabled", UNSET)

        _camera_state = d.pop("CameraState", UNSET)
        camera_state: Union[Unset, CameraInfoResponseCameraState]
        if isinstance(_camera_state, Unset):
            camera_state = UNSET
        else:
            camera_state = CameraInfoResponseCameraState(_camera_state)

        x_size = d.pop("XSize", UNSET)

        y_size = d.pop("YSize", UNSET)

        pixel_size = d.pop("PixelSize", UNSET)

        battery = d.pop("Battery", UNSET)

        gain_min = d.pop("GainMin", UNSET)

        gain_max = d.pop("GainMax", UNSET)

        can_set_gain = d.pop("CanSetGain", UNSET)

        gains = cast(List[Any], d.pop("Gains", UNSET))

        cooler_on = d.pop("CoolerOn", UNSET)

        cooler_power = d.pop("CoolerPower", UNSET)

        has_dew_heater = d.pop("HasDewHeater", UNSET)

        dew_heater_on = d.pop("DewHeaterOn", UNSET)

        can_sub_sample = d.pop("CanSubSample", UNSET)

        sub_sample_x = d.pop("SubSampleX", UNSET)

        sub_sample_y = d.pop("SubSampleY", UNSET)

        sub_sample_width = d.pop("SubSampleWidth", UNSET)

        sub_sample_height = d.pop("SubSampleHeight", UNSET)

        temperature_set_point = d.pop("TemperatureSetPoint", UNSET)

        readout_modes = cast(List[str], d.pop("ReadoutModes", UNSET))

        readout_mode = d.pop("ReadoutMode", UNSET)

        readout_mode_for_snap_images = d.pop("ReadoutModeForSnapImages", UNSET)

        readout_mode_for_normal_images = d.pop("ReadoutModeForNormalImages", UNSET)

        is_exposing = d.pop("IsExposing", UNSET)

        exposure_end_time = d.pop("ExposureEndTime", UNSET)

        last_download_time = d.pop("LastDownloadTime", UNSET)

        _sensor_type = d.pop("SensorType", UNSET)
        sensor_type: Union[Unset, CameraInfoResponseSensorType]
        if isinstance(_sensor_type, Unset):
            sensor_type = UNSET
        else:
            sensor_type = CameraInfoResponseSensorType(_sensor_type)

        bayer_offset_x = d.pop("BayerOffsetX", UNSET)

        bayer_offset_y = d.pop("BayerOffsetY", UNSET)

        binning_modes = []
        _binning_modes = d.pop("BinningModes", UNSET)
        for binning_modes_item_data in _binning_modes or []:
            binning_modes_item = CameraInfoResponseBinningModesItem.from_dict(binning_modes_item_data)

            binning_modes.append(binning_modes_item)

        exposure_max = d.pop("ExposureMax", UNSET)

        exposure_min = d.pop("ExposureMin", UNSET)

        live_view_enabled = d.pop("LiveViewEnabled", UNSET)

        can_show_live_view = d.pop("CanShowLiveView", UNSET)

        supported_actions = cast(List[str], d.pop("SupportedActions", UNSET))

        can_set_usb_limit = d.pop("CanSetUSBLimit", UNSET)

        usb_limit_min = d.pop("USBLimitMin", UNSET)

        usb_limit_max = d.pop("USBLimitMax", UNSET)

        connected = d.pop("Connected", UNSET)

        name = d.pop("Name", UNSET)

        display_name = d.pop("DisplayName", UNSET)

        device_id = d.pop("DeviceId", UNSET)

        camera_info_response = cls(
            target_temp=target_temp,
            at_target_temp=at_target_temp,
            can_set_temperature=can_set_temperature,
            has_shutter=has_shutter,
            temperature=temperature,
            gain=gain,
            default_gain=default_gain,
            electrons_per_adu=electrons_per_adu,
            bin_x=bin_x,
            bit_depth=bit_depth,
            bin_y=bin_y,
            can_set_offset=can_set_offset,
            can_get_gain=can_get_gain,
            offset_min=offset_min,
            offset_max=offset_max,
            offset=offset,
            default_offset=default_offset,
            usb_limit=usb_limit,
            is_sub_sample_enabled=is_sub_sample_enabled,
            camera_state=camera_state,
            x_size=x_size,
            y_size=y_size,
            pixel_size=pixel_size,
            battery=battery,
            gain_min=gain_min,
            gain_max=gain_max,
            can_set_gain=can_set_gain,
            gains=gains,
            cooler_on=cooler_on,
            cooler_power=cooler_power,
            has_dew_heater=has_dew_heater,
            dew_heater_on=dew_heater_on,
            can_sub_sample=can_sub_sample,
            sub_sample_x=sub_sample_x,
            sub_sample_y=sub_sample_y,
            sub_sample_width=sub_sample_width,
            sub_sample_height=sub_sample_height,
            temperature_set_point=temperature_set_point,
            readout_modes=readout_modes,
            readout_mode=readout_mode,
            readout_mode_for_snap_images=readout_mode_for_snap_images,
            readout_mode_for_normal_images=readout_mode_for_normal_images,
            is_exposing=is_exposing,
            exposure_end_time=exposure_end_time,
            last_download_time=last_download_time,
            sensor_type=sensor_type,
            bayer_offset_x=bayer_offset_x,
            bayer_offset_y=bayer_offset_y,
            binning_modes=binning_modes,
            exposure_max=exposure_max,
            exposure_min=exposure_min,
            live_view_enabled=live_view_enabled,
            can_show_live_view=can_show_live_view,
            supported_actions=supported_actions,
            can_set_usb_limit=can_set_usb_limit,
            usb_limit_min=usb_limit_min,
            usb_limit_max=usb_limit_max,
            connected=connected,
            name=name,
            display_name=display_name,
            device_id=device_id,
        )

        camera_info_response.additional_properties = d
        return camera_info_response

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

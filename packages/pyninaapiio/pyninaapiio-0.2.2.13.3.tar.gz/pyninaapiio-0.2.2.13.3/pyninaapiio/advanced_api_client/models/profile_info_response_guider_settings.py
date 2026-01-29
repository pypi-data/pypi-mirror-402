from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_guider_settings_phd2_guider_scale import (
    ProfileInfoResponseGuiderSettingsPHD2GuiderScale,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.profile_info_response_guider_settings_guide_chart_declination_color import (
        ProfileInfoResponseGuiderSettingsGuideChartDeclinationColor,
    )
    from ..models.profile_info_response_guider_settings_guide_chart_right_ascension_color import (
        ProfileInfoResponseGuiderSettingsGuideChartRightAscensionColor,
    )


T = TypeVar("T", bound="ProfileInfoResponseGuiderSettings")


@_attrs_define
class ProfileInfoResponseGuiderSettings:
    """
    Attributes:
        guider_name (Union[Unset, str]):
        dither_pixels (Union[Unset, int]):
        dither_ra_only (Union[Unset, bool]):
        phd2_guider_scale (Union[Unset, ProfileInfoResponseGuiderSettingsPHD2GuiderScale]):
        max_y (Union[Unset, int]):
        phd2_history_size (Union[Unset, int]):
        phd2_server_port (Union[Unset, int]):
        phd2_server_url (Union[Unset, str]):
        phd2_instance_number (Union[Unset, int]):
        settle_time (Union[Unset, int]):
        settle_pixels (Union[Unset, float]):
        settle_timeout (Union[Unset, int]):
        phd2_path (Union[Unset, str]):
        auto_retry_start_guiding (Union[Unset, bool]):
        auto_retry_start_guiding_timeout_seconds (Union[Unset, int]):
        meta_guide_use_ip_address_any (Union[Unset, bool]):
        meta_guide_port (Union[Unset, int]):
        mgen_focal_length (Union[Unset, int]):
        mgen_pixel_margin (Union[Unset, int]):
        meta_guide_min_intensity (Union[Unset, int]):
        meta_guide_dither_settle_seconds (Union[Unset, int]):
        meta_guide_lock_when_guiding (Union[Unset, bool]):
        phd2roi_pct (Union[Unset, int]):
        sky_guard_server_port (Union[Unset, int]):
        sky_guard_server_url (Union[Unset, str]):
        sky_guard_path (Union[Unset, str]):
        sky_guard_callback_port (Union[Unset, int]):
        sky_guard_time_laps_checked (Union[Unset, bool]):
        sky_guard_value_max_guiding (Union[Unset, int]):
        sky_guard_time_laps_guiding (Union[Unset, int]):
        sky_guard_time_laps_dither_checked (Union[Unset, bool]):
        sky_guard_value_max_dithering (Union[Unset, int]):
        sky_guard_time_laps_dithering (Union[Unset, int]):
        sky_guard_time_out_guiding (Union[Unset, int]):
        guide_chart_right_ascension_color (Union[Unset,
            ProfileInfoResponseGuiderSettingsGuideChartRightAscensionColor]):
        guide_chart_declination_color (Union[Unset, ProfileInfoResponseGuiderSettingsGuideChartDeclinationColor]):
        guide_chart_show_corrections (Union[Unset, bool]):
    """

    guider_name: Union[Unset, str] = UNSET
    dither_pixels: Union[Unset, int] = UNSET
    dither_ra_only: Union[Unset, bool] = UNSET
    phd2_guider_scale: Union[Unset, ProfileInfoResponseGuiderSettingsPHD2GuiderScale] = UNSET
    max_y: Union[Unset, int] = UNSET
    phd2_history_size: Union[Unset, int] = UNSET
    phd2_server_port: Union[Unset, int] = UNSET
    phd2_server_url: Union[Unset, str] = UNSET
    phd2_instance_number: Union[Unset, int] = UNSET
    settle_time: Union[Unset, int] = UNSET
    settle_pixels: Union[Unset, float] = UNSET
    settle_timeout: Union[Unset, int] = UNSET
    phd2_path: Union[Unset, str] = UNSET
    auto_retry_start_guiding: Union[Unset, bool] = UNSET
    auto_retry_start_guiding_timeout_seconds: Union[Unset, int] = UNSET
    meta_guide_use_ip_address_any: Union[Unset, bool] = UNSET
    meta_guide_port: Union[Unset, int] = UNSET
    mgen_focal_length: Union[Unset, int] = UNSET
    mgen_pixel_margin: Union[Unset, int] = UNSET
    meta_guide_min_intensity: Union[Unset, int] = UNSET
    meta_guide_dither_settle_seconds: Union[Unset, int] = UNSET
    meta_guide_lock_when_guiding: Union[Unset, bool] = UNSET
    phd2roi_pct: Union[Unset, int] = UNSET
    sky_guard_server_port: Union[Unset, int] = UNSET
    sky_guard_server_url: Union[Unset, str] = UNSET
    sky_guard_path: Union[Unset, str] = UNSET
    sky_guard_callback_port: Union[Unset, int] = UNSET
    sky_guard_time_laps_checked: Union[Unset, bool] = UNSET
    sky_guard_value_max_guiding: Union[Unset, int] = UNSET
    sky_guard_time_laps_guiding: Union[Unset, int] = UNSET
    sky_guard_time_laps_dither_checked: Union[Unset, bool] = UNSET
    sky_guard_value_max_dithering: Union[Unset, int] = UNSET
    sky_guard_time_laps_dithering: Union[Unset, int] = UNSET
    sky_guard_time_out_guiding: Union[Unset, int] = UNSET
    guide_chart_right_ascension_color: Union[
        Unset, "ProfileInfoResponseGuiderSettingsGuideChartRightAscensionColor"
    ] = UNSET
    guide_chart_declination_color: Union[Unset, "ProfileInfoResponseGuiderSettingsGuideChartDeclinationColor"] = UNSET
    guide_chart_show_corrections: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        guider_name = self.guider_name

        dither_pixels = self.dither_pixels

        dither_ra_only = self.dither_ra_only

        phd2_guider_scale: Union[Unset, str] = UNSET
        if not isinstance(self.phd2_guider_scale, Unset):
            phd2_guider_scale = self.phd2_guider_scale.value

        max_y = self.max_y

        phd2_history_size = self.phd2_history_size

        phd2_server_port = self.phd2_server_port

        phd2_server_url = self.phd2_server_url

        phd2_instance_number = self.phd2_instance_number

        settle_time = self.settle_time

        settle_pixels = self.settle_pixels

        settle_timeout = self.settle_timeout

        phd2_path = self.phd2_path

        auto_retry_start_guiding = self.auto_retry_start_guiding

        auto_retry_start_guiding_timeout_seconds = self.auto_retry_start_guiding_timeout_seconds

        meta_guide_use_ip_address_any = self.meta_guide_use_ip_address_any

        meta_guide_port = self.meta_guide_port

        mgen_focal_length = self.mgen_focal_length

        mgen_pixel_margin = self.mgen_pixel_margin

        meta_guide_min_intensity = self.meta_guide_min_intensity

        meta_guide_dither_settle_seconds = self.meta_guide_dither_settle_seconds

        meta_guide_lock_when_guiding = self.meta_guide_lock_when_guiding

        phd2roi_pct = self.phd2roi_pct

        sky_guard_server_port = self.sky_guard_server_port

        sky_guard_server_url = self.sky_guard_server_url

        sky_guard_path = self.sky_guard_path

        sky_guard_callback_port = self.sky_guard_callback_port

        sky_guard_time_laps_checked = self.sky_guard_time_laps_checked

        sky_guard_value_max_guiding = self.sky_guard_value_max_guiding

        sky_guard_time_laps_guiding = self.sky_guard_time_laps_guiding

        sky_guard_time_laps_dither_checked = self.sky_guard_time_laps_dither_checked

        sky_guard_value_max_dithering = self.sky_guard_value_max_dithering

        sky_guard_time_laps_dithering = self.sky_guard_time_laps_dithering

        sky_guard_time_out_guiding = self.sky_guard_time_out_guiding

        guide_chart_right_ascension_color: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.guide_chart_right_ascension_color, Unset):
            guide_chart_right_ascension_color = self.guide_chart_right_ascension_color.to_dict()

        guide_chart_declination_color: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.guide_chart_declination_color, Unset):
            guide_chart_declination_color = self.guide_chart_declination_color.to_dict()

        guide_chart_show_corrections = self.guide_chart_show_corrections

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if guider_name is not UNSET:
            field_dict["GuiderName"] = guider_name
        if dither_pixels is not UNSET:
            field_dict["DitherPixels"] = dither_pixels
        if dither_ra_only is not UNSET:
            field_dict["DitherRAOnly"] = dither_ra_only
        if phd2_guider_scale is not UNSET:
            field_dict["PHD2GuiderScale"] = phd2_guider_scale
        if max_y is not UNSET:
            field_dict["MaxY"] = max_y
        if phd2_history_size is not UNSET:
            field_dict["PHD2HistorySize"] = phd2_history_size
        if phd2_server_port is not UNSET:
            field_dict["PHD2ServerPort"] = phd2_server_port
        if phd2_server_url is not UNSET:
            field_dict["PHD2ServerUrl"] = phd2_server_url
        if phd2_instance_number is not UNSET:
            field_dict["PHD2InstanceNumber"] = phd2_instance_number
        if settle_time is not UNSET:
            field_dict["SettleTime"] = settle_time
        if settle_pixels is not UNSET:
            field_dict["SettlePixels"] = settle_pixels
        if settle_timeout is not UNSET:
            field_dict["SettleTimeout"] = settle_timeout
        if phd2_path is not UNSET:
            field_dict["PHD2Path"] = phd2_path
        if auto_retry_start_guiding is not UNSET:
            field_dict["AutoRetryStartGuiding"] = auto_retry_start_guiding
        if auto_retry_start_guiding_timeout_seconds is not UNSET:
            field_dict["AutoRetryStartGuidingTimeoutSeconds"] = auto_retry_start_guiding_timeout_seconds
        if meta_guide_use_ip_address_any is not UNSET:
            field_dict["MetaGuideUseIpAddressAny"] = meta_guide_use_ip_address_any
        if meta_guide_port is not UNSET:
            field_dict["MetaGuidePort"] = meta_guide_port
        if mgen_focal_length is not UNSET:
            field_dict["MGENFocalLength"] = mgen_focal_length
        if mgen_pixel_margin is not UNSET:
            field_dict["MGENPixelMargin"] = mgen_pixel_margin
        if meta_guide_min_intensity is not UNSET:
            field_dict["MetaGuideMinIntensity"] = meta_guide_min_intensity
        if meta_guide_dither_settle_seconds is not UNSET:
            field_dict["MetaGuideDitherSettleSeconds"] = meta_guide_dither_settle_seconds
        if meta_guide_lock_when_guiding is not UNSET:
            field_dict["MetaGuideLockWhenGuiding"] = meta_guide_lock_when_guiding
        if phd2roi_pct is not UNSET:
            field_dict["PHD2ROIPct"] = phd2roi_pct
        if sky_guard_server_port is not UNSET:
            field_dict["SkyGuardServerPort"] = sky_guard_server_port
        if sky_guard_server_url is not UNSET:
            field_dict["SkyGuardServerUrl"] = sky_guard_server_url
        if sky_guard_path is not UNSET:
            field_dict["SkyGuardPath"] = sky_guard_path
        if sky_guard_callback_port is not UNSET:
            field_dict["SkyGuardCallbackPort"] = sky_guard_callback_port
        if sky_guard_time_laps_checked is not UNSET:
            field_dict["SkyGuardTimeLapsChecked"] = sky_guard_time_laps_checked
        if sky_guard_value_max_guiding is not UNSET:
            field_dict["SkyGuardValueMaxGuiding"] = sky_guard_value_max_guiding
        if sky_guard_time_laps_guiding is not UNSET:
            field_dict["SkyGuardTimeLapsGuiding"] = sky_guard_time_laps_guiding
        if sky_guard_time_laps_dither_checked is not UNSET:
            field_dict["SkyGuardTimeLapsDitherChecked"] = sky_guard_time_laps_dither_checked
        if sky_guard_value_max_dithering is not UNSET:
            field_dict["SkyGuardValueMaxDithering"] = sky_guard_value_max_dithering
        if sky_guard_time_laps_dithering is not UNSET:
            field_dict["SkyGuardTimeLapsDithering"] = sky_guard_time_laps_dithering
        if sky_guard_time_out_guiding is not UNSET:
            field_dict["SkyGuardTimeOutGuiding"] = sky_guard_time_out_guiding
        if guide_chart_right_ascension_color is not UNSET:
            field_dict["GuideChartRightAscensionColor"] = guide_chart_right_ascension_color
        if guide_chart_declination_color is not UNSET:
            field_dict["GuideChartDeclinationColor"] = guide_chart_declination_color
        if guide_chart_show_corrections is not UNSET:
            field_dict["GuideChartShowCorrections"] = guide_chart_show_corrections

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.profile_info_response_guider_settings_guide_chart_declination_color import (
            ProfileInfoResponseGuiderSettingsGuideChartDeclinationColor,
        )
        from ..models.profile_info_response_guider_settings_guide_chart_right_ascension_color import (
            ProfileInfoResponseGuiderSettingsGuideChartRightAscensionColor,
        )

        d = src_dict.copy()
        guider_name = d.pop("GuiderName", UNSET)

        dither_pixels = d.pop("DitherPixels", UNSET)

        dither_ra_only = d.pop("DitherRAOnly", UNSET)

        _phd2_guider_scale = d.pop("PHD2GuiderScale", UNSET)
        phd2_guider_scale: Union[Unset, ProfileInfoResponseGuiderSettingsPHD2GuiderScale]
        if isinstance(_phd2_guider_scale, Unset):
            phd2_guider_scale = UNSET
        else:
            phd2_guider_scale = ProfileInfoResponseGuiderSettingsPHD2GuiderScale(_phd2_guider_scale)

        max_y = d.pop("MaxY", UNSET)

        phd2_history_size = d.pop("PHD2HistorySize", UNSET)

        phd2_server_port = d.pop("PHD2ServerPort", UNSET)

        phd2_server_url = d.pop("PHD2ServerUrl", UNSET)

        phd2_instance_number = d.pop("PHD2InstanceNumber", UNSET)

        settle_time = d.pop("SettleTime", UNSET)

        settle_pixels = d.pop("SettlePixels", UNSET)

        settle_timeout = d.pop("SettleTimeout", UNSET)

        phd2_path = d.pop("PHD2Path", UNSET)

        auto_retry_start_guiding = d.pop("AutoRetryStartGuiding", UNSET)

        auto_retry_start_guiding_timeout_seconds = d.pop("AutoRetryStartGuidingTimeoutSeconds", UNSET)

        meta_guide_use_ip_address_any = d.pop("MetaGuideUseIpAddressAny", UNSET)

        meta_guide_port = d.pop("MetaGuidePort", UNSET)

        mgen_focal_length = d.pop("MGENFocalLength", UNSET)

        mgen_pixel_margin = d.pop("MGENPixelMargin", UNSET)

        meta_guide_min_intensity = d.pop("MetaGuideMinIntensity", UNSET)

        meta_guide_dither_settle_seconds = d.pop("MetaGuideDitherSettleSeconds", UNSET)

        meta_guide_lock_when_guiding = d.pop("MetaGuideLockWhenGuiding", UNSET)

        phd2roi_pct = d.pop("PHD2ROIPct", UNSET)

        sky_guard_server_port = d.pop("SkyGuardServerPort", UNSET)

        sky_guard_server_url = d.pop("SkyGuardServerUrl", UNSET)

        sky_guard_path = d.pop("SkyGuardPath", UNSET)

        sky_guard_callback_port = d.pop("SkyGuardCallbackPort", UNSET)

        sky_guard_time_laps_checked = d.pop("SkyGuardTimeLapsChecked", UNSET)

        sky_guard_value_max_guiding = d.pop("SkyGuardValueMaxGuiding", UNSET)

        sky_guard_time_laps_guiding = d.pop("SkyGuardTimeLapsGuiding", UNSET)

        sky_guard_time_laps_dither_checked = d.pop("SkyGuardTimeLapsDitherChecked", UNSET)

        sky_guard_value_max_dithering = d.pop("SkyGuardValueMaxDithering", UNSET)

        sky_guard_time_laps_dithering = d.pop("SkyGuardTimeLapsDithering", UNSET)

        sky_guard_time_out_guiding = d.pop("SkyGuardTimeOutGuiding", UNSET)

        _guide_chart_right_ascension_color = d.pop("GuideChartRightAscensionColor", UNSET)
        guide_chart_right_ascension_color: Union[Unset, ProfileInfoResponseGuiderSettingsGuideChartRightAscensionColor]
        if isinstance(_guide_chart_right_ascension_color, Unset):
            guide_chart_right_ascension_color = UNSET
        else:
            guide_chart_right_ascension_color = (
                ProfileInfoResponseGuiderSettingsGuideChartRightAscensionColor.from_dict(
                    _guide_chart_right_ascension_color
                )
            )

        _guide_chart_declination_color = d.pop("GuideChartDeclinationColor", UNSET)
        guide_chart_declination_color: Union[Unset, ProfileInfoResponseGuiderSettingsGuideChartDeclinationColor]
        if isinstance(_guide_chart_declination_color, Unset):
            guide_chart_declination_color = UNSET
        else:
            guide_chart_declination_color = ProfileInfoResponseGuiderSettingsGuideChartDeclinationColor.from_dict(
                _guide_chart_declination_color
            )

        guide_chart_show_corrections = d.pop("GuideChartShowCorrections", UNSET)

        profile_info_response_guider_settings = cls(
            guider_name=guider_name,
            dither_pixels=dither_pixels,
            dither_ra_only=dither_ra_only,
            phd2_guider_scale=phd2_guider_scale,
            max_y=max_y,
            phd2_history_size=phd2_history_size,
            phd2_server_port=phd2_server_port,
            phd2_server_url=phd2_server_url,
            phd2_instance_number=phd2_instance_number,
            settle_time=settle_time,
            settle_pixels=settle_pixels,
            settle_timeout=settle_timeout,
            phd2_path=phd2_path,
            auto_retry_start_guiding=auto_retry_start_guiding,
            auto_retry_start_guiding_timeout_seconds=auto_retry_start_guiding_timeout_seconds,
            meta_guide_use_ip_address_any=meta_guide_use_ip_address_any,
            meta_guide_port=meta_guide_port,
            mgen_focal_length=mgen_focal_length,
            mgen_pixel_margin=mgen_pixel_margin,
            meta_guide_min_intensity=meta_guide_min_intensity,
            meta_guide_dither_settle_seconds=meta_guide_dither_settle_seconds,
            meta_guide_lock_when_guiding=meta_guide_lock_when_guiding,
            phd2roi_pct=phd2roi_pct,
            sky_guard_server_port=sky_guard_server_port,
            sky_guard_server_url=sky_guard_server_url,
            sky_guard_path=sky_guard_path,
            sky_guard_callback_port=sky_guard_callback_port,
            sky_guard_time_laps_checked=sky_guard_time_laps_checked,
            sky_guard_value_max_guiding=sky_guard_value_max_guiding,
            sky_guard_time_laps_guiding=sky_guard_time_laps_guiding,
            sky_guard_time_laps_dither_checked=sky_guard_time_laps_dither_checked,
            sky_guard_value_max_dithering=sky_guard_value_max_dithering,
            sky_guard_time_laps_dithering=sky_guard_time_laps_dithering,
            sky_guard_time_out_guiding=sky_guard_time_out_guiding,
            guide_chart_right_ascension_color=guide_chart_right_ascension_color,
            guide_chart_declination_color=guide_chart_declination_color,
            guide_chart_show_corrections=guide_chart_show_corrections,
        )

        profile_info_response_guider_settings.additional_properties = d
        return profile_info_response_guider_settings

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

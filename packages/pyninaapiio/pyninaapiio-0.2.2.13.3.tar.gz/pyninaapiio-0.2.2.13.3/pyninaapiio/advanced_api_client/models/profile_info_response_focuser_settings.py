from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_focuser_settings_auto_focus_curve_fitting import (
    ProfileInfoResponseFocuserSettingsAutoFocusCurveFitting,
)
from ..models.profile_info_response_focuser_settings_auto_focus_method import (
    ProfileInfoResponseFocuserSettingsAutoFocusMethod,
)
from ..models.profile_info_response_focuser_settings_backlash_compensation_model import (
    ProfileInfoResponseFocuserSettingsBacklashCompensationModel,
)
from ..models.profile_info_response_focuser_settings_contrast_detection_method import (
    ProfileInfoResponseFocuserSettingsContrastDetectionMethod,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseFocuserSettings")


@_attrs_define
class ProfileInfoResponseFocuserSettings:
    """
    Attributes:
        auto_focus_exposure_time (Union[Unset, int]):
        auto_focus_initial_offset_steps (Union[Unset, int]):
        auto_focus_step_size (Union[Unset, int]):
        id (Union[Unset, str]):
        use_filter_wheel_offsets (Union[Unset, bool]):
        auto_focus_disable_guiding (Union[Unset, bool]):
        focuser_settle_time (Union[Unset, int]):
        auto_focus_total_number_of_attempts (Union[Unset, int]):
        auto_focus_number_of_frames_per_point (Union[Unset, int]):
        auto_focus_inner_crop_ratio (Union[Unset, int]):
        auto_focus_outer_crop_ratio (Union[Unset, int]):
        auto_focus_use_brightest_stars (Union[Unset, int]):
        backlash_in (Union[Unset, int]):
        backlash_out (Union[Unset, int]):
        auto_focus_binning (Union[Unset, int]):
        auto_focus_curve_fitting (Union[Unset, ProfileInfoResponseFocuserSettingsAutoFocusCurveFitting]):
        auto_focus_method (Union[Unset, ProfileInfoResponseFocuserSettingsAutoFocusMethod]):
        contrast_detection_method (Union[Unset, ProfileInfoResponseFocuserSettingsContrastDetectionMethod]):
        backlash_compensation_model (Union[Unset, ProfileInfoResponseFocuserSettingsBacklashCompensationModel]):
        auto_focus_timeout_seconds (Union[Unset, int]):
        r_squared_threshold (Union[Unset, float]):
    """

    auto_focus_exposure_time: Union[Unset, int] = UNSET
    auto_focus_initial_offset_steps: Union[Unset, int] = UNSET
    auto_focus_step_size: Union[Unset, int] = UNSET
    id: Union[Unset, str] = UNSET
    use_filter_wheel_offsets: Union[Unset, bool] = UNSET
    auto_focus_disable_guiding: Union[Unset, bool] = UNSET
    focuser_settle_time: Union[Unset, int] = UNSET
    auto_focus_total_number_of_attempts: Union[Unset, int] = UNSET
    auto_focus_number_of_frames_per_point: Union[Unset, int] = UNSET
    auto_focus_inner_crop_ratio: Union[Unset, int] = UNSET
    auto_focus_outer_crop_ratio: Union[Unset, int] = UNSET
    auto_focus_use_brightest_stars: Union[Unset, int] = UNSET
    backlash_in: Union[Unset, int] = UNSET
    backlash_out: Union[Unset, int] = UNSET
    auto_focus_binning: Union[Unset, int] = UNSET
    auto_focus_curve_fitting: Union[Unset, ProfileInfoResponseFocuserSettingsAutoFocusCurveFitting] = UNSET
    auto_focus_method: Union[Unset, ProfileInfoResponseFocuserSettingsAutoFocusMethod] = UNSET
    contrast_detection_method: Union[Unset, ProfileInfoResponseFocuserSettingsContrastDetectionMethod] = UNSET
    backlash_compensation_model: Union[Unset, ProfileInfoResponseFocuserSettingsBacklashCompensationModel] = UNSET
    auto_focus_timeout_seconds: Union[Unset, int] = UNSET
    r_squared_threshold: Union[Unset, float] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        auto_focus_exposure_time = self.auto_focus_exposure_time

        auto_focus_initial_offset_steps = self.auto_focus_initial_offset_steps

        auto_focus_step_size = self.auto_focus_step_size

        id = self.id

        use_filter_wheel_offsets = self.use_filter_wheel_offsets

        auto_focus_disable_guiding = self.auto_focus_disable_guiding

        focuser_settle_time = self.focuser_settle_time

        auto_focus_total_number_of_attempts = self.auto_focus_total_number_of_attempts

        auto_focus_number_of_frames_per_point = self.auto_focus_number_of_frames_per_point

        auto_focus_inner_crop_ratio = self.auto_focus_inner_crop_ratio

        auto_focus_outer_crop_ratio = self.auto_focus_outer_crop_ratio

        auto_focus_use_brightest_stars = self.auto_focus_use_brightest_stars

        backlash_in = self.backlash_in

        backlash_out = self.backlash_out

        auto_focus_binning = self.auto_focus_binning

        auto_focus_curve_fitting: Union[Unset, str] = UNSET
        if not isinstance(self.auto_focus_curve_fitting, Unset):
            auto_focus_curve_fitting = self.auto_focus_curve_fitting.value

        auto_focus_method: Union[Unset, str] = UNSET
        if not isinstance(self.auto_focus_method, Unset):
            auto_focus_method = self.auto_focus_method.value

        contrast_detection_method: Union[Unset, str] = UNSET
        if not isinstance(self.contrast_detection_method, Unset):
            contrast_detection_method = self.contrast_detection_method.value

        backlash_compensation_model: Union[Unset, str] = UNSET
        if not isinstance(self.backlash_compensation_model, Unset):
            backlash_compensation_model = self.backlash_compensation_model.value

        auto_focus_timeout_seconds = self.auto_focus_timeout_seconds

        r_squared_threshold = self.r_squared_threshold

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if auto_focus_exposure_time is not UNSET:
            field_dict["AutoFocusExposureTime"] = auto_focus_exposure_time
        if auto_focus_initial_offset_steps is not UNSET:
            field_dict["AutoFocusInitialOffsetSteps"] = auto_focus_initial_offset_steps
        if auto_focus_step_size is not UNSET:
            field_dict["AutoFocusStepSize"] = auto_focus_step_size
        if id is not UNSET:
            field_dict["Id"] = id
        if use_filter_wheel_offsets is not UNSET:
            field_dict["UseFilterWheelOffsets"] = use_filter_wheel_offsets
        if auto_focus_disable_guiding is not UNSET:
            field_dict["AutoFocusDisableGuiding"] = auto_focus_disable_guiding
        if focuser_settle_time is not UNSET:
            field_dict["FocuserSettleTime"] = focuser_settle_time
        if auto_focus_total_number_of_attempts is not UNSET:
            field_dict["AutoFocusTotalNumberOfAttempts"] = auto_focus_total_number_of_attempts
        if auto_focus_number_of_frames_per_point is not UNSET:
            field_dict["AutoFocusNumberOfFramesPerPoint"] = auto_focus_number_of_frames_per_point
        if auto_focus_inner_crop_ratio is not UNSET:
            field_dict["AutoFocusInnerCropRatio"] = auto_focus_inner_crop_ratio
        if auto_focus_outer_crop_ratio is not UNSET:
            field_dict["AutoFocusOuterCropRatio"] = auto_focus_outer_crop_ratio
        if auto_focus_use_brightest_stars is not UNSET:
            field_dict["AutoFocusUseBrightestStars"] = auto_focus_use_brightest_stars
        if backlash_in is not UNSET:
            field_dict["BacklashIn"] = backlash_in
        if backlash_out is not UNSET:
            field_dict["BacklashOut"] = backlash_out
        if auto_focus_binning is not UNSET:
            field_dict["AutoFocusBinning"] = auto_focus_binning
        if auto_focus_curve_fitting is not UNSET:
            field_dict["AutoFocusCurveFitting"] = auto_focus_curve_fitting
        if auto_focus_method is not UNSET:
            field_dict["AutoFocusMethod"] = auto_focus_method
        if contrast_detection_method is not UNSET:
            field_dict["ContrastDetectionMethod"] = contrast_detection_method
        if backlash_compensation_model is not UNSET:
            field_dict["BacklashCompensationModel"] = backlash_compensation_model
        if auto_focus_timeout_seconds is not UNSET:
            field_dict["AutoFocusTimeoutSeconds"] = auto_focus_timeout_seconds
        if r_squared_threshold is not UNSET:
            field_dict["RSquaredThreshold"] = r_squared_threshold

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        auto_focus_exposure_time = d.pop("AutoFocusExposureTime", UNSET)

        auto_focus_initial_offset_steps = d.pop("AutoFocusInitialOffsetSteps", UNSET)

        auto_focus_step_size = d.pop("AutoFocusStepSize", UNSET)

        id = d.pop("Id", UNSET)

        use_filter_wheel_offsets = d.pop("UseFilterWheelOffsets", UNSET)

        auto_focus_disable_guiding = d.pop("AutoFocusDisableGuiding", UNSET)

        focuser_settle_time = d.pop("FocuserSettleTime", UNSET)

        auto_focus_total_number_of_attempts = d.pop("AutoFocusTotalNumberOfAttempts", UNSET)

        auto_focus_number_of_frames_per_point = d.pop("AutoFocusNumberOfFramesPerPoint", UNSET)

        auto_focus_inner_crop_ratio = d.pop("AutoFocusInnerCropRatio", UNSET)

        auto_focus_outer_crop_ratio = d.pop("AutoFocusOuterCropRatio", UNSET)

        auto_focus_use_brightest_stars = d.pop("AutoFocusUseBrightestStars", UNSET)

        backlash_in = d.pop("BacklashIn", UNSET)

        backlash_out = d.pop("BacklashOut", UNSET)

        auto_focus_binning = d.pop("AutoFocusBinning", UNSET)

        _auto_focus_curve_fitting = d.pop("AutoFocusCurveFitting", UNSET)
        auto_focus_curve_fitting: Union[Unset, ProfileInfoResponseFocuserSettingsAutoFocusCurveFitting]
        if isinstance(_auto_focus_curve_fitting, Unset):
            auto_focus_curve_fitting = UNSET
        else:
            auto_focus_curve_fitting = ProfileInfoResponseFocuserSettingsAutoFocusCurveFitting(
                _auto_focus_curve_fitting
            )

        _auto_focus_method = d.pop("AutoFocusMethod", UNSET)
        auto_focus_method: Union[Unset, ProfileInfoResponseFocuserSettingsAutoFocusMethod]
        if isinstance(_auto_focus_method, Unset):
            auto_focus_method = UNSET
        else:
            auto_focus_method = ProfileInfoResponseFocuserSettingsAutoFocusMethod(_auto_focus_method)

        _contrast_detection_method = d.pop("ContrastDetectionMethod", UNSET)
        contrast_detection_method: Union[Unset, ProfileInfoResponseFocuserSettingsContrastDetectionMethod]
        if isinstance(_contrast_detection_method, Unset):
            contrast_detection_method = UNSET
        else:
            contrast_detection_method = ProfileInfoResponseFocuserSettingsContrastDetectionMethod(
                _contrast_detection_method
            )

        _backlash_compensation_model = d.pop("BacklashCompensationModel", UNSET)
        backlash_compensation_model: Union[Unset, ProfileInfoResponseFocuserSettingsBacklashCompensationModel]
        if isinstance(_backlash_compensation_model, Unset):
            backlash_compensation_model = UNSET
        else:
            backlash_compensation_model = ProfileInfoResponseFocuserSettingsBacklashCompensationModel(
                _backlash_compensation_model
            )

        auto_focus_timeout_seconds = d.pop("AutoFocusTimeoutSeconds", UNSET)

        r_squared_threshold = d.pop("RSquaredThreshold", UNSET)

        profile_info_response_focuser_settings = cls(
            auto_focus_exposure_time=auto_focus_exposure_time,
            auto_focus_initial_offset_steps=auto_focus_initial_offset_steps,
            auto_focus_step_size=auto_focus_step_size,
            id=id,
            use_filter_wheel_offsets=use_filter_wheel_offsets,
            auto_focus_disable_guiding=auto_focus_disable_guiding,
            focuser_settle_time=focuser_settle_time,
            auto_focus_total_number_of_attempts=auto_focus_total_number_of_attempts,
            auto_focus_number_of_frames_per_point=auto_focus_number_of_frames_per_point,
            auto_focus_inner_crop_ratio=auto_focus_inner_crop_ratio,
            auto_focus_outer_crop_ratio=auto_focus_outer_crop_ratio,
            auto_focus_use_brightest_stars=auto_focus_use_brightest_stars,
            backlash_in=backlash_in,
            backlash_out=backlash_out,
            auto_focus_binning=auto_focus_binning,
            auto_focus_curve_fitting=auto_focus_curve_fitting,
            auto_focus_method=auto_focus_method,
            contrast_detection_method=contrast_detection_method,
            backlash_compensation_model=backlash_compensation_model,
            auto_focus_timeout_seconds=auto_focus_timeout_seconds,
            r_squared_threshold=r_squared_threshold,
        )

        profile_info_response_focuser_settings.additional_properties = d
        return profile_info_response_focuser_settings

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

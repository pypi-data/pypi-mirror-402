from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.profile_info_response_alpaca_settings import ProfileInfoResponseAlpacaSettings
    from ..models.profile_info_response_application_settings import ProfileInfoResponseApplicationSettings
    from ..models.profile_info_response_astrometry_settings import ProfileInfoResponseAstrometrySettings
    from ..models.profile_info_response_camera_settings import ProfileInfoResponseCameraSettings
    from ..models.profile_info_response_color_schema_settings import ProfileInfoResponseColorSchemaSettings
    from ..models.profile_info_response_dome_settings import ProfileInfoResponseDomeSettings
    from ..models.profile_info_response_filter_wheel_settings import ProfileInfoResponseFilterWheelSettings
    from ..models.profile_info_response_flat_device_settings import ProfileInfoResponseFlatDeviceSettings
    from ..models.profile_info_response_flat_wizard_settings import ProfileInfoResponseFlatWizardSettings
    from ..models.profile_info_response_focuser_settings import ProfileInfoResponseFocuserSettings
    from ..models.profile_info_response_framing_assistant_settings import ProfileInfoResponseFramingAssistantSettings
    from ..models.profile_info_response_guider_settings import ProfileInfoResponseGuiderSettings
    from ..models.profile_info_response_image_file_settings import ProfileInfoResponseImageFileSettings
    from ..models.profile_info_response_image_history_settings import ProfileInfoResponseImageHistorySettings
    from ..models.profile_info_response_image_settings import ProfileInfoResponseImageSettings
    from ..models.profile_info_response_meridian_flip_settings import ProfileInfoResponseMeridianFlipSettings
    from ..models.profile_info_response_planetarium_settings import ProfileInfoResponsePlanetariumSettings
    from ..models.profile_info_response_plate_solve_settings import ProfileInfoResponsePlateSolveSettings
    from ..models.profile_info_response_rotator_settings import ProfileInfoResponseRotatorSettings
    from ..models.profile_info_response_safety_monitor_settings import ProfileInfoResponseSafetyMonitorSettings
    from ..models.profile_info_response_sequence_settings import ProfileInfoResponseSequenceSettings
    from ..models.profile_info_response_snap_shot_control_settings import ProfileInfoResponseSnapShotControlSettings
    from ..models.profile_info_response_switch_settings import ProfileInfoResponseSwitchSettings
    from ..models.profile_info_response_telescope_settings import ProfileInfoResponseTelescopeSettings
    from ..models.profile_info_response_weather_data_settings import ProfileInfoResponseWeatherDataSettings


T = TypeVar("T", bound="ProfileInfoResponse")


@_attrs_define
class ProfileInfoResponse:
    """
    Attributes:
        name (Union[Unset, str]):
        description (Union[Unset, str]):
        id (Union[Unset, str]):
        last_used (Union[Unset, str]):
        application_settings (Union[Unset, ProfileInfoResponseApplicationSettings]):
        astrometry_settings (Union[Unset, ProfileInfoResponseAstrometrySettings]):
        camera_settings (Union[Unset, ProfileInfoResponseCameraSettings]):
        color_schema_settings (Union[Unset, ProfileInfoResponseColorSchemaSettings]):
        dome_settings (Union[Unset, ProfileInfoResponseDomeSettings]):
        filter_wheel_settings (Union[Unset, ProfileInfoResponseFilterWheelSettings]):
        flat_wizard_settings (Union[Unset, ProfileInfoResponseFlatWizardSettings]):
        focuser_settings (Union[Unset, ProfileInfoResponseFocuserSettings]):
        framing_assistant_settings (Union[Unset, ProfileInfoResponseFramingAssistantSettings]):
        guider_settings (Union[Unset, ProfileInfoResponseGuiderSettings]):
        image_file_settings (Union[Unset, ProfileInfoResponseImageFileSettings]):
        image_settings (Union[Unset, ProfileInfoResponseImageSettings]):
        meridian_flip_settings (Union[Unset, ProfileInfoResponseMeridianFlipSettings]):
        planetarium_settings (Union[Unset, ProfileInfoResponsePlanetariumSettings]):
        plate_solve_settings (Union[Unset, ProfileInfoResponsePlateSolveSettings]):
        rotator_settings (Union[Unset, ProfileInfoResponseRotatorSettings]):
        flat_device_settings (Union[Unset, ProfileInfoResponseFlatDeviceSettings]):
        sequence_settings (Union[Unset, ProfileInfoResponseSequenceSettings]):
        switch_settings (Union[Unset, ProfileInfoResponseSwitchSettings]):
        telescope_settings (Union[Unset, ProfileInfoResponseTelescopeSettings]):
        weather_data_settings (Union[Unset, ProfileInfoResponseWeatherDataSettings]):
        snap_shot_control_settings (Union[Unset, ProfileInfoResponseSnapShotControlSettings]):
        safety_monitor_settings (Union[Unset, ProfileInfoResponseSafetyMonitorSettings]):
        alpaca_settings (Union[Unset, ProfileInfoResponseAlpacaSettings]):
        image_history_settings (Union[Unset, ProfileInfoResponseImageHistorySettings]):
    """

    name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    id: Union[Unset, str] = UNSET
    last_used: Union[Unset, str] = UNSET
    application_settings: Union[Unset, "ProfileInfoResponseApplicationSettings"] = UNSET
    astrometry_settings: Union[Unset, "ProfileInfoResponseAstrometrySettings"] = UNSET
    camera_settings: Union[Unset, "ProfileInfoResponseCameraSettings"] = UNSET
    color_schema_settings: Union[Unset, "ProfileInfoResponseColorSchemaSettings"] = UNSET
    dome_settings: Union[Unset, "ProfileInfoResponseDomeSettings"] = UNSET
    filter_wheel_settings: Union[Unset, "ProfileInfoResponseFilterWheelSettings"] = UNSET
    flat_wizard_settings: Union[Unset, "ProfileInfoResponseFlatWizardSettings"] = UNSET
    focuser_settings: Union[Unset, "ProfileInfoResponseFocuserSettings"] = UNSET
    framing_assistant_settings: Union[Unset, "ProfileInfoResponseFramingAssistantSettings"] = UNSET
    guider_settings: Union[Unset, "ProfileInfoResponseGuiderSettings"] = UNSET
    image_file_settings: Union[Unset, "ProfileInfoResponseImageFileSettings"] = UNSET
    image_settings: Union[Unset, "ProfileInfoResponseImageSettings"] = UNSET
    meridian_flip_settings: Union[Unset, "ProfileInfoResponseMeridianFlipSettings"] = UNSET
    planetarium_settings: Union[Unset, "ProfileInfoResponsePlanetariumSettings"] = UNSET
    plate_solve_settings: Union[Unset, "ProfileInfoResponsePlateSolveSettings"] = UNSET
    rotator_settings: Union[Unset, "ProfileInfoResponseRotatorSettings"] = UNSET
    flat_device_settings: Union[Unset, "ProfileInfoResponseFlatDeviceSettings"] = UNSET
    sequence_settings: Union[Unset, "ProfileInfoResponseSequenceSettings"] = UNSET
    switch_settings: Union[Unset, "ProfileInfoResponseSwitchSettings"] = UNSET
    telescope_settings: Union[Unset, "ProfileInfoResponseTelescopeSettings"] = UNSET
    weather_data_settings: Union[Unset, "ProfileInfoResponseWeatherDataSettings"] = UNSET
    snap_shot_control_settings: Union[Unset, "ProfileInfoResponseSnapShotControlSettings"] = UNSET
    safety_monitor_settings: Union[Unset, "ProfileInfoResponseSafetyMonitorSettings"] = UNSET
    alpaca_settings: Union[Unset, "ProfileInfoResponseAlpacaSettings"] = UNSET
    image_history_settings: Union[Unset, "ProfileInfoResponseImageHistorySettings"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        description = self.description

        id = self.id

        last_used = self.last_used

        application_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.application_settings, Unset):
            application_settings = self.application_settings.to_dict()

        astrometry_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.astrometry_settings, Unset):
            astrometry_settings = self.astrometry_settings.to_dict()

        camera_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.camera_settings, Unset):
            camera_settings = self.camera_settings.to_dict()

        color_schema_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.color_schema_settings, Unset):
            color_schema_settings = self.color_schema_settings.to_dict()

        dome_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.dome_settings, Unset):
            dome_settings = self.dome_settings.to_dict()

        filter_wheel_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.filter_wheel_settings, Unset):
            filter_wheel_settings = self.filter_wheel_settings.to_dict()

        flat_wizard_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.flat_wizard_settings, Unset):
            flat_wizard_settings = self.flat_wizard_settings.to_dict()

        focuser_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.focuser_settings, Unset):
            focuser_settings = self.focuser_settings.to_dict()

        framing_assistant_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.framing_assistant_settings, Unset):
            framing_assistant_settings = self.framing_assistant_settings.to_dict()

        guider_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.guider_settings, Unset):
            guider_settings = self.guider_settings.to_dict()

        image_file_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.image_file_settings, Unset):
            image_file_settings = self.image_file_settings.to_dict()

        image_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.image_settings, Unset):
            image_settings = self.image_settings.to_dict()

        meridian_flip_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.meridian_flip_settings, Unset):
            meridian_flip_settings = self.meridian_flip_settings.to_dict()

        planetarium_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.planetarium_settings, Unset):
            planetarium_settings = self.planetarium_settings.to_dict()

        plate_solve_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.plate_solve_settings, Unset):
            plate_solve_settings = self.plate_solve_settings.to_dict()

        rotator_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.rotator_settings, Unset):
            rotator_settings = self.rotator_settings.to_dict()

        flat_device_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.flat_device_settings, Unset):
            flat_device_settings = self.flat_device_settings.to_dict()

        sequence_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.sequence_settings, Unset):
            sequence_settings = self.sequence_settings.to_dict()

        switch_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.switch_settings, Unset):
            switch_settings = self.switch_settings.to_dict()

        telescope_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.telescope_settings, Unset):
            telescope_settings = self.telescope_settings.to_dict()

        weather_data_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.weather_data_settings, Unset):
            weather_data_settings = self.weather_data_settings.to_dict()

        snap_shot_control_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.snap_shot_control_settings, Unset):
            snap_shot_control_settings = self.snap_shot_control_settings.to_dict()

        safety_monitor_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.safety_monitor_settings, Unset):
            safety_monitor_settings = self.safety_monitor_settings.to_dict()

        alpaca_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.alpaca_settings, Unset):
            alpaca_settings = self.alpaca_settings.to_dict()

        image_history_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.image_history_settings, Unset):
            image_history_settings = self.image_history_settings.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["Name"] = name
        if description is not UNSET:
            field_dict["Description"] = description
        if id is not UNSET:
            field_dict["Id"] = id
        if last_used is not UNSET:
            field_dict["LastUsed"] = last_used
        if application_settings is not UNSET:
            field_dict["ApplicationSettings"] = application_settings
        if astrometry_settings is not UNSET:
            field_dict["AstrometrySettings"] = astrometry_settings
        if camera_settings is not UNSET:
            field_dict["CameraSettings"] = camera_settings
        if color_schema_settings is not UNSET:
            field_dict["ColorSchemaSettings"] = color_schema_settings
        if dome_settings is not UNSET:
            field_dict["DomeSettings"] = dome_settings
        if filter_wheel_settings is not UNSET:
            field_dict["FilterWheelSettings"] = filter_wheel_settings
        if flat_wizard_settings is not UNSET:
            field_dict["FlatWizardSettings"] = flat_wizard_settings
        if focuser_settings is not UNSET:
            field_dict["FocuserSettings"] = focuser_settings
        if framing_assistant_settings is not UNSET:
            field_dict["FramingAssistantSettings"] = framing_assistant_settings
        if guider_settings is not UNSET:
            field_dict["GuiderSettings"] = guider_settings
        if image_file_settings is not UNSET:
            field_dict["ImageFileSettings"] = image_file_settings
        if image_settings is not UNSET:
            field_dict["ImageSettings"] = image_settings
        if meridian_flip_settings is not UNSET:
            field_dict["MeridianFlipSettings"] = meridian_flip_settings
        if planetarium_settings is not UNSET:
            field_dict["PlanetariumSettings"] = planetarium_settings
        if plate_solve_settings is not UNSET:
            field_dict["PlateSolveSettings"] = plate_solve_settings
        if rotator_settings is not UNSET:
            field_dict["RotatorSettings"] = rotator_settings
        if flat_device_settings is not UNSET:
            field_dict["FlatDeviceSettings"] = flat_device_settings
        if sequence_settings is not UNSET:
            field_dict["SequenceSettings"] = sequence_settings
        if switch_settings is not UNSET:
            field_dict["SwitchSettings"] = switch_settings
        if telescope_settings is not UNSET:
            field_dict["TelescopeSettings"] = telescope_settings
        if weather_data_settings is not UNSET:
            field_dict["WeatherDataSettings"] = weather_data_settings
        if snap_shot_control_settings is not UNSET:
            field_dict["SnapShotControlSettings"] = snap_shot_control_settings
        if safety_monitor_settings is not UNSET:
            field_dict["SafetyMonitorSettings"] = safety_monitor_settings
        if alpaca_settings is not UNSET:
            field_dict["AlpacaSettings"] = alpaca_settings
        if image_history_settings is not UNSET:
            field_dict["ImageHistorySettings"] = image_history_settings

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.profile_info_response_alpaca_settings import ProfileInfoResponseAlpacaSettings
        from ..models.profile_info_response_application_settings import ProfileInfoResponseApplicationSettings
        from ..models.profile_info_response_astrometry_settings import ProfileInfoResponseAstrometrySettings
        from ..models.profile_info_response_camera_settings import ProfileInfoResponseCameraSettings
        from ..models.profile_info_response_color_schema_settings import ProfileInfoResponseColorSchemaSettings
        from ..models.profile_info_response_dome_settings import ProfileInfoResponseDomeSettings
        from ..models.profile_info_response_filter_wheel_settings import ProfileInfoResponseFilterWheelSettings
        from ..models.profile_info_response_flat_device_settings import ProfileInfoResponseFlatDeviceSettings
        from ..models.profile_info_response_flat_wizard_settings import ProfileInfoResponseFlatWizardSettings
        from ..models.profile_info_response_focuser_settings import ProfileInfoResponseFocuserSettings
        from ..models.profile_info_response_framing_assistant_settings import (
            ProfileInfoResponseFramingAssistantSettings,
        )
        from ..models.profile_info_response_guider_settings import ProfileInfoResponseGuiderSettings
        from ..models.profile_info_response_image_file_settings import ProfileInfoResponseImageFileSettings
        from ..models.profile_info_response_image_history_settings import ProfileInfoResponseImageHistorySettings
        from ..models.profile_info_response_image_settings import ProfileInfoResponseImageSettings
        from ..models.profile_info_response_meridian_flip_settings import ProfileInfoResponseMeridianFlipSettings
        from ..models.profile_info_response_planetarium_settings import ProfileInfoResponsePlanetariumSettings
        from ..models.profile_info_response_plate_solve_settings import ProfileInfoResponsePlateSolveSettings
        from ..models.profile_info_response_rotator_settings import ProfileInfoResponseRotatorSettings
        from ..models.profile_info_response_safety_monitor_settings import ProfileInfoResponseSafetyMonitorSettings
        from ..models.profile_info_response_sequence_settings import ProfileInfoResponseSequenceSettings
        from ..models.profile_info_response_snap_shot_control_settings import ProfileInfoResponseSnapShotControlSettings
        from ..models.profile_info_response_switch_settings import ProfileInfoResponseSwitchSettings
        from ..models.profile_info_response_telescope_settings import ProfileInfoResponseTelescopeSettings
        from ..models.profile_info_response_weather_data_settings import ProfileInfoResponseWeatherDataSettings

        d = src_dict.copy()
        name = d.pop("Name", UNSET)

        description = d.pop("Description", UNSET)

        id = d.pop("Id", UNSET)

        last_used = d.pop("LastUsed", UNSET)

        _application_settings = d.pop("ApplicationSettings", UNSET)
        application_settings: Union[Unset, ProfileInfoResponseApplicationSettings]
        if isinstance(_application_settings, Unset):
            application_settings = UNSET
        else:
            application_settings = ProfileInfoResponseApplicationSettings.from_dict(_application_settings)

        _astrometry_settings = d.pop("AstrometrySettings", UNSET)
        astrometry_settings: Union[Unset, ProfileInfoResponseAstrometrySettings]
        if isinstance(_astrometry_settings, Unset):
            astrometry_settings = UNSET
        else:
            astrometry_settings = ProfileInfoResponseAstrometrySettings.from_dict(_astrometry_settings)

        _camera_settings = d.pop("CameraSettings", UNSET)
        camera_settings: Union[Unset, ProfileInfoResponseCameraSettings]
        if isinstance(_camera_settings, Unset):
            camera_settings = UNSET
        else:
            camera_settings = ProfileInfoResponseCameraSettings.from_dict(_camera_settings)

        _color_schema_settings = d.pop("ColorSchemaSettings", UNSET)
        color_schema_settings: Union[Unset, ProfileInfoResponseColorSchemaSettings]
        if isinstance(_color_schema_settings, Unset):
            color_schema_settings = UNSET
        else:
            color_schema_settings = ProfileInfoResponseColorSchemaSettings.from_dict(_color_schema_settings)

        _dome_settings = d.pop("DomeSettings", UNSET)
        dome_settings: Union[Unset, ProfileInfoResponseDomeSettings]
        if isinstance(_dome_settings, Unset):
            dome_settings = UNSET
        else:
            dome_settings = ProfileInfoResponseDomeSettings.from_dict(_dome_settings)

        _filter_wheel_settings = d.pop("FilterWheelSettings", UNSET)
        filter_wheel_settings: Union[Unset, ProfileInfoResponseFilterWheelSettings]
        if isinstance(_filter_wheel_settings, Unset):
            filter_wheel_settings = UNSET
        else:
            filter_wheel_settings = ProfileInfoResponseFilterWheelSettings.from_dict(_filter_wheel_settings)

        _flat_wizard_settings = d.pop("FlatWizardSettings", UNSET)
        flat_wizard_settings: Union[Unset, ProfileInfoResponseFlatWizardSettings]
        if isinstance(_flat_wizard_settings, Unset):
            flat_wizard_settings = UNSET
        else:
            flat_wizard_settings = ProfileInfoResponseFlatWizardSettings.from_dict(_flat_wizard_settings)

        _focuser_settings = d.pop("FocuserSettings", UNSET)
        focuser_settings: Union[Unset, ProfileInfoResponseFocuserSettings]
        if isinstance(_focuser_settings, Unset):
            focuser_settings = UNSET
        else:
            focuser_settings = ProfileInfoResponseFocuserSettings.from_dict(_focuser_settings)

        _framing_assistant_settings = d.pop("FramingAssistantSettings", UNSET)
        framing_assistant_settings: Union[Unset, ProfileInfoResponseFramingAssistantSettings]
        if isinstance(_framing_assistant_settings, Unset):
            framing_assistant_settings = UNSET
        else:
            framing_assistant_settings = ProfileInfoResponseFramingAssistantSettings.from_dict(
                _framing_assistant_settings
            )

        _guider_settings = d.pop("GuiderSettings", UNSET)
        guider_settings: Union[Unset, ProfileInfoResponseGuiderSettings]
        if isinstance(_guider_settings, Unset):
            guider_settings = UNSET
        else:
            guider_settings = ProfileInfoResponseGuiderSettings.from_dict(_guider_settings)

        _image_file_settings = d.pop("ImageFileSettings", UNSET)
        image_file_settings: Union[Unset, ProfileInfoResponseImageFileSettings]
        if isinstance(_image_file_settings, Unset):
            image_file_settings = UNSET
        else:
            image_file_settings = ProfileInfoResponseImageFileSettings.from_dict(_image_file_settings)

        _image_settings = d.pop("ImageSettings", UNSET)
        image_settings: Union[Unset, ProfileInfoResponseImageSettings]
        if isinstance(_image_settings, Unset):
            image_settings = UNSET
        else:
            image_settings = ProfileInfoResponseImageSettings.from_dict(_image_settings)

        _meridian_flip_settings = d.pop("MeridianFlipSettings", UNSET)
        meridian_flip_settings: Union[Unset, ProfileInfoResponseMeridianFlipSettings]
        if isinstance(_meridian_flip_settings, Unset):
            meridian_flip_settings = UNSET
        else:
            meridian_flip_settings = ProfileInfoResponseMeridianFlipSettings.from_dict(_meridian_flip_settings)

        _planetarium_settings = d.pop("PlanetariumSettings", UNSET)
        planetarium_settings: Union[Unset, ProfileInfoResponsePlanetariumSettings]
        if isinstance(_planetarium_settings, Unset):
            planetarium_settings = UNSET
        else:
            planetarium_settings = ProfileInfoResponsePlanetariumSettings.from_dict(_planetarium_settings)

        _plate_solve_settings = d.pop("PlateSolveSettings", UNSET)
        plate_solve_settings: Union[Unset, ProfileInfoResponsePlateSolveSettings]
        if isinstance(_plate_solve_settings, Unset):
            plate_solve_settings = UNSET
        else:
            plate_solve_settings = ProfileInfoResponsePlateSolveSettings.from_dict(_plate_solve_settings)

        _rotator_settings = d.pop("RotatorSettings", UNSET)
        rotator_settings: Union[Unset, ProfileInfoResponseRotatorSettings]
        if isinstance(_rotator_settings, Unset):
            rotator_settings = UNSET
        else:
            rotator_settings = ProfileInfoResponseRotatorSettings.from_dict(_rotator_settings)

        _flat_device_settings = d.pop("FlatDeviceSettings", UNSET)
        flat_device_settings: Union[Unset, ProfileInfoResponseFlatDeviceSettings]
        if isinstance(_flat_device_settings, Unset):
            flat_device_settings = UNSET
        else:
            flat_device_settings = ProfileInfoResponseFlatDeviceSettings.from_dict(_flat_device_settings)

        _sequence_settings = d.pop("SequenceSettings", UNSET)
        sequence_settings: Union[Unset, ProfileInfoResponseSequenceSettings]
        if isinstance(_sequence_settings, Unset):
            sequence_settings = UNSET
        else:
            sequence_settings = ProfileInfoResponseSequenceSettings.from_dict(_sequence_settings)

        _switch_settings = d.pop("SwitchSettings", UNSET)
        switch_settings: Union[Unset, ProfileInfoResponseSwitchSettings]
        if isinstance(_switch_settings, Unset):
            switch_settings = UNSET
        else:
            switch_settings = ProfileInfoResponseSwitchSettings.from_dict(_switch_settings)

        _telescope_settings = d.pop("TelescopeSettings", UNSET)
        telescope_settings: Union[Unset, ProfileInfoResponseTelescopeSettings]
        if isinstance(_telescope_settings, Unset):
            telescope_settings = UNSET
        else:
            telescope_settings = ProfileInfoResponseTelescopeSettings.from_dict(_telescope_settings)

        _weather_data_settings = d.pop("WeatherDataSettings", UNSET)
        weather_data_settings: Union[Unset, ProfileInfoResponseWeatherDataSettings]
        if isinstance(_weather_data_settings, Unset):
            weather_data_settings = UNSET
        else:
            weather_data_settings = ProfileInfoResponseWeatherDataSettings.from_dict(_weather_data_settings)

        _snap_shot_control_settings = d.pop("SnapShotControlSettings", UNSET)
        snap_shot_control_settings: Union[Unset, ProfileInfoResponseSnapShotControlSettings]
        if isinstance(_snap_shot_control_settings, Unset):
            snap_shot_control_settings = UNSET
        else:
            snap_shot_control_settings = ProfileInfoResponseSnapShotControlSettings.from_dict(
                _snap_shot_control_settings
            )

        _safety_monitor_settings = d.pop("SafetyMonitorSettings", UNSET)
        safety_monitor_settings: Union[Unset, ProfileInfoResponseSafetyMonitorSettings]
        if isinstance(_safety_monitor_settings, Unset):
            safety_monitor_settings = UNSET
        else:
            safety_monitor_settings = ProfileInfoResponseSafetyMonitorSettings.from_dict(_safety_monitor_settings)

        _alpaca_settings = d.pop("AlpacaSettings", UNSET)
        alpaca_settings: Union[Unset, ProfileInfoResponseAlpacaSettings]
        if isinstance(_alpaca_settings, Unset):
            alpaca_settings = UNSET
        else:
            alpaca_settings = ProfileInfoResponseAlpacaSettings.from_dict(_alpaca_settings)

        _image_history_settings = d.pop("ImageHistorySettings", UNSET)
        image_history_settings: Union[Unset, ProfileInfoResponseImageHistorySettings]
        if isinstance(_image_history_settings, Unset):
            image_history_settings = UNSET
        else:
            image_history_settings = ProfileInfoResponseImageHistorySettings.from_dict(_image_history_settings)

        profile_info_response = cls(
            name=name,
            description=description,
            id=id,
            last_used=last_used,
            application_settings=application_settings,
            astrometry_settings=astrometry_settings,
            camera_settings=camera_settings,
            color_schema_settings=color_schema_settings,
            dome_settings=dome_settings,
            filter_wheel_settings=filter_wheel_settings,
            flat_wizard_settings=flat_wizard_settings,
            focuser_settings=focuser_settings,
            framing_assistant_settings=framing_assistant_settings,
            guider_settings=guider_settings,
            image_file_settings=image_file_settings,
            image_settings=image_settings,
            meridian_flip_settings=meridian_flip_settings,
            planetarium_settings=planetarium_settings,
            plate_solve_settings=plate_solve_settings,
            rotator_settings=rotator_settings,
            flat_device_settings=flat_device_settings,
            sequence_settings=sequence_settings,
            switch_settings=switch_settings,
            telescope_settings=telescope_settings,
            weather_data_settings=weather_data_settings,
            snap_shot_control_settings=snap_shot_control_settings,
            safety_monitor_settings=safety_monitor_settings,
            alpaca_settings=alpaca_settings,
            image_history_settings=image_history_settings,
        )

        profile_info_response.additional_properties = d
        return profile_info_response

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

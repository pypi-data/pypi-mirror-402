from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_framing_assistant_settings_last_selected_image_source import (
    ProfileInfoResponseFramingAssistantSettingsLastSelectedImageSource,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseFramingAssistantSettings")


@_attrs_define
class ProfileInfoResponseFramingAssistantSettings:
    """
    Attributes:
        camera_height (Union[Unset, int]):
        camera_width (Union[Unset, int]):
        field_of_view (Union[Unset, int]):
        opacity (Union[Unset, float]):
        last_selected_image_source (Union[Unset, ProfileInfoResponseFramingAssistantSettingsLastSelectedImageSource]):
        last_rotation_angle (Union[Unset, int]):
        save_image_in_offline_cache (Union[Unset, bool]):
    """

    camera_height: Union[Unset, int] = UNSET
    camera_width: Union[Unset, int] = UNSET
    field_of_view: Union[Unset, int] = UNSET
    opacity: Union[Unset, float] = UNSET
    last_selected_image_source: Union[Unset, ProfileInfoResponseFramingAssistantSettingsLastSelectedImageSource] = UNSET
    last_rotation_angle: Union[Unset, int] = UNSET
    save_image_in_offline_cache: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        camera_height = self.camera_height

        camera_width = self.camera_width

        field_of_view = self.field_of_view

        opacity = self.opacity

        last_selected_image_source: Union[Unset, str] = UNSET
        if not isinstance(self.last_selected_image_source, Unset):
            last_selected_image_source = self.last_selected_image_source.value

        last_rotation_angle = self.last_rotation_angle

        save_image_in_offline_cache = self.save_image_in_offline_cache

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if camera_height is not UNSET:
            field_dict["CameraHeight"] = camera_height
        if camera_width is not UNSET:
            field_dict["CameraWidth"] = camera_width
        if field_of_view is not UNSET:
            field_dict["FieldOfView"] = field_of_view
        if opacity is not UNSET:
            field_dict["Opacity"] = opacity
        if last_selected_image_source is not UNSET:
            field_dict["LastSelectedImageSource"] = last_selected_image_source
        if last_rotation_angle is not UNSET:
            field_dict["LastRotationAngle"] = last_rotation_angle
        if save_image_in_offline_cache is not UNSET:
            field_dict["SaveImageInOfflineCache"] = save_image_in_offline_cache

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        camera_height = d.pop("CameraHeight", UNSET)

        camera_width = d.pop("CameraWidth", UNSET)

        field_of_view = d.pop("FieldOfView", UNSET)

        opacity = d.pop("Opacity", UNSET)

        _last_selected_image_source = d.pop("LastSelectedImageSource", UNSET)
        last_selected_image_source: Union[Unset, ProfileInfoResponseFramingAssistantSettingsLastSelectedImageSource]
        if isinstance(_last_selected_image_source, Unset):
            last_selected_image_source = UNSET
        else:
            last_selected_image_source = ProfileInfoResponseFramingAssistantSettingsLastSelectedImageSource(
                _last_selected_image_source
            )

        last_rotation_angle = d.pop("LastRotationAngle", UNSET)

        save_image_in_offline_cache = d.pop("SaveImageInOfflineCache", UNSET)

        profile_info_response_framing_assistant_settings = cls(
            camera_height=camera_height,
            camera_width=camera_width,
            field_of_view=field_of_view,
            opacity=opacity,
            last_selected_image_source=last_selected_image_source,
            last_rotation_angle=last_rotation_angle,
            save_image_in_offline_cache=save_image_in_offline_cache,
        )

        profile_info_response_framing_assistant_settings.additional_properties = d
        return profile_info_response_framing_assistant_settings

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

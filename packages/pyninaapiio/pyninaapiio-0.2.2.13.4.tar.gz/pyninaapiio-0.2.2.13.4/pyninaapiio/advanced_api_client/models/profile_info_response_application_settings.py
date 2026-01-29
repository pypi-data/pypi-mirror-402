from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_application_settings_log_level import ProfileInfoResponseApplicationSettingsLogLevel
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseApplicationSettings")


@_attrs_define
class ProfileInfoResponseApplicationSettings:
    """
    Attributes:
        culture (Union[Unset, str]):
        device_polling_interval (Union[Unset, int]):
        page_size (Union[Unset, int]):
        log_level (Union[Unset, ProfileInfoResponseApplicationSettingsLogLevel]):
    """

    culture: Union[Unset, str] = UNSET
    device_polling_interval: Union[Unset, int] = UNSET
    page_size: Union[Unset, int] = UNSET
    log_level: Union[Unset, ProfileInfoResponseApplicationSettingsLogLevel] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        culture = self.culture

        device_polling_interval = self.device_polling_interval

        page_size = self.page_size

        log_level: Union[Unset, str] = UNSET
        if not isinstance(self.log_level, Unset):
            log_level = self.log_level.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if culture is not UNSET:
            field_dict["Culture"] = culture
        if device_polling_interval is not UNSET:
            field_dict["DevicePollingInterval"] = device_polling_interval
        if page_size is not UNSET:
            field_dict["PageSize"] = page_size
        if log_level is not UNSET:
            field_dict["LogLevel"] = log_level

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        culture = d.pop("Culture", UNSET)

        device_polling_interval = d.pop("DevicePollingInterval", UNSET)

        page_size = d.pop("PageSize", UNSET)

        _log_level = d.pop("LogLevel", UNSET)
        log_level: Union[Unset, ProfileInfoResponseApplicationSettingsLogLevel]
        if isinstance(_log_level, Unset):
            log_level = UNSET
        else:
            log_level = ProfileInfoResponseApplicationSettingsLogLevel(_log_level)

        profile_info_response_application_settings = cls(
            culture=culture,
            device_polling_interval=device_polling_interval,
            page_size=page_size,
            log_level=log_level,
        )

        profile_info_response_application_settings.additional_properties = d
        return profile_info_response_application_settings

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

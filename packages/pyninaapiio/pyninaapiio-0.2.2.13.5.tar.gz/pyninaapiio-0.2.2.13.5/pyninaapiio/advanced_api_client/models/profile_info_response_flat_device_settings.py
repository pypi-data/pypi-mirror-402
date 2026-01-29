from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseFlatDeviceSettings")


@_attrs_define
class ProfileInfoResponseFlatDeviceSettings:
    """
    Attributes:
        id (Union[Unset, str]):
        port_name (Union[Unset, str]):
        settle_time (Union[Unset, int]):
        trained_flat_exposure_settings (Union[Unset, List[Any]]):
    """

    id: Union[Unset, str] = UNSET
    port_name: Union[Unset, str] = UNSET
    settle_time: Union[Unset, int] = UNSET
    trained_flat_exposure_settings: Union[Unset, List[Any]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        port_name = self.port_name

        settle_time = self.settle_time

        trained_flat_exposure_settings: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.trained_flat_exposure_settings, Unset):
            trained_flat_exposure_settings = self.trained_flat_exposure_settings

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["Id"] = id
        if port_name is not UNSET:
            field_dict["PortName"] = port_name
        if settle_time is not UNSET:
            field_dict["SettleTime"] = settle_time
        if trained_flat_exposure_settings is not UNSET:
            field_dict["TrainedFlatExposureSettings"] = trained_flat_exposure_settings

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("Id", UNSET)

        port_name = d.pop("PortName", UNSET)

        settle_time = d.pop("SettleTime", UNSET)

        trained_flat_exposure_settings = cast(List[Any], d.pop("TrainedFlatExposureSettings", UNSET))

        profile_info_response_flat_device_settings = cls(
            id=id,
            port_name=port_name,
            settle_time=settle_time,
            trained_flat_exposure_settings=trained_flat_exposure_settings,
        )

        profile_info_response_flat_device_settings.additional_properties = d
        return profile_info_response_flat_device_settings

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

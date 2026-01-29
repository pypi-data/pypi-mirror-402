from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item import (
        ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItem,
    )


T = TypeVar("T", bound="ProfileInfoResponseFilterWheelSettings")


@_attrs_define
class ProfileInfoResponseFilterWheelSettings:
    """
    Attributes:
        filter_wheel_filters (Union[Unset, List['ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItem']]):
        id (Union[Unset, str]):
        disable_guiding_on_filter_change (Union[Unset, bool]):
        unidirectional (Union[Unset, bool]):
    """

    filter_wheel_filters: Union[Unset, List["ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItem"]] = UNSET
    id: Union[Unset, str] = UNSET
    disable_guiding_on_filter_change: Union[Unset, bool] = UNSET
    unidirectional: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        filter_wheel_filters: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.filter_wheel_filters, Unset):
            filter_wheel_filters = []
            for filter_wheel_filters_item_data in self.filter_wheel_filters:
                filter_wheel_filters_item = filter_wheel_filters_item_data.to_dict()
                filter_wheel_filters.append(filter_wheel_filters_item)

        id = self.id

        disable_guiding_on_filter_change = self.disable_guiding_on_filter_change

        unidirectional = self.unidirectional

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if filter_wheel_filters is not UNSET:
            field_dict["FilterWheelFilters"] = filter_wheel_filters
        if id is not UNSET:
            field_dict["Id"] = id
        if disable_guiding_on_filter_change is not UNSET:
            field_dict["DisableGuidingOnFilterChange"] = disable_guiding_on_filter_change
        if unidirectional is not UNSET:
            field_dict["Unidirectional"] = unidirectional

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.profile_info_response_filter_wheel_settings_filter_wheel_filters_item import (
            ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItem,
        )

        d = src_dict.copy()
        filter_wheel_filters = []
        _filter_wheel_filters = d.pop("FilterWheelFilters", UNSET)
        for filter_wheel_filters_item_data in _filter_wheel_filters or []:
            filter_wheel_filters_item = ProfileInfoResponseFilterWheelSettingsFilterWheelFiltersItem.from_dict(
                filter_wheel_filters_item_data
            )

            filter_wheel_filters.append(filter_wheel_filters_item)

        id = d.pop("Id", UNSET)

        disable_guiding_on_filter_change = d.pop("DisableGuidingOnFilterChange", UNSET)

        unidirectional = d.pop("Unidirectional", UNSET)

        profile_info_response_filter_wheel_settings = cls(
            filter_wheel_filters=filter_wheel_filters,
            id=id,
            disable_guiding_on_filter_change=disable_guiding_on_filter_change,
            unidirectional=unidirectional,
        )

        profile_info_response_filter_wheel_settings.additional_properties = d
        return profile_info_response_filter_wheel_settings

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

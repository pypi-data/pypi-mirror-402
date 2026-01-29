from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetEquipmentMountDisconnectResponse200")


@_attrs_define
class GetEquipmentMountDisconnectResponse200:
    """
    Attributes:
        response (Union[Unset, str]):  Example: Disconnected.
        error (Union[Unset, str]):
        status_code (Union[Unset, int]):  Example: 200.
        success (Union[Unset, bool]):  Example: True.
        type (Union[Unset, str]):  Example: API.
    """

    response: Union[Unset, str] = UNSET
    error: Union[Unset, str] = UNSET
    status_code: Union[Unset, int] = UNSET
    success: Union[Unset, bool] = UNSET
    type: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        response = self.response

        error = self.error

        status_code = self.status_code

        success = self.success

        type = self.type

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if response is not UNSET:
            field_dict["Response"] = response
        if error is not UNSET:
            field_dict["Error"] = error
        if status_code is not UNSET:
            field_dict["StatusCode"] = status_code
        if success is not UNSET:
            field_dict["Success"] = success
        if type is not UNSET:
            field_dict["Type"] = type

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        response = d.pop("Response", UNSET)

        error = d.pop("Error", UNSET)

        status_code = d.pop("StatusCode", UNSET)

        success = d.pop("Success", UNSET)

        type = d.pop("Type", UNSET)

        get_equipment_mount_disconnect_response_200 = cls(
            response=response,
            error=error,
            status_code=status_code,
            success=success,
            type=type,
        )

        get_equipment_mount_disconnect_response_200.additional_properties = d
        return get_equipment_mount_disconnect_response_200

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

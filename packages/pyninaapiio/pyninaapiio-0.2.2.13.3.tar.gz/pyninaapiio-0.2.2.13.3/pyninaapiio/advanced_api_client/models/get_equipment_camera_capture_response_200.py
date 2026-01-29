from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_equipment_camera_capture_response_200_response_type_0 import (
    GetEquipmentCameraCaptureResponse200ResponseType0,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_equipment_camera_capture_response_200_response_type_1 import (
        GetEquipmentCameraCaptureResponse200ResponseType1,
    )


T = TypeVar("T", bound="GetEquipmentCameraCaptureResponse200")


@_attrs_define
class GetEquipmentCameraCaptureResponse200:
    """
    Attributes:
        response (Union['GetEquipmentCameraCaptureResponse200ResponseType1',
            GetEquipmentCameraCaptureResponse200ResponseType0, Unset]):
        error (Union[Unset, str]):
        status_code (Union[Unset, int]):  Example: 200.
        success (Union[Unset, bool]):  Example: True.
        type (Union[Unset, str]):  Example: API.
    """

    response: Union[
        "GetEquipmentCameraCaptureResponse200ResponseType1", GetEquipmentCameraCaptureResponse200ResponseType0, Unset
    ] = UNSET
    error: Union[Unset, str] = UNSET
    status_code: Union[Unset, int] = UNSET
    success: Union[Unset, bool] = UNSET
    type: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        response: Union[Dict[str, Any], Unset, str]
        if isinstance(self.response, Unset):
            response = UNSET
        elif isinstance(self.response, GetEquipmentCameraCaptureResponse200ResponseType0):
            response = self.response.value
        else:
            response = self.response.to_dict()

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
        from ..models.get_equipment_camera_capture_response_200_response_type_1 import (
            GetEquipmentCameraCaptureResponse200ResponseType1,
        )

        d = src_dict.copy()

        def _parse_response(
            data: object,
        ) -> Union[
            "GetEquipmentCameraCaptureResponse200ResponseType1",
            GetEquipmentCameraCaptureResponse200ResponseType0,
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                response_type_0 = GetEquipmentCameraCaptureResponse200ResponseType0(data)

                return response_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_type_1 = GetEquipmentCameraCaptureResponse200ResponseType1.from_dict(data)

            return response_type_1

        response = _parse_response(d.pop("Response", UNSET))

        error = d.pop("Error", UNSET)

        status_code = d.pop("StatusCode", UNSET)

        success = d.pop("Success", UNSET)

        type = d.pop("Type", UNSET)

        get_equipment_camera_capture_response_200 = cls(
            response=response,
            error=error,
            status_code=status_code,
            success=success,
            type=type,
        )

        get_equipment_camera_capture_response_200.additional_properties = d
        return get_equipment_camera_capture_response_200

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

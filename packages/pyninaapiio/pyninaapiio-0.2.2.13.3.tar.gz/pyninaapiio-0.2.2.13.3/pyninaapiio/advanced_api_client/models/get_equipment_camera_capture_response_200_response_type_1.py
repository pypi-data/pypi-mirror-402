from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_equipment_camera_capture_response_200_response_type_1_plate_solve_result import (
        GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResult,
    )


T = TypeVar("T", bound="GetEquipmentCameraCaptureResponse200ResponseType1")


@_attrs_define
class GetEquipmentCameraCaptureResponse200ResponseType1:
    """
    Attributes:
        image (str): The base64 encoded image Example: <base64 encoded image>.
        plate_solve_result (Union[Unset, GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResult]):
    """

    image: str
    plate_solve_result: Union[Unset, "GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResult"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        image = self.image

        plate_solve_result: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.plate_solve_result, Unset):
            plate_solve_result = self.plate_solve_result.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Image": image,
            }
        )
        if plate_solve_result is not UNSET:
            field_dict["PlateSolveResult"] = plate_solve_result

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_equipment_camera_capture_response_200_response_type_1_plate_solve_result import (
            GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResult,
        )

        d = src_dict.copy()
        image = d.pop("Image")

        _plate_solve_result = d.pop("PlateSolveResult", UNSET)
        plate_solve_result: Union[Unset, GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResult]
        if isinstance(_plate_solve_result, Unset):
            plate_solve_result = UNSET
        else:
            plate_solve_result = GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResult.from_dict(
                _plate_solve_result
            )

        get_equipment_camera_capture_response_200_response_type_1 = cls(
            image=image,
            plate_solve_result=plate_solve_result,
        )

        get_equipment_camera_capture_response_200_response_type_1.additional_properties = d
        return get_equipment_camera_capture_response_200_response_type_1

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

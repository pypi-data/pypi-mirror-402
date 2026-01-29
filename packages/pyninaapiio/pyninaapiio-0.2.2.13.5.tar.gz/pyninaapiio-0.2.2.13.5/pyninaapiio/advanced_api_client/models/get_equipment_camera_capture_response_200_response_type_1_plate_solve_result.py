from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_equipment_camera_capture_response_200_response_type_1_plate_solve_result_coordinates import (
        GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResultCoordinates,
    )


T = TypeVar("T", bound="GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResult")


@_attrs_define
class GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResult:
    """
    Attributes:
        coordinates (Union[Unset, GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResultCoordinates]):
        position_angle (Union[Unset, float]):
        pixel_scale (Union[Unset, float]):
        radius (Union[Unset, float]):
        flipped (Union[Unset, bool]):
        success (Union[Unset, bool]):
        ra_error_string (Union[Unset, str]):
        ra_pix_error (Union[Unset, float]):
        dec_pix_error (Union[Unset, float]):
        dec_error_string (Union[Unset, str]):
    """

    coordinates: Union[Unset, "GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResultCoordinates"] = UNSET
    position_angle: Union[Unset, float] = UNSET
    pixel_scale: Union[Unset, float] = UNSET
    radius: Union[Unset, float] = UNSET
    flipped: Union[Unset, bool] = UNSET
    success: Union[Unset, bool] = UNSET
    ra_error_string: Union[Unset, str] = UNSET
    ra_pix_error: Union[Unset, float] = UNSET
    dec_pix_error: Union[Unset, float] = UNSET
    dec_error_string: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        coordinates: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.coordinates, Unset):
            coordinates = self.coordinates.to_dict()

        position_angle = self.position_angle

        pixel_scale = self.pixel_scale

        radius = self.radius

        flipped = self.flipped

        success = self.success

        ra_error_string = self.ra_error_string

        ra_pix_error = self.ra_pix_error

        dec_pix_error = self.dec_pix_error

        dec_error_string = self.dec_error_string

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if coordinates is not UNSET:
            field_dict["Coordinates"] = coordinates
        if position_angle is not UNSET:
            field_dict["PositionAngle"] = position_angle
        if pixel_scale is not UNSET:
            field_dict["PixelScale"] = pixel_scale
        if radius is not UNSET:
            field_dict["Radius"] = radius
        if flipped is not UNSET:
            field_dict["Flipped"] = flipped
        if success is not UNSET:
            field_dict["Success"] = success
        if ra_error_string is not UNSET:
            field_dict["RaErrorString"] = ra_error_string
        if ra_pix_error is not UNSET:
            field_dict["RaPixError"] = ra_pix_error
        if dec_pix_error is not UNSET:
            field_dict["DecPixError"] = dec_pix_error
        if dec_error_string is not UNSET:
            field_dict["DecErrorString"] = dec_error_string

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_equipment_camera_capture_response_200_response_type_1_plate_solve_result_coordinates import (
            GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResultCoordinates,
        )

        d = src_dict.copy()
        _coordinates = d.pop("Coordinates", UNSET)
        coordinates: Union[Unset, GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResultCoordinates]
        if isinstance(_coordinates, Unset):
            coordinates = UNSET
        else:
            coordinates = GetEquipmentCameraCaptureResponse200ResponseType1PlateSolveResultCoordinates.from_dict(
                _coordinates
            )

        position_angle = d.pop("PositionAngle", UNSET)

        pixel_scale = d.pop("PixelScale", UNSET)

        radius = d.pop("Radius", UNSET)

        flipped = d.pop("Flipped", UNSET)

        success = d.pop("Success", UNSET)

        ra_error_string = d.pop("RaErrorString", UNSET)

        ra_pix_error = d.pop("RaPixError", UNSET)

        dec_pix_error = d.pop("DecPixError", UNSET)

        dec_error_string = d.pop("DecErrorString", UNSET)

        get_equipment_camera_capture_response_200_response_type_1_plate_solve_result = cls(
            coordinates=coordinates,
            position_angle=position_angle,
            pixel_scale=pixel_scale,
            radius=radius,
            flipped=flipped,
            success=success,
            ra_error_string=ra_error_string,
            ra_pix_error=ra_pix_error,
            dec_pix_error=dec_pix_error,
            dec_error_string=dec_error_string,
        )

        get_equipment_camera_capture_response_200_response_type_1_plate_solve_result.additional_properties = d
        return get_equipment_camera_capture_response_200_response_type_1_plate_solve_result

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

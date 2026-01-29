from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetPreparedImageSolveResponse200ResponseCoordinates")


@_attrs_define
class GetPreparedImageSolveResponse200ResponseCoordinates:
    """
    Attributes:
        ra (Union[Unset, float]):
        ra_degrees (Union[Unset, float]):
        dec (Union[Unset, float]):
        dec_degrees (Union[Unset, float]):
        epoch (Union[Unset, int]):
    """

    ra: Union[Unset, float] = UNSET
    ra_degrees: Union[Unset, float] = UNSET
    dec: Union[Unset, float] = UNSET
    dec_degrees: Union[Unset, float] = UNSET
    epoch: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        ra = self.ra

        ra_degrees = self.ra_degrees

        dec = self.dec

        dec_degrees = self.dec_degrees

        epoch = self.epoch

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ra is not UNSET:
            field_dict["RA"] = ra
        if ra_degrees is not UNSET:
            field_dict["RADegrees"] = ra_degrees
        if dec is not UNSET:
            field_dict["Dec"] = dec
        if dec_degrees is not UNSET:
            field_dict["DECDegrees"] = dec_degrees
        if epoch is not UNSET:
            field_dict["Epoch"] = epoch

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        ra = d.pop("RA", UNSET)

        ra_degrees = d.pop("RADegrees", UNSET)

        dec = d.pop("Dec", UNSET)

        dec_degrees = d.pop("DECDegrees", UNSET)

        epoch = d.pop("Epoch", UNSET)

        get_prepared_image_solve_response_200_response_coordinates = cls(
            ra=ra,
            ra_degrees=ra_degrees,
            dec=dec,
            dec_degrees=dec_degrees,
            epoch=epoch,
        )

        get_prepared_image_solve_response_200_response_coordinates.additional_properties = d
        return get_prepared_image_solve_response_200_response_coordinates

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

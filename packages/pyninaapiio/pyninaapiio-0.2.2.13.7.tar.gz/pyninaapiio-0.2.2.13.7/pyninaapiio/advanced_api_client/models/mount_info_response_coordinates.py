from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.mount_info_response_coordinates_epoch import MountInfoResponseCoordinatesEpoch

if TYPE_CHECKING:
    from ..models.mount_info_response_coordinates_date_time import MountInfoResponseCoordinatesDateTime


T = TypeVar("T", bound="MountInfoResponseCoordinates")


@_attrs_define
class MountInfoResponseCoordinates:
    """
    Attributes:
        ra (float):
        ra_string (str):
        ra_degrees (float):
        dec (float):
        dec_string (str):
        epoch (MountInfoResponseCoordinatesEpoch):
        date_time (MountInfoResponseCoordinatesDateTime):
    """

    ra: float
    ra_string: str
    ra_degrees: float
    dec: float
    dec_string: str
    epoch: MountInfoResponseCoordinatesEpoch
    date_time: "MountInfoResponseCoordinatesDateTime"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        ra = self.ra

        ra_string = self.ra_string

        ra_degrees = self.ra_degrees

        dec = self.dec

        dec_string = self.dec_string

        epoch = self.epoch.value

        date_time = self.date_time.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "RA": ra,
                "RAString": ra_string,
                "RADegrees": ra_degrees,
                "Dec": dec,
                "DecString": dec_string,
                "Epoch": epoch,
                "DateTime": date_time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.mount_info_response_coordinates_date_time import MountInfoResponseCoordinatesDateTime

        d = src_dict.copy()
        ra = d.pop("RA")

        ra_string = d.pop("RAString")

        ra_degrees = d.pop("RADegrees")

        dec = d.pop("Dec")

        dec_string = d.pop("DecString")

        epoch = MountInfoResponseCoordinatesEpoch(d.pop("Epoch"))

        date_time = MountInfoResponseCoordinatesDateTime.from_dict(d.pop("DateTime"))

        mount_info_response_coordinates = cls(
            ra=ra,
            ra_string=ra_string,
            ra_degrees=ra_degrees,
            dec=dec,
            dec_string=dec_string,
            epoch=epoch,
            date_time=date_time,
        )

        mount_info_response_coordinates.additional_properties = d
        return mount_info_response_coordinates

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

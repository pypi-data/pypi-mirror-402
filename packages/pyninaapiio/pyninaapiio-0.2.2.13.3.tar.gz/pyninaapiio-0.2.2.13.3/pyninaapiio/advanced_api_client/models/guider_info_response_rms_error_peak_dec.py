from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GuiderInfoResponseRMSErrorPeakDec")


@_attrs_define
class GuiderInfoResponseRMSErrorPeakDec:
    """
    Attributes:
        pixel (int):
        arcseconds (int):
    """

    pixel: int
    arcseconds: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        pixel = self.pixel

        arcseconds = self.arcseconds

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Pixel": pixel,
                "Arcseconds": arcseconds,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        pixel = d.pop("Pixel")

        arcseconds = d.pop("Arcseconds")

        guider_info_response_rms_error_peak_dec = cls(
            pixel=pixel,
            arcseconds=arcseconds,
        )

        guider_info_response_rms_error_peak_dec.additional_properties = d
        return guider_info_response_rms_error_peak_dec

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

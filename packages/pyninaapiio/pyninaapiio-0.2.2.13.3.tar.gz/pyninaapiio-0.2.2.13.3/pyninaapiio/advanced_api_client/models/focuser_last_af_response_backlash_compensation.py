from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FocuserLastAFResponseBacklashCompensation")


@_attrs_define
class FocuserLastAFResponseBacklashCompensation:
    """
    Attributes:
        backlash_compensation_model (str):
        backlash_in (int):
        backlash_out (int):
    """

    backlash_compensation_model: str
    backlash_in: int
    backlash_out: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        backlash_compensation_model = self.backlash_compensation_model

        backlash_in = self.backlash_in

        backlash_out = self.backlash_out

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "BacklashCompensationModel": backlash_compensation_model,
                "BacklashIN": backlash_in,
                "BacklashOUT": backlash_out,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        backlash_compensation_model = d.pop("BacklashCompensationModel")

        backlash_in = d.pop("BacklashIN")

        backlash_out = d.pop("BacklashOUT")

        focuser_last_af_response_backlash_compensation = cls(
            backlash_compensation_model=backlash_compensation_model,
            backlash_in=backlash_in,
            backlash_out=backlash_out,
        )

        focuser_last_af_response_backlash_compensation.additional_properties = d
        return focuser_last_af_response_backlash_compensation

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

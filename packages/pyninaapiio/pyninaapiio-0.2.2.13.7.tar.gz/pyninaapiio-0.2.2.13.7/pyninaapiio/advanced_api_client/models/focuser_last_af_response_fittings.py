from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FocuserLastAFResponseFittings")


@_attrs_define
class FocuserLastAFResponseFittings:
    """
    Attributes:
        quadratic (str):
        hyperbolic (str):
        gaussian (str):
        left_trend (str):
        right_trend (str):
    """

    quadratic: str
    hyperbolic: str
    gaussian: str
    left_trend: str
    right_trend: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        quadratic = self.quadratic

        hyperbolic = self.hyperbolic

        gaussian = self.gaussian

        left_trend = self.left_trend

        right_trend = self.right_trend

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Quadratic": quadratic,
                "Hyperbolic": hyperbolic,
                "Gaussian": gaussian,
                "LeftTrend": left_trend,
                "RightTrend": right_trend,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        quadratic = d.pop("Quadratic")

        hyperbolic = d.pop("Hyperbolic")

        gaussian = d.pop("Gaussian")

        left_trend = d.pop("LeftTrend")

        right_trend = d.pop("RightTrend")

        focuser_last_af_response_fittings = cls(
            quadratic=quadratic,
            hyperbolic=hyperbolic,
            gaussian=gaussian,
            left_trend=left_trend,
            right_trend=right_trend,
        )

        focuser_last_af_response_fittings.additional_properties = d
        return focuser_last_af_response_fittings

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

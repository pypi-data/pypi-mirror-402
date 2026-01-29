from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.focuser_last_af_response_intersections_hyperbolic_minimum import (
        FocuserLastAFResponseIntersectionsHyperbolicMinimum,
    )
    from ..models.focuser_last_af_response_intersections_trend_line_intersection import (
        FocuserLastAFResponseIntersectionsTrendLineIntersection,
    )


T = TypeVar("T", bound="FocuserLastAFResponseIntersections")


@_attrs_define
class FocuserLastAFResponseIntersections:
    """
    Attributes:
        trend_line_intersection (FocuserLastAFResponseIntersectionsTrendLineIntersection):
        hyperbolic_minimum (FocuserLastAFResponseIntersectionsHyperbolicMinimum):
    """

    trend_line_intersection: "FocuserLastAFResponseIntersectionsTrendLineIntersection"
    hyperbolic_minimum: "FocuserLastAFResponseIntersectionsHyperbolicMinimum"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        trend_line_intersection = self.trend_line_intersection.to_dict()

        hyperbolic_minimum = self.hyperbolic_minimum.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "TrendLineIntersection": trend_line_intersection,
                "HyperbolicMinimum": hyperbolic_minimum,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.focuser_last_af_response_intersections_hyperbolic_minimum import (
            FocuserLastAFResponseIntersectionsHyperbolicMinimum,
        )
        from ..models.focuser_last_af_response_intersections_trend_line_intersection import (
            FocuserLastAFResponseIntersectionsTrendLineIntersection,
        )

        d = src_dict.copy()
        trend_line_intersection = FocuserLastAFResponseIntersectionsTrendLineIntersection.from_dict(
            d.pop("TrendLineIntersection")
        )

        hyperbolic_minimum = FocuserLastAFResponseIntersectionsHyperbolicMinimum.from_dict(d.pop("HyperbolicMinimum"))

        focuser_last_af_response_intersections = cls(
            trend_line_intersection=trend_line_intersection,
            hyperbolic_minimum=hyperbolic_minimum,
        )

        focuser_last_af_response_intersections.additional_properties = d
        return focuser_last_af_response_intersections

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

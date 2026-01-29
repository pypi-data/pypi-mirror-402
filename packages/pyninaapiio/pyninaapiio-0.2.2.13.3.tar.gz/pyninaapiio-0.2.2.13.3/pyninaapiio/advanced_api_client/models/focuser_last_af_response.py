from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.focuser_last_af_response_backlash_compensation import FocuserLastAFResponseBacklashCompensation
    from ..models.focuser_last_af_response_calculated_focus_point import FocuserLastAFResponseCalculatedFocusPoint
    from ..models.focuser_last_af_response_fittings import FocuserLastAFResponseFittings
    from ..models.focuser_last_af_response_initial_focus_point import FocuserLastAFResponseInitialFocusPoint
    from ..models.focuser_last_af_response_intersections import FocuserLastAFResponseIntersections
    from ..models.focuser_last_af_response_measure_points_item import FocuserLastAFResponseMeasurePointsItem
    from ..models.focuser_last_af_response_previous_focus_point import FocuserLastAFResponsePreviousFocusPoint
    from ..models.focuser_last_af_response_r_squares import FocuserLastAFResponseRSquares


T = TypeVar("T", bound="FocuserLastAFResponse")


@_attrs_define
class FocuserLastAFResponse:
    """
    Attributes:
        version (int):
        filter_ (str):
        auto_focuser_name (str):
        star_detector_name (str):
        timestamp (str):
        temperature (float):
        method (str):
        fitting (str):
        initial_focus_point (FocuserLastAFResponseInitialFocusPoint):
        calculated_focus_point (FocuserLastAFResponseCalculatedFocusPoint):
        previous_focus_point (FocuserLastAFResponsePreviousFocusPoint):
        measure_points (List['FocuserLastAFResponseMeasurePointsItem']):
        intersections (FocuserLastAFResponseIntersections):
        fittings (FocuserLastAFResponseFittings):
        r_squares (FocuserLastAFResponseRSquares):
        backlash_compensation (FocuserLastAFResponseBacklashCompensation):
        duration (str):
    """

    version: int
    filter_: str
    auto_focuser_name: str
    star_detector_name: str
    timestamp: str
    temperature: float
    method: str
    fitting: str
    initial_focus_point: "FocuserLastAFResponseInitialFocusPoint"
    calculated_focus_point: "FocuserLastAFResponseCalculatedFocusPoint"
    previous_focus_point: "FocuserLastAFResponsePreviousFocusPoint"
    measure_points: List["FocuserLastAFResponseMeasurePointsItem"]
    intersections: "FocuserLastAFResponseIntersections"
    fittings: "FocuserLastAFResponseFittings"
    r_squares: "FocuserLastAFResponseRSquares"
    backlash_compensation: "FocuserLastAFResponseBacklashCompensation"
    duration: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        version = self.version

        filter_ = self.filter_

        auto_focuser_name = self.auto_focuser_name

        star_detector_name = self.star_detector_name

        timestamp = self.timestamp

        temperature = self.temperature

        method = self.method

        fitting = self.fitting

        initial_focus_point = self.initial_focus_point.to_dict()

        calculated_focus_point = self.calculated_focus_point.to_dict()

        previous_focus_point = self.previous_focus_point.to_dict()

        measure_points = []
        for measure_points_item_data in self.measure_points:
            measure_points_item = measure_points_item_data.to_dict()
            measure_points.append(measure_points_item)

        intersections = self.intersections.to_dict()

        fittings = self.fittings.to_dict()

        r_squares = self.r_squares.to_dict()

        backlash_compensation = self.backlash_compensation.to_dict()

        duration = self.duration

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Version": version,
                "Filter": filter_,
                "AutoFocuserName": auto_focuser_name,
                "StarDetectorName": star_detector_name,
                "Timestamp": timestamp,
                "Temperature": temperature,
                "Method": method,
                "Fitting": fitting,
                "InitialFocusPoint": initial_focus_point,
                "CalculatedFocusPoint": calculated_focus_point,
                "PreviousFocusPoint": previous_focus_point,
                "MeasurePoints": measure_points,
                "Intersections": intersections,
                "Fittings": fittings,
                "RSquares": r_squares,
                "BacklashCompensation": backlash_compensation,
                "Duration": duration,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.focuser_last_af_response_backlash_compensation import FocuserLastAFResponseBacklashCompensation
        from ..models.focuser_last_af_response_calculated_focus_point import FocuserLastAFResponseCalculatedFocusPoint
        from ..models.focuser_last_af_response_fittings import FocuserLastAFResponseFittings
        from ..models.focuser_last_af_response_initial_focus_point import FocuserLastAFResponseInitialFocusPoint
        from ..models.focuser_last_af_response_intersections import FocuserLastAFResponseIntersections
        from ..models.focuser_last_af_response_measure_points_item import FocuserLastAFResponseMeasurePointsItem
        from ..models.focuser_last_af_response_previous_focus_point import FocuserLastAFResponsePreviousFocusPoint
        from ..models.focuser_last_af_response_r_squares import FocuserLastAFResponseRSquares

        d = src_dict.copy()
        version = d.pop("Version")

        filter_ = d.pop("Filter")

        auto_focuser_name = d.pop("AutoFocuserName")

        star_detector_name = d.pop("StarDetectorName")

        timestamp = d.pop("Timestamp")

        temperature = d.pop("Temperature")

        method = d.pop("Method")

        fitting = d.pop("Fitting")

        initial_focus_point = FocuserLastAFResponseInitialFocusPoint.from_dict(d.pop("InitialFocusPoint"))

        calculated_focus_point = FocuserLastAFResponseCalculatedFocusPoint.from_dict(d.pop("CalculatedFocusPoint"))

        previous_focus_point = FocuserLastAFResponsePreviousFocusPoint.from_dict(d.pop("PreviousFocusPoint"))

        measure_points = []
        _measure_points = d.pop("MeasurePoints")
        for measure_points_item_data in _measure_points:
            measure_points_item = FocuserLastAFResponseMeasurePointsItem.from_dict(measure_points_item_data)

            measure_points.append(measure_points_item)

        intersections = FocuserLastAFResponseIntersections.from_dict(d.pop("Intersections"))

        fittings = FocuserLastAFResponseFittings.from_dict(d.pop("Fittings"))

        r_squares = FocuserLastAFResponseRSquares.from_dict(d.pop("RSquares"))

        backlash_compensation = FocuserLastAFResponseBacklashCompensation.from_dict(d.pop("BacklashCompensation"))

        duration = d.pop("Duration")

        focuser_last_af_response = cls(
            version=version,
            filter_=filter_,
            auto_focuser_name=auto_focuser_name,
            star_detector_name=star_detector_name,
            timestamp=timestamp,
            temperature=temperature,
            method=method,
            fitting=fitting,
            initial_focus_point=initial_focus_point,
            calculated_focus_point=calculated_focus_point,
            previous_focus_point=previous_focus_point,
            measure_points=measure_points,
            intersections=intersections,
            fittings=fittings,
            r_squares=r_squares,
            backlash_compensation=backlash_compensation,
            duration=duration,
        )

        focuser_last_af_response.additional_properties = d
        return focuser_last_af_response

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

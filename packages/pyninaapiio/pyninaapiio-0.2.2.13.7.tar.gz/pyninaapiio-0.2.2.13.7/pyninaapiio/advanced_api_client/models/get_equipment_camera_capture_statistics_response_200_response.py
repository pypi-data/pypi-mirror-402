from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetEquipmentCameraCaptureStatisticsResponse200Response")


@_attrs_define
class GetEquipmentCameraCaptureStatisticsResponse200Response:
    """
    Attributes:
        stars (Union[Unset, int]):
        hfr (Union[Unset, float]):
        median (Union[Unset, float]):
        median_absolute_deviation (Union[Unset, float]):
        mean (Union[Unset, float]):
        max_ (Union[Unset, int]):
        min_ (Union[Unset, int]):
        st_dev (Union[Unset, float]):
    """

    stars: Union[Unset, int] = UNSET
    hfr: Union[Unset, float] = UNSET
    median: Union[Unset, float] = UNSET
    median_absolute_deviation: Union[Unset, float] = UNSET
    mean: Union[Unset, float] = UNSET
    max_: Union[Unset, int] = UNSET
    min_: Union[Unset, int] = UNSET
    st_dev: Union[Unset, float] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        stars = self.stars

        hfr = self.hfr

        median = self.median

        median_absolute_deviation = self.median_absolute_deviation

        mean = self.mean

        max_ = self.max_

        min_ = self.min_

        st_dev = self.st_dev

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if stars is not UNSET:
            field_dict["Stars"] = stars
        if hfr is not UNSET:
            field_dict["HFR"] = hfr
        if median is not UNSET:
            field_dict["Median"] = median
        if median_absolute_deviation is not UNSET:
            field_dict["MedianAbsoluteDeviation"] = median_absolute_deviation
        if mean is not UNSET:
            field_dict["Mean"] = mean
        if max_ is not UNSET:
            field_dict["Max"] = max_
        if min_ is not UNSET:
            field_dict["Min"] = min_
        if st_dev is not UNSET:
            field_dict["StDev"] = st_dev

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        stars = d.pop("Stars", UNSET)

        hfr = d.pop("HFR", UNSET)

        median = d.pop("Median", UNSET)

        median_absolute_deviation = d.pop("MedianAbsoluteDeviation", UNSET)

        mean = d.pop("Mean", UNSET)

        max_ = d.pop("Max", UNSET)

        min_ = d.pop("Min", UNSET)

        st_dev = d.pop("StDev", UNSET)

        get_equipment_camera_capture_statistics_response_200_response = cls(
            stars=stars,
            hfr=hfr,
            median=median,
            median_absolute_deviation=median_absolute_deviation,
            mean=mean,
            max_=max_,
            min_=min_,
            st_dev=st_dev,
        )

        get_equipment_camera_capture_statistics_response_200_response.additional_properties = d
        return get_equipment_camera_capture_statistics_response_200_response

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

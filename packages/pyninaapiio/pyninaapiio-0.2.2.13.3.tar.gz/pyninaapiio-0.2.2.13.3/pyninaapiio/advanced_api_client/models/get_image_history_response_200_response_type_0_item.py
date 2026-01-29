from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_image_history_response_200_response_type_0_item_image_type import (
    GetImageHistoryResponse200ResponseType0ItemImageType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetImageHistoryResponse200ResponseType0Item")


@_attrs_define
class GetImageHistoryResponse200ResponseType0Item:
    """
    Attributes:
        exposure_time (Union[Unset, float]):
        image_type (Union[Unset, GetImageHistoryResponse200ResponseType0ItemImageType]):
        filter_ (Union[Unset, str]):
        rms_text (Union[Unset, str]):
        temperature (Union[Unset, str]):
        camera_name (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):
        date (Union[Unset, str]):
        telescope_name (Union[Unset, str]):
        focal_length (Union[Unset, float]):
        st_dev (Union[Unset, float]):
        mean (Union[Unset, float]):
        median (Union[Unset, float]):
        stars (Union[Unset, int]):
        hfr (Union[Unset, float]):
        is_bayered (Union[Unset, bool]):
        min_ (Union[Unset, float]):
        max_ (Union[Unset, float]):
        hfr_st_dev (Union[Unset, float]):
        target_name (Union[Unset, str]):
        filename (Union[Unset, str]):
    """

    exposure_time: Union[Unset, float] = UNSET
    image_type: Union[Unset, GetImageHistoryResponse200ResponseType0ItemImageType] = UNSET
    filter_: Union[Unset, str] = UNSET
    rms_text: Union[Unset, str] = UNSET
    temperature: Union[Unset, str] = UNSET
    camera_name: Union[Unset, str] = UNSET
    gain: Union[Unset, int] = UNSET
    offset: Union[Unset, int] = UNSET
    date: Union[Unset, str] = UNSET
    telescope_name: Union[Unset, str] = UNSET
    focal_length: Union[Unset, float] = UNSET
    st_dev: Union[Unset, float] = UNSET
    mean: Union[Unset, float] = UNSET
    median: Union[Unset, float] = UNSET
    stars: Union[Unset, int] = UNSET
    hfr: Union[Unset, float] = UNSET
    is_bayered: Union[Unset, bool] = UNSET
    min_: Union[Unset, float] = UNSET
    max_: Union[Unset, float] = UNSET
    hfr_st_dev: Union[Unset, float] = UNSET
    target_name: Union[Unset, str] = UNSET
    filename: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        exposure_time = self.exposure_time

        image_type: Union[Unset, str] = UNSET
        if not isinstance(self.image_type, Unset):
            image_type = self.image_type.value

        filter_ = self.filter_

        rms_text = self.rms_text

        temperature = self.temperature

        camera_name = self.camera_name

        gain = self.gain

        offset = self.offset

        date = self.date

        telescope_name = self.telescope_name

        focal_length = self.focal_length

        st_dev = self.st_dev

        mean = self.mean

        median = self.median

        stars = self.stars

        hfr = self.hfr

        is_bayered = self.is_bayered

        min_ = self.min_

        max_ = self.max_

        hfr_st_dev = self.hfr_st_dev

        target_name = self.target_name

        filename = self.filename

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if exposure_time is not UNSET:
            field_dict["ExposureTime"] = exposure_time
        if image_type is not UNSET:
            field_dict["ImageType"] = image_type
        if filter_ is not UNSET:
            field_dict["Filter"] = filter_
        if rms_text is not UNSET:
            field_dict["RmsText"] = rms_text
        if temperature is not UNSET:
            field_dict["Temperature"] = temperature
        if camera_name is not UNSET:
            field_dict["CameraName"] = camera_name
        if gain is not UNSET:
            field_dict["Gain"] = gain
        if offset is not UNSET:
            field_dict["Offset"] = offset
        if date is not UNSET:
            field_dict["Date"] = date
        if telescope_name is not UNSET:
            field_dict["TelescopeName"] = telescope_name
        if focal_length is not UNSET:
            field_dict["FocalLength"] = focal_length
        if st_dev is not UNSET:
            field_dict["StDev"] = st_dev
        if mean is not UNSET:
            field_dict["Mean"] = mean
        if median is not UNSET:
            field_dict["Median"] = median
        if stars is not UNSET:
            field_dict["Stars"] = stars
        if hfr is not UNSET:
            field_dict["HFR"] = hfr
        if is_bayered is not UNSET:
            field_dict["IsBayered"] = is_bayered
        if min_ is not UNSET:
            field_dict["Min"] = min_
        if max_ is not UNSET:
            field_dict["Max"] = max_
        if hfr_st_dev is not UNSET:
            field_dict["HFRStDev"] = hfr_st_dev
        if target_name is not UNSET:
            field_dict["TargetName"] = target_name
        if filename is not UNSET:
            field_dict["Filename"] = filename

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        exposure_time = d.pop("ExposureTime", UNSET)

        _image_type = d.pop("ImageType", UNSET)
        image_type: Union[Unset, GetImageHistoryResponse200ResponseType0ItemImageType]
        if isinstance(_image_type, Unset):
            image_type = UNSET
        else:
            image_type = GetImageHistoryResponse200ResponseType0ItemImageType(_image_type)

        filter_ = d.pop("Filter", UNSET)

        rms_text = d.pop("RmsText", UNSET)

        temperature = d.pop("Temperature", UNSET)

        camera_name = d.pop("CameraName", UNSET)

        gain = d.pop("Gain", UNSET)

        offset = d.pop("Offset", UNSET)

        date = d.pop("Date", UNSET)

        telescope_name = d.pop("TelescopeName", UNSET)

        focal_length = d.pop("FocalLength", UNSET)

        st_dev = d.pop("StDev", UNSET)

        mean = d.pop("Mean", UNSET)

        median = d.pop("Median", UNSET)

        stars = d.pop("Stars", UNSET)

        hfr = d.pop("HFR", UNSET)

        is_bayered = d.pop("IsBayered", UNSET)

        min_ = d.pop("Min", UNSET)

        max_ = d.pop("Max", UNSET)

        hfr_st_dev = d.pop("HFRStDev", UNSET)

        target_name = d.pop("TargetName", UNSET)

        filename = d.pop("Filename", UNSET)

        get_image_history_response_200_response_type_0_item = cls(
            exposure_time=exposure_time,
            image_type=image_type,
            filter_=filter_,
            rms_text=rms_text,
            temperature=temperature,
            camera_name=camera_name,
            gain=gain,
            offset=offset,
            date=date,
            telescope_name=telescope_name,
            focal_length=focal_length,
            st_dev=st_dev,
            mean=mean,
            median=median,
            stars=stars,
            hfr=hfr,
            is_bayered=is_bayered,
            min_=min_,
            max_=max_,
            hfr_st_dev=hfr_st_dev,
            target_name=target_name,
            filename=filename,
        )

        get_image_history_response_200_response_type_0_item.additional_properties = d
        return get_image_history_response_200_response_type_0_item

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

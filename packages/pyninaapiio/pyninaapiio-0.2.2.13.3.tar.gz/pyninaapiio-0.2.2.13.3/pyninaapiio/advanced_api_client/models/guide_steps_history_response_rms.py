from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GuideStepsHistoryResponseRMS")


@_attrs_define
class GuideStepsHistoryResponseRMS:
    """
    Attributes:
        ra (Union[Unset, float]):
        dec (Union[Unset, float]):
        total (Union[Unset, float]):
        ra_text (Union[Unset, str]):
        dec_text (Union[Unset, str]):
        total_text (Union[Unset, str]):
        peak_ra_text (Union[Unset, str]):
        peak_dec_text (Union[Unset, str]):
        scale (Union[Unset, float]):
        peak_ra (Union[Unset, float]):
        peak_dec (Union[Unset, float]):
        data_points (Union[Unset, int]):
    """

    ra: Union[Unset, float] = UNSET
    dec: Union[Unset, float] = UNSET
    total: Union[Unset, float] = UNSET
    ra_text: Union[Unset, str] = UNSET
    dec_text: Union[Unset, str] = UNSET
    total_text: Union[Unset, str] = UNSET
    peak_ra_text: Union[Unset, str] = UNSET
    peak_dec_text: Union[Unset, str] = UNSET
    scale: Union[Unset, float] = UNSET
    peak_ra: Union[Unset, float] = UNSET
    peak_dec: Union[Unset, float] = UNSET
    data_points: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        ra = self.ra

        dec = self.dec

        total = self.total

        ra_text = self.ra_text

        dec_text = self.dec_text

        total_text = self.total_text

        peak_ra_text = self.peak_ra_text

        peak_dec_text = self.peak_dec_text

        scale = self.scale

        peak_ra = self.peak_ra

        peak_dec = self.peak_dec

        data_points = self.data_points

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ra is not UNSET:
            field_dict["RA"] = ra
        if dec is not UNSET:
            field_dict["Dec"] = dec
        if total is not UNSET:
            field_dict["Total"] = total
        if ra_text is not UNSET:
            field_dict["RAText"] = ra_text
        if dec_text is not UNSET:
            field_dict["DecText"] = dec_text
        if total_text is not UNSET:
            field_dict["TotalText"] = total_text
        if peak_ra_text is not UNSET:
            field_dict["PeakRAText"] = peak_ra_text
        if peak_dec_text is not UNSET:
            field_dict["PeakDecText"] = peak_dec_text
        if scale is not UNSET:
            field_dict["Scale"] = scale
        if peak_ra is not UNSET:
            field_dict["PeakRA"] = peak_ra
        if peak_dec is not UNSET:
            field_dict["PeakDec"] = peak_dec
        if data_points is not UNSET:
            field_dict["DataPoints"] = data_points

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        ra = d.pop("RA", UNSET)

        dec = d.pop("Dec", UNSET)

        total = d.pop("Total", UNSET)

        ra_text = d.pop("RAText", UNSET)

        dec_text = d.pop("DecText", UNSET)

        total_text = d.pop("TotalText", UNSET)

        peak_ra_text = d.pop("PeakRAText", UNSET)

        peak_dec_text = d.pop("PeakDecText", UNSET)

        scale = d.pop("Scale", UNSET)

        peak_ra = d.pop("PeakRA", UNSET)

        peak_dec = d.pop("PeakDec", UNSET)

        data_points = d.pop("DataPoints", UNSET)

        guide_steps_history_response_rms = cls(
            ra=ra,
            dec=dec,
            total=total,
            ra_text=ra_text,
            dec_text=dec_text,
            total_text=total_text,
            peak_ra_text=peak_ra_text,
            peak_dec_text=peak_dec_text,
            scale=scale,
            peak_ra=peak_ra,
            peak_dec=peak_dec,
            data_points=data_points,
        )

        guide_steps_history_response_rms.additional_properties = d
        return guide_steps_history_response_rms

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

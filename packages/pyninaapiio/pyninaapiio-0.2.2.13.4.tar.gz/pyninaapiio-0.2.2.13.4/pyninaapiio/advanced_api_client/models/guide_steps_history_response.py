from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.guide_steps_history_response_guide_steps_item import GuideStepsHistoryResponseGuideStepsItem
    from ..models.guide_steps_history_response_rms import GuideStepsHistoryResponseRMS


T = TypeVar("T", bound="GuideStepsHistoryResponse")


@_attrs_define
class GuideStepsHistoryResponse:
    """
    Attributes:
        rms (Union[Unset, GuideStepsHistoryResponseRMS]):
        interval (Union[Unset, int]):
        max_y (Union[Unset, int]):
        min_y (Union[Unset, int]):
        max_duration_y (Union[Unset, int]):
        min_duration_y (Union[Unset, int]):
        guide_steps (Union[Unset, List['GuideStepsHistoryResponseGuideStepsItem']]):
        history_size (Union[Unset, int]):
        pixel_scale (Union[Unset, float]):
        scale (Union[Unset, int]):
    """

    rms: Union[Unset, "GuideStepsHistoryResponseRMS"] = UNSET
    interval: Union[Unset, int] = UNSET
    max_y: Union[Unset, int] = UNSET
    min_y: Union[Unset, int] = UNSET
    max_duration_y: Union[Unset, int] = UNSET
    min_duration_y: Union[Unset, int] = UNSET
    guide_steps: Union[Unset, List["GuideStepsHistoryResponseGuideStepsItem"]] = UNSET
    history_size: Union[Unset, int] = UNSET
    pixel_scale: Union[Unset, float] = UNSET
    scale: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        rms: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.rms, Unset):
            rms = self.rms.to_dict()

        interval = self.interval

        max_y = self.max_y

        min_y = self.min_y

        max_duration_y = self.max_duration_y

        min_duration_y = self.min_duration_y

        guide_steps: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.guide_steps, Unset):
            guide_steps = []
            for guide_steps_item_data in self.guide_steps:
                guide_steps_item = guide_steps_item_data.to_dict()
                guide_steps.append(guide_steps_item)

        history_size = self.history_size

        pixel_scale = self.pixel_scale

        scale = self.scale

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rms is not UNSET:
            field_dict["RMS"] = rms
        if interval is not UNSET:
            field_dict["Interval"] = interval
        if max_y is not UNSET:
            field_dict["MaxY"] = max_y
        if min_y is not UNSET:
            field_dict["MinY"] = min_y
        if max_duration_y is not UNSET:
            field_dict["MaxDurationY"] = max_duration_y
        if min_duration_y is not UNSET:
            field_dict["MinDurationY"] = min_duration_y
        if guide_steps is not UNSET:
            field_dict["GuideSteps"] = guide_steps
        if history_size is not UNSET:
            field_dict["HistorySize"] = history_size
        if pixel_scale is not UNSET:
            field_dict["PixelScale"] = pixel_scale
        if scale is not UNSET:
            field_dict["Scale"] = scale

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.guide_steps_history_response_guide_steps_item import GuideStepsHistoryResponseGuideStepsItem
        from ..models.guide_steps_history_response_rms import GuideStepsHistoryResponseRMS

        d = src_dict.copy()
        _rms = d.pop("RMS", UNSET)
        rms: Union[Unset, GuideStepsHistoryResponseRMS]
        if isinstance(_rms, Unset):
            rms = UNSET
        else:
            rms = GuideStepsHistoryResponseRMS.from_dict(_rms)

        interval = d.pop("Interval", UNSET)

        max_y = d.pop("MaxY", UNSET)

        min_y = d.pop("MinY", UNSET)

        max_duration_y = d.pop("MaxDurationY", UNSET)

        min_duration_y = d.pop("MinDurationY", UNSET)

        guide_steps = []
        _guide_steps = d.pop("GuideSteps", UNSET)
        for guide_steps_item_data in _guide_steps or []:
            guide_steps_item = GuideStepsHistoryResponseGuideStepsItem.from_dict(guide_steps_item_data)

            guide_steps.append(guide_steps_item)

        history_size = d.pop("HistorySize", UNSET)

        pixel_scale = d.pop("PixelScale", UNSET)

        scale = d.pop("Scale", UNSET)

        guide_steps_history_response = cls(
            rms=rms,
            interval=interval,
            max_y=max_y,
            min_y=min_y,
            max_duration_y=max_duration_y,
            min_duration_y=min_duration_y,
            guide_steps=guide_steps,
            history_size=history_size,
            pixel_scale=pixel_scale,
            scale=scale,
        )

        guide_steps_history_response.additional_properties = d
        return guide_steps_history_response

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

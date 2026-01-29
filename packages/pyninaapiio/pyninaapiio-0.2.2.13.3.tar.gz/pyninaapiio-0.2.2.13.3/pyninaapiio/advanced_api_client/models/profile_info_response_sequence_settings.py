from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseSequenceSettings")


@_attrs_define
class ProfileInfoResponseSequenceSettings:
    """
    Attributes:
        estimated_download_time (Union[Unset, str]):
        template_path (Union[Unset, str]):
        time_span_in_ticks (Union[Unset, int]):
        park_mount_at_sequence_end (Union[Unset, bool]):
        close_dome_shutter_at_sequence_end (Union[Unset, bool]):
        park_dome_at_sequence_end (Union[Unset, bool]):
        warm_cam_at_sequence_end (Union[Unset, bool]):
        default_sequence_folder (Union[Unset, str]):
        startup_sequence_template (Union[Unset, str]):
        sequencer_templates_folder (Union[Unset, str]):
        sequencer_targets_folder (Union[Unset, str]):
        collapse_sequencer_templates_by_default (Union[Unset, bool]):
        cool_camera_at_sequence_start (Union[Unset, bool]):
        unpar_mount_at_sequence_start (Union[Unset, bool]):
        open_dome_shutter_at_sequence_start (Union[Unset, bool]):
        do_meridian_flip (Union[Unset, bool]):
        disable_simple_sequencer (Union[Unset, bool]):
    """

    estimated_download_time: Union[Unset, str] = UNSET
    template_path: Union[Unset, str] = UNSET
    time_span_in_ticks: Union[Unset, int] = UNSET
    park_mount_at_sequence_end: Union[Unset, bool] = UNSET
    close_dome_shutter_at_sequence_end: Union[Unset, bool] = UNSET
    park_dome_at_sequence_end: Union[Unset, bool] = UNSET
    warm_cam_at_sequence_end: Union[Unset, bool] = UNSET
    default_sequence_folder: Union[Unset, str] = UNSET
    startup_sequence_template: Union[Unset, str] = UNSET
    sequencer_templates_folder: Union[Unset, str] = UNSET
    sequencer_targets_folder: Union[Unset, str] = UNSET
    collapse_sequencer_templates_by_default: Union[Unset, bool] = UNSET
    cool_camera_at_sequence_start: Union[Unset, bool] = UNSET
    unpar_mount_at_sequence_start: Union[Unset, bool] = UNSET
    open_dome_shutter_at_sequence_start: Union[Unset, bool] = UNSET
    do_meridian_flip: Union[Unset, bool] = UNSET
    disable_simple_sequencer: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        estimated_download_time = self.estimated_download_time

        template_path = self.template_path

        time_span_in_ticks = self.time_span_in_ticks

        park_mount_at_sequence_end = self.park_mount_at_sequence_end

        close_dome_shutter_at_sequence_end = self.close_dome_shutter_at_sequence_end

        park_dome_at_sequence_end = self.park_dome_at_sequence_end

        warm_cam_at_sequence_end = self.warm_cam_at_sequence_end

        default_sequence_folder = self.default_sequence_folder

        startup_sequence_template = self.startup_sequence_template

        sequencer_templates_folder = self.sequencer_templates_folder

        sequencer_targets_folder = self.sequencer_targets_folder

        collapse_sequencer_templates_by_default = self.collapse_sequencer_templates_by_default

        cool_camera_at_sequence_start = self.cool_camera_at_sequence_start

        unpar_mount_at_sequence_start = self.unpar_mount_at_sequence_start

        open_dome_shutter_at_sequence_start = self.open_dome_shutter_at_sequence_start

        do_meridian_flip = self.do_meridian_flip

        disable_simple_sequencer = self.disable_simple_sequencer

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if estimated_download_time is not UNSET:
            field_dict["EstimatedDownloadTime"] = estimated_download_time
        if template_path is not UNSET:
            field_dict["TemplatePath"] = template_path
        if time_span_in_ticks is not UNSET:
            field_dict["TimeSpanInTicks"] = time_span_in_ticks
        if park_mount_at_sequence_end is not UNSET:
            field_dict["ParkMountAtSequenceEnd"] = park_mount_at_sequence_end
        if close_dome_shutter_at_sequence_end is not UNSET:
            field_dict["CloseDomeShutterAtSequenceEnd"] = close_dome_shutter_at_sequence_end
        if park_dome_at_sequence_end is not UNSET:
            field_dict["ParkDomeAtSequenceEnd"] = park_dome_at_sequence_end
        if warm_cam_at_sequence_end is not UNSET:
            field_dict["WarmCamAtSequenceEnd"] = warm_cam_at_sequence_end
        if default_sequence_folder is not UNSET:
            field_dict["DefaultSequenceFolder"] = default_sequence_folder
        if startup_sequence_template is not UNSET:
            field_dict["StartupSequenceTemplate"] = startup_sequence_template
        if sequencer_templates_folder is not UNSET:
            field_dict["SequencerTemplatesFolder"] = sequencer_templates_folder
        if sequencer_targets_folder is not UNSET:
            field_dict["SequencerTargetsFolder"] = sequencer_targets_folder
        if collapse_sequencer_templates_by_default is not UNSET:
            field_dict["CollapseSequencerTemplatesByDefault"] = collapse_sequencer_templates_by_default
        if cool_camera_at_sequence_start is not UNSET:
            field_dict["CoolCameraAtSequenceStart"] = cool_camera_at_sequence_start
        if unpar_mount_at_sequence_start is not UNSET:
            field_dict["UnparMountAtSequenceStart"] = unpar_mount_at_sequence_start
        if open_dome_shutter_at_sequence_start is not UNSET:
            field_dict["OpenDomeShutterAtSequenceStart"] = open_dome_shutter_at_sequence_start
        if do_meridian_flip is not UNSET:
            field_dict["DoMeridianFlip"] = do_meridian_flip
        if disable_simple_sequencer is not UNSET:
            field_dict["DisableSimpleSequencer"] = disable_simple_sequencer

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        estimated_download_time = d.pop("EstimatedDownloadTime", UNSET)

        template_path = d.pop("TemplatePath", UNSET)

        time_span_in_ticks = d.pop("TimeSpanInTicks", UNSET)

        park_mount_at_sequence_end = d.pop("ParkMountAtSequenceEnd", UNSET)

        close_dome_shutter_at_sequence_end = d.pop("CloseDomeShutterAtSequenceEnd", UNSET)

        park_dome_at_sequence_end = d.pop("ParkDomeAtSequenceEnd", UNSET)

        warm_cam_at_sequence_end = d.pop("WarmCamAtSequenceEnd", UNSET)

        default_sequence_folder = d.pop("DefaultSequenceFolder", UNSET)

        startup_sequence_template = d.pop("StartupSequenceTemplate", UNSET)

        sequencer_templates_folder = d.pop("SequencerTemplatesFolder", UNSET)

        sequencer_targets_folder = d.pop("SequencerTargetsFolder", UNSET)

        collapse_sequencer_templates_by_default = d.pop("CollapseSequencerTemplatesByDefault", UNSET)

        cool_camera_at_sequence_start = d.pop("CoolCameraAtSequenceStart", UNSET)

        unpar_mount_at_sequence_start = d.pop("UnparMountAtSequenceStart", UNSET)

        open_dome_shutter_at_sequence_start = d.pop("OpenDomeShutterAtSequenceStart", UNSET)

        do_meridian_flip = d.pop("DoMeridianFlip", UNSET)

        disable_simple_sequencer = d.pop("DisableSimpleSequencer", UNSET)

        profile_info_response_sequence_settings = cls(
            estimated_download_time=estimated_download_time,
            template_path=template_path,
            time_span_in_ticks=time_span_in_ticks,
            park_mount_at_sequence_end=park_mount_at_sequence_end,
            close_dome_shutter_at_sequence_end=close_dome_shutter_at_sequence_end,
            park_dome_at_sequence_end=park_dome_at_sequence_end,
            warm_cam_at_sequence_end=warm_cam_at_sequence_end,
            default_sequence_folder=default_sequence_folder,
            startup_sequence_template=startup_sequence_template,
            sequencer_templates_folder=sequencer_templates_folder,
            sequencer_targets_folder=sequencer_targets_folder,
            collapse_sequencer_templates_by_default=collapse_sequencer_templates_by_default,
            cool_camera_at_sequence_start=cool_camera_at_sequence_start,
            unpar_mount_at_sequence_start=unpar_mount_at_sequence_start,
            open_dome_shutter_at_sequence_start=open_dome_shutter_at_sequence_start,
            do_meridian_flip=do_meridian_flip,
            disable_simple_sequencer=disable_simple_sequencer,
        )

        profile_info_response_sequence_settings.additional_properties = d
        return profile_info_response_sequence_settings

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

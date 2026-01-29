from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.guider_info_response_state import GuiderInfoResponseState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.guider_info_response_last_guide_step import GuiderInfoResponseLastGuideStep
    from ..models.guider_info_response_rms_error import GuiderInfoResponseRMSError


T = TypeVar("T", bound="GuiderInfoResponse")


@_attrs_define
class GuiderInfoResponse:
    """
    Attributes:
        connected (bool):
        can_clear_calibration (bool):
        can_set_shift_rate (bool):
        can_get_lock_position (bool):
        pixel_scale (float):
        name (Union[Unset, str]):
        display_name (Union[Unset, str]):
        description (Union[Unset, str]):
        driver_info (Union[Unset, str]):
        driver_version (Union[Unset, str]):
        device_id (Union[Unset, str]):
        supported_actions (Union[Unset, List[Any]]):
        rms_error (Union[Unset, GuiderInfoResponseRMSError]):
        last_guide_step (Union[Unset, GuiderInfoResponseLastGuideStep]):
        state (Union[Unset, GuiderInfoResponseState]):
    """

    connected: bool
    can_clear_calibration: bool
    can_set_shift_rate: bool
    can_get_lock_position: bool
    pixel_scale: float
    name: Union[Unset, str] = UNSET
    display_name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    driver_info: Union[Unset, str] = UNSET
    driver_version: Union[Unset, str] = UNSET
    device_id: Union[Unset, str] = UNSET
    supported_actions: Union[Unset, List[Any]] = UNSET
    rms_error: Union[Unset, "GuiderInfoResponseRMSError"] = UNSET
    last_guide_step: Union[Unset, "GuiderInfoResponseLastGuideStep"] = UNSET
    state: Union[Unset, GuiderInfoResponseState] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        connected = self.connected

        can_clear_calibration = self.can_clear_calibration

        can_set_shift_rate = self.can_set_shift_rate

        can_get_lock_position = self.can_get_lock_position

        pixel_scale = self.pixel_scale

        name = self.name

        display_name = self.display_name

        description = self.description

        driver_info = self.driver_info

        driver_version = self.driver_version

        device_id = self.device_id

        supported_actions: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.supported_actions, Unset):
            supported_actions = self.supported_actions

        rms_error: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.rms_error, Unset):
            rms_error = self.rms_error.to_dict()

        last_guide_step: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.last_guide_step, Unset):
            last_guide_step = self.last_guide_step.to_dict()

        state: Union[Unset, str] = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Connected": connected,
                "CanClearCalibration": can_clear_calibration,
                "CanSetShiftRate": can_set_shift_rate,
                "CanGetLockPosition": can_get_lock_position,
                "PixelScale": pixel_scale,
            }
        )
        if name is not UNSET:
            field_dict["Name"] = name
        if display_name is not UNSET:
            field_dict["DisplayName"] = display_name
        if description is not UNSET:
            field_dict["Description"] = description
        if driver_info is not UNSET:
            field_dict["DriverInfo"] = driver_info
        if driver_version is not UNSET:
            field_dict["DriverVersion"] = driver_version
        if device_id is not UNSET:
            field_dict["DeviceId"] = device_id
        if supported_actions is not UNSET:
            field_dict["SupportedActions"] = supported_actions
        if rms_error is not UNSET:
            field_dict["RMSError"] = rms_error
        if last_guide_step is not UNSET:
            field_dict["LastGuideStep"] = last_guide_step
        if state is not UNSET:
            field_dict["State"] = state

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.guider_info_response_last_guide_step import GuiderInfoResponseLastGuideStep
        from ..models.guider_info_response_rms_error import GuiderInfoResponseRMSError

        d = src_dict.copy()
        connected = d.pop("Connected")

        can_clear_calibration = d.pop("CanClearCalibration")

        can_set_shift_rate = d.pop("CanSetShiftRate")

        can_get_lock_position = d.pop("CanGetLockPosition")

        pixel_scale = d.pop("PixelScale")

        name = d.pop("Name", UNSET)

        display_name = d.pop("DisplayName", UNSET)

        description = d.pop("Description", UNSET)

        driver_info = d.pop("DriverInfo", UNSET)

        driver_version = d.pop("DriverVersion", UNSET)

        device_id = d.pop("DeviceId", UNSET)

        supported_actions = cast(List[Any], d.pop("SupportedActions", UNSET))

        _rms_error = d.pop("RMSError", UNSET)
        rms_error: Union[Unset, GuiderInfoResponseRMSError]
        if isinstance(_rms_error, Unset):
            rms_error = UNSET
        else:
            rms_error = GuiderInfoResponseRMSError.from_dict(_rms_error)

        _last_guide_step = d.pop("LastGuideStep", UNSET)
        last_guide_step: Union[Unset, GuiderInfoResponseLastGuideStep]
        if isinstance(_last_guide_step, Unset):
            last_guide_step = UNSET
        else:
            last_guide_step = GuiderInfoResponseLastGuideStep.from_dict(_last_guide_step)

        _state = d.pop("State", UNSET)
        state: Union[Unset, GuiderInfoResponseState]
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = GuiderInfoResponseState(_state)

        guider_info_response = cls(
            connected=connected,
            can_clear_calibration=can_clear_calibration,
            can_set_shift_rate=can_set_shift_rate,
            can_get_lock_position=can_get_lock_position,
            pixel_scale=pixel_scale,
            name=name,
            display_name=display_name,
            description=description,
            driver_info=driver_info,
            driver_version=driver_version,
            device_id=device_id,
            supported_actions=supported_actions,
            rms_error=rms_error,
            last_guide_step=last_guide_step,
            state=state,
        )

        guider_info_response.additional_properties = d
        return guider_info_response

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

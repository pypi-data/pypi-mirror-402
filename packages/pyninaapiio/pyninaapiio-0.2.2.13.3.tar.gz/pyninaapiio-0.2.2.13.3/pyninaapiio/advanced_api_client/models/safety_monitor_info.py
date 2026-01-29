from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.safety_monitor_info_response import SafetyMonitorInfoResponse


T = TypeVar("T", bound="SafetyMonitorInfo")


@_attrs_define
class SafetyMonitorInfo:
    """
    Attributes:
        response (SafetyMonitorInfoResponse):
        error (str):
        status_code (int):
        success (bool):
        type (str):
    """

    response: "SafetyMonitorInfoResponse"
    error: str
    status_code: int
    success: bool
    type: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        response = self.response.to_dict()

        error = self.error

        status_code = self.status_code

        success = self.success

        type = self.type

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Response": response,
                "Error": error,
                "StatusCode": status_code,
                "Success": success,
                "Type": type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.safety_monitor_info_response import SafetyMonitorInfoResponse

        d = src_dict.copy()
        response = SafetyMonitorInfoResponse.from_dict(d.pop("Response"))

        error = d.pop("Error")

        status_code = d.pop("StatusCode")

        success = d.pop("Success")

        type = d.pop("Type")

        safety_monitor_info = cls(
            response=response,
            error=error,
            status_code=status_code,
            success=success,
            type=type,
        )

        safety_monitor_info.additional_properties = d
        return safety_monitor_info

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

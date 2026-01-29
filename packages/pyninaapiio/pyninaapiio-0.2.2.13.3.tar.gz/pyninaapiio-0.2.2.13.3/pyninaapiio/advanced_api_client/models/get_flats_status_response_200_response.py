from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_flats_status_response_200_response_state import GetFlatsStatusResponse200ResponseState
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetFlatsStatusResponse200Response")


@_attrs_define
class GetFlatsStatusResponse200Response:
    """
    Attributes:
        completed_iterations (Union[Unset, int]):  Example: 10.
        total_iterations (Union[Unset, int]):  Example: 15.
        state (Union[Unset, GetFlatsStatusResponse200ResponseState]):
    """

    completed_iterations: Union[Unset, int] = UNSET
    total_iterations: Union[Unset, int] = UNSET
    state: Union[Unset, GetFlatsStatusResponse200ResponseState] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        completed_iterations = self.completed_iterations

        total_iterations = self.total_iterations

        state: Union[Unset, str] = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if completed_iterations is not UNSET:
            field_dict["CompletedIterations"] = completed_iterations
        if total_iterations is not UNSET:
            field_dict["TotalIterations"] = total_iterations
        if state is not UNSET:
            field_dict["State"] = state

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        completed_iterations = d.pop("CompletedIterations", UNSET)

        total_iterations = d.pop("TotalIterations", UNSET)

        _state = d.pop("State", UNSET)
        state: Union[Unset, GetFlatsStatusResponse200ResponseState]
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = GetFlatsStatusResponse200ResponseState(_state)

        get_flats_status_response_200_response = cls(
            completed_iterations=completed_iterations,
            total_iterations=total_iterations,
            state=state,
        )

        get_flats_status_response_200_response.additional_properties = d
        return get_flats_status_response_200_response

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

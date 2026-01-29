from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseAlpacaSettings")


@_attrs_define
class ProfileInfoResponseAlpacaSettings:
    """
    Attributes:
        number_of_polls (Union[Unset, int]):
        poll_interval (Union[Unset, int]):
        discovery_port (Union[Unset, int]):
        discovery_duration (Union[Unset, int]):
        resolve_dns_name (Union[Unset, bool]):
        use_i_pv_4 (Union[Unset, bool]):
        use_i_pv_6 (Union[Unset, bool]):
        use_https (Union[Unset, bool]):
    """

    number_of_polls: Union[Unset, int] = UNSET
    poll_interval: Union[Unset, int] = UNSET
    discovery_port: Union[Unset, int] = UNSET
    discovery_duration: Union[Unset, int] = UNSET
    resolve_dns_name: Union[Unset, bool] = UNSET
    use_i_pv_4: Union[Unset, bool] = UNSET
    use_i_pv_6: Union[Unset, bool] = UNSET
    use_https: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        number_of_polls = self.number_of_polls

        poll_interval = self.poll_interval

        discovery_port = self.discovery_port

        discovery_duration = self.discovery_duration

        resolve_dns_name = self.resolve_dns_name

        use_i_pv_4 = self.use_i_pv_4

        use_i_pv_6 = self.use_i_pv_6

        use_https = self.use_https

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if number_of_polls is not UNSET:
            field_dict["NumberOfPolls"] = number_of_polls
        if poll_interval is not UNSET:
            field_dict["PollInterval"] = poll_interval
        if discovery_port is not UNSET:
            field_dict["DiscoveryPort"] = discovery_port
        if discovery_duration is not UNSET:
            field_dict["DiscoveryDuration"] = discovery_duration
        if resolve_dns_name is not UNSET:
            field_dict["ResolveDnsName"] = resolve_dns_name
        if use_i_pv_4 is not UNSET:
            field_dict["UseIPv4"] = use_i_pv_4
        if use_i_pv_6 is not UNSET:
            field_dict["UseIPv6"] = use_i_pv_6
        if use_https is not UNSET:
            field_dict["UseHttps"] = use_https

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        number_of_polls = d.pop("NumberOfPolls", UNSET)

        poll_interval = d.pop("PollInterval", UNSET)

        discovery_port = d.pop("DiscoveryPort", UNSET)

        discovery_duration = d.pop("DiscoveryDuration", UNSET)

        resolve_dns_name = d.pop("ResolveDnsName", UNSET)

        use_i_pv_4 = d.pop("UseIPv4", UNSET)

        use_i_pv_6 = d.pop("UseIPv6", UNSET)

        use_https = d.pop("UseHttps", UNSET)

        profile_info_response_alpaca_settings = cls(
            number_of_polls=number_of_polls,
            poll_interval=poll_interval,
            discovery_port=discovery_port,
            discovery_duration=discovery_duration,
            resolve_dns_name=resolve_dns_name,
            use_i_pv_4=use_i_pv_4,
            use_i_pv_6=use_i_pv_6,
            use_https=use_https,
        )

        profile_info_response_alpaca_settings.additional_properties = d
        return profile_info_response_alpaca_settings

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

from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_image_settings_noise_reduction import ProfileInfoResponseImageSettingsNoiseReduction
from ..models.profile_info_response_image_settings_star_sensitivity import (
    ProfileInfoResponseImageSettingsStarSensitivity,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseImageSettings")


@_attrs_define
class ProfileInfoResponseImageSettings:
    """
    Attributes:
        annotate_image (Union[Unset, bool]):
        debayer_image (Union[Unset, bool]):
        debayered_hfr (Union[Unset, bool]):
        unlinked_stretch (Union[Unset, bool]):
        annotate_unlimited_stars (Union[Unset, bool]):
        auto_stretch_factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        star_sensitivity (Union[Unset, ProfileInfoResponseImageSettingsStarSensitivity]):
        noise_reduction (Union[Unset, ProfileInfoResponseImageSettingsNoiseReduction]):
        detect_stars (Union[Unset, bool]):
        auto_stretch (Union[Unset, bool]):
    """

    annotate_image: Union[Unset, bool] = UNSET
    debayer_image: Union[Unset, bool] = UNSET
    debayered_hfr: Union[Unset, bool] = UNSET
    unlinked_stretch: Union[Unset, bool] = UNSET
    annotate_unlimited_stars: Union[Unset, bool] = UNSET
    auto_stretch_factor: Union[Unset, float] = UNSET
    black_clipping: Union[Unset, float] = UNSET
    star_sensitivity: Union[Unset, ProfileInfoResponseImageSettingsStarSensitivity] = UNSET
    noise_reduction: Union[Unset, ProfileInfoResponseImageSettingsNoiseReduction] = UNSET
    detect_stars: Union[Unset, bool] = UNSET
    auto_stretch: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        annotate_image = self.annotate_image

        debayer_image = self.debayer_image

        debayered_hfr = self.debayered_hfr

        unlinked_stretch = self.unlinked_stretch

        annotate_unlimited_stars = self.annotate_unlimited_stars

        auto_stretch_factor = self.auto_stretch_factor

        black_clipping = self.black_clipping

        star_sensitivity: Union[Unset, str] = UNSET
        if not isinstance(self.star_sensitivity, Unset):
            star_sensitivity = self.star_sensitivity.value

        noise_reduction: Union[Unset, str] = UNSET
        if not isinstance(self.noise_reduction, Unset):
            noise_reduction = self.noise_reduction.value

        detect_stars = self.detect_stars

        auto_stretch = self.auto_stretch

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if annotate_image is not UNSET:
            field_dict["AnnotateImage"] = annotate_image
        if debayer_image is not UNSET:
            field_dict["DebayerImage"] = debayer_image
        if debayered_hfr is not UNSET:
            field_dict["DebayeredHFR"] = debayered_hfr
        if unlinked_stretch is not UNSET:
            field_dict["UnlinkedStretch"] = unlinked_stretch
        if annotate_unlimited_stars is not UNSET:
            field_dict["AnnotateUnlimitedStars"] = annotate_unlimited_stars
        if auto_stretch_factor is not UNSET:
            field_dict["AutoStretchFactor"] = auto_stretch_factor
        if black_clipping is not UNSET:
            field_dict["BlackClipping"] = black_clipping
        if star_sensitivity is not UNSET:
            field_dict["StarSensitivity"] = star_sensitivity
        if noise_reduction is not UNSET:
            field_dict["NoiseReduction"] = noise_reduction
        if detect_stars is not UNSET:
            field_dict["DetectStars"] = detect_stars
        if auto_stretch is not UNSET:
            field_dict["AutoStretch"] = auto_stretch

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        annotate_image = d.pop("AnnotateImage", UNSET)

        debayer_image = d.pop("DebayerImage", UNSET)

        debayered_hfr = d.pop("DebayeredHFR", UNSET)

        unlinked_stretch = d.pop("UnlinkedStretch", UNSET)

        annotate_unlimited_stars = d.pop("AnnotateUnlimitedStars", UNSET)

        auto_stretch_factor = d.pop("AutoStretchFactor", UNSET)

        black_clipping = d.pop("BlackClipping", UNSET)

        _star_sensitivity = d.pop("StarSensitivity", UNSET)
        star_sensitivity: Union[Unset, ProfileInfoResponseImageSettingsStarSensitivity]
        if isinstance(_star_sensitivity, Unset):
            star_sensitivity = UNSET
        else:
            star_sensitivity = ProfileInfoResponseImageSettingsStarSensitivity(_star_sensitivity)

        _noise_reduction = d.pop("NoiseReduction", UNSET)
        noise_reduction: Union[Unset, ProfileInfoResponseImageSettingsNoiseReduction]
        if isinstance(_noise_reduction, Unset):
            noise_reduction = UNSET
        else:
            noise_reduction = ProfileInfoResponseImageSettingsNoiseReduction(_noise_reduction)

        detect_stars = d.pop("DetectStars", UNSET)

        auto_stretch = d.pop("AutoStretch", UNSET)

        profile_info_response_image_settings = cls(
            annotate_image=annotate_image,
            debayer_image=debayer_image,
            debayered_hfr=debayered_hfr,
            unlinked_stretch=unlinked_stretch,
            annotate_unlimited_stars=annotate_unlimited_stars,
            auto_stretch_factor=auto_stretch_factor,
            black_clipping=black_clipping,
            star_sensitivity=star_sensitivity,
            noise_reduction=noise_reduction,
            detect_stars=detect_stars,
            auto_stretch=auto_stretch,
        )

        profile_info_response_image_settings.additional_properties = d
        return profile_info_response_image_settings

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

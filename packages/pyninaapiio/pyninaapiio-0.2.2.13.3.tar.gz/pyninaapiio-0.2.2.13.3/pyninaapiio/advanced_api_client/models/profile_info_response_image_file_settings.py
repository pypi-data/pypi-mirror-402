from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.profile_info_response_image_file_settings_file_type import ProfileInfoResponseImageFileSettingsFileType
from ..models.profile_info_response_image_file_settings_fits_compression_type import (
    ProfileInfoResponseImageFileSettingsFITSCompressionType,
)
from ..models.profile_info_response_image_file_settings_tiff_compression_type import (
    ProfileInfoResponseImageFileSettingsTIFFCompressionType,
)
from ..models.profile_info_response_image_file_settings_xisf_checksum_type import (
    ProfileInfoResponseImageFileSettingsXISFChecksumType,
)
from ..models.profile_info_response_image_file_settings_xisf_compression_type import (
    ProfileInfoResponseImageFileSettingsXISFCompressionType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileInfoResponseImageFileSettings")


@_attrs_define
class ProfileInfoResponseImageFileSettings:
    """
    Attributes:
        file_path (Union[Unset, str]):
        file_pattern (Union[Unset, str]):
        file_pattern_dark (Union[Unset, str]):
        file_pattern_bias (Union[Unset, str]):
        file_pattern_flat (Union[Unset, str]):
        file_type (Union[Unset, ProfileInfoResponseImageFileSettingsFileType]):
        tiff_compression_type (Union[Unset, ProfileInfoResponseImageFileSettingsTIFFCompressionType]):
        xisf_compression_type (Union[Unset, ProfileInfoResponseImageFileSettingsXISFCompressionType]):
        xisf_checksum_type (Union[Unset, ProfileInfoResponseImageFileSettingsXISFChecksumType]):
        xisf_byte_shuffling (Union[Unset, bool]):
        fits_compression_type (Union[Unset, ProfileInfoResponseImageFileSettingsFITSCompressionType]):
        fits_add_fz_extension (Union[Unset, bool]):
        fits_use_legacy_writer (Union[Unset, bool]):
    """

    file_path: Union[Unset, str] = UNSET
    file_pattern: Union[Unset, str] = UNSET
    file_pattern_dark: Union[Unset, str] = UNSET
    file_pattern_bias: Union[Unset, str] = UNSET
    file_pattern_flat: Union[Unset, str] = UNSET
    file_type: Union[Unset, ProfileInfoResponseImageFileSettingsFileType] = UNSET
    tiff_compression_type: Union[Unset, ProfileInfoResponseImageFileSettingsTIFFCompressionType] = UNSET
    xisf_compression_type: Union[Unset, ProfileInfoResponseImageFileSettingsXISFCompressionType] = UNSET
    xisf_checksum_type: Union[Unset, ProfileInfoResponseImageFileSettingsXISFChecksumType] = UNSET
    xisf_byte_shuffling: Union[Unset, bool] = UNSET
    fits_compression_type: Union[Unset, ProfileInfoResponseImageFileSettingsFITSCompressionType] = UNSET
    fits_add_fz_extension: Union[Unset, bool] = UNSET
    fits_use_legacy_writer: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        file_path = self.file_path

        file_pattern = self.file_pattern

        file_pattern_dark = self.file_pattern_dark

        file_pattern_bias = self.file_pattern_bias

        file_pattern_flat = self.file_pattern_flat

        file_type: Union[Unset, str] = UNSET
        if not isinstance(self.file_type, Unset):
            file_type = self.file_type.value

        tiff_compression_type: Union[Unset, str] = UNSET
        if not isinstance(self.tiff_compression_type, Unset):
            tiff_compression_type = self.tiff_compression_type.value

        xisf_compression_type: Union[Unset, str] = UNSET
        if not isinstance(self.xisf_compression_type, Unset):
            xisf_compression_type = self.xisf_compression_type.value

        xisf_checksum_type: Union[Unset, str] = UNSET
        if not isinstance(self.xisf_checksum_type, Unset):
            xisf_checksum_type = self.xisf_checksum_type.value

        xisf_byte_shuffling = self.xisf_byte_shuffling

        fits_compression_type: Union[Unset, str] = UNSET
        if not isinstance(self.fits_compression_type, Unset):
            fits_compression_type = self.fits_compression_type.value

        fits_add_fz_extension = self.fits_add_fz_extension

        fits_use_legacy_writer = self.fits_use_legacy_writer

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file_path is not UNSET:
            field_dict["FilePath"] = file_path
        if file_pattern is not UNSET:
            field_dict["FilePattern"] = file_pattern
        if file_pattern_dark is not UNSET:
            field_dict["FilePatternDARK"] = file_pattern_dark
        if file_pattern_bias is not UNSET:
            field_dict["FilePatternBIAS"] = file_pattern_bias
        if file_pattern_flat is not UNSET:
            field_dict["FilePatternFLAT"] = file_pattern_flat
        if file_type is not UNSET:
            field_dict["FileType"] = file_type
        if tiff_compression_type is not UNSET:
            field_dict["TIFFCompressionType"] = tiff_compression_type
        if xisf_compression_type is not UNSET:
            field_dict["XISFCompressionType"] = xisf_compression_type
        if xisf_checksum_type is not UNSET:
            field_dict["XISFChecksumType"] = xisf_checksum_type
        if xisf_byte_shuffling is not UNSET:
            field_dict["XISFByteShuffling"] = xisf_byte_shuffling
        if fits_compression_type is not UNSET:
            field_dict["FITSCompressionType"] = fits_compression_type
        if fits_add_fz_extension is not UNSET:
            field_dict["FITSAddFzExtension"] = fits_add_fz_extension
        if fits_use_legacy_writer is not UNSET:
            field_dict["FITSUseLegacyWriter"] = fits_use_legacy_writer

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        file_path = d.pop("FilePath", UNSET)

        file_pattern = d.pop("FilePattern", UNSET)

        file_pattern_dark = d.pop("FilePatternDARK", UNSET)

        file_pattern_bias = d.pop("FilePatternBIAS", UNSET)

        file_pattern_flat = d.pop("FilePatternFLAT", UNSET)

        _file_type = d.pop("FileType", UNSET)
        file_type: Union[Unset, ProfileInfoResponseImageFileSettingsFileType]
        if isinstance(_file_type, Unset):
            file_type = UNSET
        else:
            file_type = ProfileInfoResponseImageFileSettingsFileType(_file_type)

        _tiff_compression_type = d.pop("TIFFCompressionType", UNSET)
        tiff_compression_type: Union[Unset, ProfileInfoResponseImageFileSettingsTIFFCompressionType]
        if isinstance(_tiff_compression_type, Unset):
            tiff_compression_type = UNSET
        else:
            tiff_compression_type = ProfileInfoResponseImageFileSettingsTIFFCompressionType(_tiff_compression_type)

        _xisf_compression_type = d.pop("XISFCompressionType", UNSET)
        xisf_compression_type: Union[Unset, ProfileInfoResponseImageFileSettingsXISFCompressionType]
        if isinstance(_xisf_compression_type, Unset):
            xisf_compression_type = UNSET
        else:
            xisf_compression_type = ProfileInfoResponseImageFileSettingsXISFCompressionType(_xisf_compression_type)

        _xisf_checksum_type = d.pop("XISFChecksumType", UNSET)
        xisf_checksum_type: Union[Unset, ProfileInfoResponseImageFileSettingsXISFChecksumType]
        if isinstance(_xisf_checksum_type, Unset):
            xisf_checksum_type = UNSET
        else:
            xisf_checksum_type = ProfileInfoResponseImageFileSettingsXISFChecksumType(_xisf_checksum_type)

        xisf_byte_shuffling = d.pop("XISFByteShuffling", UNSET)

        _fits_compression_type = d.pop("FITSCompressionType", UNSET)
        fits_compression_type: Union[Unset, ProfileInfoResponseImageFileSettingsFITSCompressionType]
        if isinstance(_fits_compression_type, Unset):
            fits_compression_type = UNSET
        else:
            fits_compression_type = ProfileInfoResponseImageFileSettingsFITSCompressionType(_fits_compression_type)

        fits_add_fz_extension = d.pop("FITSAddFzExtension", UNSET)

        fits_use_legacy_writer = d.pop("FITSUseLegacyWriter", UNSET)

        profile_info_response_image_file_settings = cls(
            file_path=file_path,
            file_pattern=file_pattern,
            file_pattern_dark=file_pattern_dark,
            file_pattern_bias=file_pattern_bias,
            file_pattern_flat=file_pattern_flat,
            file_type=file_type,
            tiff_compression_type=tiff_compression_type,
            xisf_compression_type=xisf_compression_type,
            xisf_checksum_type=xisf_checksum_type,
            xisf_byte_shuffling=xisf_byte_shuffling,
            fits_compression_type=fits_compression_type,
            fits_add_fz_extension=fits_add_fz_extension,
            fits_use_legacy_writer=fits_use_legacy_writer,
        )

        profile_info_response_image_file_settings.additional_properties = d
        return profile_info_response_image_file_settings

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

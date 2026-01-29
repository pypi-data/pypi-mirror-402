from enum import Enum


class ProfileInfoResponseImageFileSettingsFileType(str, Enum):
    FITS = "FITS"
    RAW = "RAW"
    TIFF = "TIFF"
    TIFF_LZW = "TIFF_LZW"
    TIFF_ZIP = "TIFF_ZIP"
    XISF = "XISF"

    def __str__(self) -> str:
        return str(self.value)

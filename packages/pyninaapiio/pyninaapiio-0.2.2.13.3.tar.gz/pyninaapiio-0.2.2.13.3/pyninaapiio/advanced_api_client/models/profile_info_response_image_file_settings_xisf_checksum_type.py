from enum import Enum


class ProfileInfoResponseImageFileSettingsXISFChecksumType(str, Enum):
    NONE = "NONE"
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA3_256 = "SHA3_256"
    SHA3_512 = "SHA3_512"
    SHA512 = "SHA512"

    def __str__(self) -> str:
        return str(self.value)

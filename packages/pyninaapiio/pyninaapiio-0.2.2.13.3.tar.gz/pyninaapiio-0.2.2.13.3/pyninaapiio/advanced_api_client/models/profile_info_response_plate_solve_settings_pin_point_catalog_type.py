from enum import Enum


class ProfileInfoResponsePlateSolveSettingsPinPointCatalogType(str, Enum):
    PPATLAS = "ppAtlas"
    PPGSCACT = "ppGSCACT"
    PPTYCHO2 = "ppTycho2"
    PPUCAC2 = "ppUCAC2"
    PPUCAC3 = "ppUCAC3"
    PPUCAC4 = "ppUCAC4"
    PPUSNO_A = "ppUSNO_A"
    PPUSNO_B = "ppUSNO_B"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class GetEquipmentDomeSetFollowResponse200Response(str, Enum):
    FOLLOWING_DISABLED = "Following disabled"
    FOLLOWING_ENABLED = "Following enabled"

    def __str__(self) -> str:
        return str(self.value)

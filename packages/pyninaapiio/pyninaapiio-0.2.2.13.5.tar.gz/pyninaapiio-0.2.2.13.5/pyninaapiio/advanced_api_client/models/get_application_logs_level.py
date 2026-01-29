from enum import Enum


class GetApplicationLogsLevel(str, Enum):
    DEBUG = "DEBUG"
    ERROR = "ERROR"
    INFO = "INFO"
    TRACE = "TRACE"
    WARNING = "WARNING"

    def __str__(self) -> str:
        return str(self.value)

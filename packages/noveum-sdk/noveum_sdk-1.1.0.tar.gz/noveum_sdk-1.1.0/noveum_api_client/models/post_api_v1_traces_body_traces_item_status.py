from enum import Enum


class PostApiV1TracesBodyTracesItemStatus(str, Enum):
    ERROR = "error"
    OK = "ok"
    TIMEOUT = "timeout"

    def __str__(self) -> str:
        return str(self.value)

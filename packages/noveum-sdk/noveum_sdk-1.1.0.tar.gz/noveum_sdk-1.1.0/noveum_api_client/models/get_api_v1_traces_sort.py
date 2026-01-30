from enum import Enum


class GetApiV1TracesSort(str, Enum):
    DURATION_MSASC = "duration_ms:asc"
    DURATION_MSDESC = "duration_ms:desc"
    END_TIMEASC = "end_time:asc"
    END_TIMEDESC = "end_time:desc"
    START_TIMEASC = "start_time:asc"
    START_TIMEDESC = "start_time:desc"

    def __str__(self) -> str:
        return str(self.value)

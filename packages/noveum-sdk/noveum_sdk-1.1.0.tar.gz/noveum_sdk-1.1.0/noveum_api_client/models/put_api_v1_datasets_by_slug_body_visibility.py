from enum import Enum


class PutApiV1DatasetsBySlugBodyVisibility(str, Enum):
    ORG = "org"
    PRIVATE = "private"
    PUBLIC = "public"

    def __str__(self) -> str:
        return str(self.value)

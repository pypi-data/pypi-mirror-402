from enum import Enum


class PostApiV1DatasetsBodyVisibility(str, Enum):
    ORG = "org"
    PRIVATE = "private"
    PUBLIC = "public"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class GetApiV1DatasetsByDatasetSlugItemsSortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

    def __str__(self) -> str:
        return str(self.value)

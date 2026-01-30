from enum import Enum


class PostApiV1DatasetsBodyDatasetType(str, Enum):
    AGENT = "agent"
    CONVERSATIONAL = "conversational"
    CUSTOM = "custom"
    G_EVAL = "g-eval"

    def __str__(self) -> str:
        return str(self.value)

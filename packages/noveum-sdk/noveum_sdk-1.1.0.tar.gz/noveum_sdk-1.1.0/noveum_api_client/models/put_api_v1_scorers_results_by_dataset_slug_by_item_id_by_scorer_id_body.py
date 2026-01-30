from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.put_api_v1_scorers_results_by_dataset_slug_by_item_id_by_scorer_id_body_metadata import (
        PutApiV1ScorersResultsByDatasetSlugByItemIdByScorerIdBodyMetadata,
    )


T = TypeVar("T", bound="PutApiV1ScorersResultsByDatasetSlugByItemIdByScorerIdBody")


@_attrs_define
class PutApiV1ScorersResultsByDatasetSlugByItemIdByScorerIdBody:
    """
    Attributes:
        score (float | Unset):
        passed (bool | Unset):
        metadata (PutApiV1ScorersResultsByDatasetSlugByItemIdByScorerIdBodyMetadata | Unset):
        error (str | Unset):
        execution_time_ms (float | Unset):
    """

    score: float | Unset = UNSET
    passed: bool | Unset = UNSET
    metadata: PutApiV1ScorersResultsByDatasetSlugByItemIdByScorerIdBodyMetadata | Unset = UNSET
    error: str | Unset = UNSET
    execution_time_ms: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        score = self.score

        passed = self.passed

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        error = self.error

        execution_time_ms = self.execution_time_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if score is not UNSET:
            field_dict["score"] = score
        if passed is not UNSET:
            field_dict["passed"] = passed
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if error is not UNSET:
            field_dict["error"] = error
        if execution_time_ms is not UNSET:
            field_dict["executionTimeMs"] = execution_time_ms

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.put_api_v1_scorers_results_by_dataset_slug_by_item_id_by_scorer_id_body_metadata import (
            PutApiV1ScorersResultsByDatasetSlugByItemIdByScorerIdBodyMetadata,
        )

        d = dict(src_dict)
        score = d.pop("score", UNSET)

        passed = d.pop("passed", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: PutApiV1ScorersResultsByDatasetSlugByItemIdByScorerIdBodyMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PutApiV1ScorersResultsByDatasetSlugByItemIdByScorerIdBodyMetadata.from_dict(_metadata)

        error = d.pop("error", UNSET)

        execution_time_ms = d.pop("executionTimeMs", UNSET)

        put_api_v1_scorers_results_by_dataset_slug_by_item_id_by_scorer_id_body = cls(
            score=score,
            passed=passed,
            metadata=metadata,
            error=error,
            execution_time_ms=execution_time_ms,
        )

        put_api_v1_scorers_results_by_dataset_slug_by_item_id_by_scorer_id_body.additional_properties = d
        return put_api_v1_scorers_results_by_dataset_slug_by_item_id_by_scorer_id_body

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

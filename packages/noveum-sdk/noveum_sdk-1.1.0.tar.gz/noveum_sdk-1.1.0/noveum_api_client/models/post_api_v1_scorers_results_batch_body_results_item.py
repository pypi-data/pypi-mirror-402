from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_scorers_results_batch_body_results_item_metadata import (
        PostApiV1ScorersResultsBatchBodyResultsItemMetadata,
    )


T = TypeVar("T", bound="PostApiV1ScorersResultsBatchBodyResultsItem")


@_attrs_define
class PostApiV1ScorersResultsBatchBodyResultsItem:
    """
    Attributes:
        dataset_slug (str):
        item_id (str):
        scorer_id (str):
        score (float):
        passed (bool | Unset):  Default: False.
        metadata (PostApiV1ScorersResultsBatchBodyResultsItemMetadata | Unset):
        error (str | Unset):  Default: ''.
        execution_time_ms (float | Unset):  Default: 0.0.
    """

    dataset_slug: str
    item_id: str
    scorer_id: str
    score: float
    passed: bool | Unset = False
    metadata: PostApiV1ScorersResultsBatchBodyResultsItemMetadata | Unset = UNSET
    error: str | Unset = ""
    execution_time_ms: float | Unset = 0.0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_slug = self.dataset_slug

        item_id = self.item_id

        scorer_id = self.scorer_id

        score = self.score

        passed = self.passed

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        error = self.error

        execution_time_ms = self.execution_time_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "datasetSlug": dataset_slug,
                "itemId": item_id,
                "scorerId": scorer_id,
                "score": score,
            }
        )
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
        from ..models.post_api_v1_scorers_results_batch_body_results_item_metadata import (
            PostApiV1ScorersResultsBatchBodyResultsItemMetadata,
        )

        d = dict(src_dict)
        dataset_slug = d.pop("datasetSlug")

        item_id = d.pop("itemId")

        scorer_id = d.pop("scorerId")

        score = d.pop("score")

        passed = d.pop("passed", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: PostApiV1ScorersResultsBatchBodyResultsItemMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PostApiV1ScorersResultsBatchBodyResultsItemMetadata.from_dict(_metadata)

        error = d.pop("error", UNSET)

        execution_time_ms = d.pop("executionTimeMs", UNSET)

        post_api_v1_scorers_results_batch_body_results_item = cls(
            dataset_slug=dataset_slug,
            item_id=item_id,
            scorer_id=scorer_id,
            score=score,
            passed=passed,
            metadata=metadata,
            error=error,
            execution_time_ms=execution_time_ms,
        )

        post_api_v1_scorers_results_batch_body_results_item.additional_properties = d
        return post_api_v1_scorers_results_batch_body_results_item

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

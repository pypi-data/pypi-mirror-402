from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content import (
        PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContent,
    )
    from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_metadata import (
        PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemMetadata,
    )


T = TypeVar("T", bound="PostApiV1DatasetsByDatasetSlugItemsBodyItemsItem")


@_attrs_define
class PostApiV1DatasetsByDatasetSlugItemsBodyItemsItem:
    """
    Attributes:
        item_type (str):
        content (PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContent):
        item_id (str | Unset):
        metadata (PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemMetadata | Unset):
        trace_id (str | Unset):
        span_id (str | Unset):
    """

    item_type: str
    content: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContent
    item_id: str | Unset = UNSET
    metadata: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemMetadata | Unset = UNSET
    trace_id: str | Unset = UNSET
    span_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_type = self.item_type

        content = self.content.to_dict()

        item_id = self.item_id

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        trace_id = self.trace_id

        span_id = self.span_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "item_type": item_type,
                "content": content,
            }
        )
        if item_id is not UNSET:
            field_dict["item_id"] = item_id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if trace_id is not UNSET:
            field_dict["trace_id"] = trace_id
        if span_id is not UNSET:
            field_dict["span_id"] = span_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content import (
            PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContent,
        )
        from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_metadata import (
            PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemMetadata,
        )

        d = dict(src_dict)
        item_type = d.pop("item_type")

        content = PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContent.from_dict(d.pop("content"))

        item_id = d.pop("item_id", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemMetadata.from_dict(_metadata)

        trace_id = d.pop("trace_id", UNSET)

        span_id = d.pop("span_id", UNSET)

        post_api_v1_datasets_by_dataset_slug_items_body_items_item = cls(
            item_type=item_type,
            content=content,
            item_id=item_id,
            metadata=metadata,
            trace_id=trace_id,
            span_id=span_id,
        )

        post_api_v1_datasets_by_dataset_slug_items_body_items_item.additional_properties = d
        return post_api_v1_datasets_by_dataset_slug_items_body_items_item

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_traces_single_body_spans_item_links_item_attributes import (
        PostApiV1TracesSingleBodySpansItemLinksItemAttributes,
    )


T = TypeVar("T", bound="PostApiV1TracesSingleBodySpansItemLinksItem")


@_attrs_define
class PostApiV1TracesSingleBodySpansItemLinksItem:
    """
    Attributes:
        trace_id (str):
        span_id (str):
        attributes (PostApiV1TracesSingleBodySpansItemLinksItemAttributes | Unset):
    """

    trace_id: str
    span_id: str
    attributes: PostApiV1TracesSingleBodySpansItemLinksItemAttributes | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        trace_id = self.trace_id

        span_id = self.span_id

        attributes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "trace_id": trace_id,
                "span_id": span_id,
            }
        )
        if attributes is not UNSET:
            field_dict["attributes"] = attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_traces_single_body_spans_item_links_item_attributes import (
            PostApiV1TracesSingleBodySpansItemLinksItemAttributes,
        )

        d = dict(src_dict)
        trace_id = d.pop("trace_id")

        span_id = d.pop("span_id")

        _attributes = d.pop("attributes", UNSET)
        attributes: PostApiV1TracesSingleBodySpansItemLinksItemAttributes | Unset
        if isinstance(_attributes, Unset):
            attributes = UNSET
        else:
            attributes = PostApiV1TracesSingleBodySpansItemLinksItemAttributes.from_dict(_attributes)

        post_api_v1_traces_single_body_spans_item_links_item = cls(
            trace_id=trace_id,
            span_id=span_id,
            attributes=attributes,
        )

        post_api_v1_traces_single_body_spans_item_links_item.additional_properties = d
        return post_api_v1_traces_single_body_spans_item_links_item

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

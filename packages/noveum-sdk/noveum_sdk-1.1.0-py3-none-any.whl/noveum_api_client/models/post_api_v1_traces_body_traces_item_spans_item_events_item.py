from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_traces_body_traces_item_spans_item_events_item_attributes import (
        PostApiV1TracesBodyTracesItemSpansItemEventsItemAttributes,
    )


T = TypeVar("T", bound="PostApiV1TracesBodyTracesItemSpansItemEventsItem")


@_attrs_define
class PostApiV1TracesBodyTracesItemSpansItemEventsItem:
    """
    Attributes:
        name (str):
        timestamp (str):
        attributes (PostApiV1TracesBodyTracesItemSpansItemEventsItemAttributes | Unset):
    """

    name: str
    timestamp: str
    attributes: PostApiV1TracesBodyTracesItemSpansItemEventsItemAttributes | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        timestamp = self.timestamp

        attributes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "timestamp": timestamp,
            }
        )
        if attributes is not UNSET:
            field_dict["attributes"] = attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_traces_body_traces_item_spans_item_events_item_attributes import (
            PostApiV1TracesBodyTracesItemSpansItemEventsItemAttributes,
        )

        d = dict(src_dict)
        name = d.pop("name")

        timestamp = d.pop("timestamp")

        _attributes = d.pop("attributes", UNSET)
        attributes: PostApiV1TracesBodyTracesItemSpansItemEventsItemAttributes | Unset
        if isinstance(_attributes, Unset):
            attributes = UNSET
        else:
            attributes = PostApiV1TracesBodyTracesItemSpansItemEventsItemAttributes.from_dict(_attributes)

        post_api_v1_traces_body_traces_item_spans_item_events_item = cls(
            name=name,
            timestamp=timestamp,
            attributes=attributes,
        )

        post_api_v1_traces_body_traces_item_spans_item_events_item.additional_properties = d
        return post_api_v1_traces_body_traces_item_spans_item_events_item

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

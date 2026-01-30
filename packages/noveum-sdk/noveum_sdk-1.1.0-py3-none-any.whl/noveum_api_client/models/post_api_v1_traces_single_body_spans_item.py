from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_api_v1_traces_single_body_spans_item_status import PostApiV1TracesSingleBodySpansItemStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_traces_single_body_spans_item_attributes import (
        PostApiV1TracesSingleBodySpansItemAttributes,
    )
    from ..models.post_api_v1_traces_single_body_spans_item_events_item import (
        PostApiV1TracesSingleBodySpansItemEventsItem,
    )
    from ..models.post_api_v1_traces_single_body_spans_item_links_item import (
        PostApiV1TracesSingleBodySpansItemLinksItem,
    )


T = TypeVar("T", bound="PostApiV1TracesSingleBodySpansItem")


@_attrs_define
class PostApiV1TracesSingleBodySpansItem:
    """
    Attributes:
        span_id (str):
        trace_id (str):
        name (str):
        start_time (str):
        end_time (str):
        duration_ms (float):
        status (PostApiV1TracesSingleBodySpansItemStatus):
        parent_span_id (None | str | Unset):
        status_message (None | str | Unset):
        attributes (PostApiV1TracesSingleBodySpansItemAttributes | Unset):
        events (list[PostApiV1TracesSingleBodySpansItemEventsItem] | Unset):
        links (list[PostApiV1TracesSingleBodySpansItemLinksItem] | Unset):
    """

    span_id: str
    trace_id: str
    name: str
    start_time: str
    end_time: str
    duration_ms: float
    status: PostApiV1TracesSingleBodySpansItemStatus
    parent_span_id: None | str | Unset = UNSET
    status_message: None | str | Unset = UNSET
    attributes: PostApiV1TracesSingleBodySpansItemAttributes | Unset = UNSET
    events: list[PostApiV1TracesSingleBodySpansItemEventsItem] | Unset = UNSET
    links: list[PostApiV1TracesSingleBodySpansItemLinksItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        span_id = self.span_id

        trace_id = self.trace_id

        name = self.name

        start_time = self.start_time

        end_time = self.end_time

        duration_ms = self.duration_ms

        status = self.status.value

        parent_span_id: None | str | Unset
        if isinstance(self.parent_span_id, Unset):
            parent_span_id = UNSET
        else:
            parent_span_id = self.parent_span_id

        status_message: None | str | Unset
        if isinstance(self.status_message, Unset):
            status_message = UNSET
        else:
            status_message = self.status_message

        attributes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = self.attributes.to_dict()

        events: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.events, Unset):
            events = []
            for events_item_data in self.events:
                events_item = events_item_data.to_dict()
                events.append(events_item)

        links: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.links, Unset):
            links = []
            for links_item_data in self.links:
                links_item = links_item_data.to_dict()
                links.append(links_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "span_id": span_id,
                "trace_id": trace_id,
                "name": name,
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": duration_ms,
                "status": status,
            }
        )
        if parent_span_id is not UNSET:
            field_dict["parent_span_id"] = parent_span_id
        if status_message is not UNSET:
            field_dict["status_message"] = status_message
        if attributes is not UNSET:
            field_dict["attributes"] = attributes
        if events is not UNSET:
            field_dict["events"] = events
        if links is not UNSET:
            field_dict["links"] = links

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_traces_single_body_spans_item_attributes import (
            PostApiV1TracesSingleBodySpansItemAttributes,
        )
        from ..models.post_api_v1_traces_single_body_spans_item_events_item import (
            PostApiV1TracesSingleBodySpansItemEventsItem,
        )
        from ..models.post_api_v1_traces_single_body_spans_item_links_item import (
            PostApiV1TracesSingleBodySpansItemLinksItem,
        )

        d = dict(src_dict)
        span_id = d.pop("span_id")

        trace_id = d.pop("trace_id")

        name = d.pop("name")

        start_time = d.pop("start_time")

        end_time = d.pop("end_time")

        duration_ms = d.pop("duration_ms")

        status = PostApiV1TracesSingleBodySpansItemStatus(d.pop("status"))

        def _parse_parent_span_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_span_id = _parse_parent_span_id(d.pop("parent_span_id", UNSET))

        def _parse_status_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status_message = _parse_status_message(d.pop("status_message", UNSET))

        _attributes = d.pop("attributes", UNSET)
        attributes: PostApiV1TracesSingleBodySpansItemAttributes | Unset
        if isinstance(_attributes, Unset):
            attributes = UNSET
        else:
            attributes = PostApiV1TracesSingleBodySpansItemAttributes.from_dict(_attributes)

        _events = d.pop("events", UNSET)
        events: list[PostApiV1TracesSingleBodySpansItemEventsItem] | Unset = UNSET
        if _events is not UNSET:
            events = []
            for events_item_data in _events:
                events_item = PostApiV1TracesSingleBodySpansItemEventsItem.from_dict(events_item_data)

                events.append(events_item)

        _links = d.pop("links", UNSET)
        links: list[PostApiV1TracesSingleBodySpansItemLinksItem] | Unset = UNSET
        if _links is not UNSET:
            links = []
            for links_item_data in _links:
                links_item = PostApiV1TracesSingleBodySpansItemLinksItem.from_dict(links_item_data)

                links.append(links_item)

        post_api_v1_traces_single_body_spans_item = cls(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            status=status,
            parent_span_id=parent_span_id,
            status_message=status_message,
            attributes=attributes,
            events=events,
            links=links,
        )

        post_api_v1_traces_single_body_spans_item.additional_properties = d
        return post_api_v1_traces_single_body_spans_item

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

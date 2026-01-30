from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_api_v1_traces_single_body_status import PostApiV1TracesSingleBodyStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_traces_single_body_attributes import PostApiV1TracesSingleBodyAttributes
    from ..models.post_api_v1_traces_single_body_metadata import PostApiV1TracesSingleBodyMetadata
    from ..models.post_api_v1_traces_single_body_sdk import PostApiV1TracesSingleBodySdk
    from ..models.post_api_v1_traces_single_body_spans_item import PostApiV1TracesSingleBodySpansItem


T = TypeVar("T", bound="PostApiV1TracesSingleBody")


@_attrs_define
class PostApiV1TracesSingleBody:
    """
    Attributes:
        name (str):
        start_time (str):
        end_time (str):
        duration_ms (float):
        status (PostApiV1TracesSingleBodyStatus):
        span_count (int):
        project (str):
        sdk (PostApiV1TracesSingleBodySdk):
        spans (list[PostApiV1TracesSingleBodySpansItem]):
        trace_id (str | Unset):
        status_message (None | str | Unset):
        error_count (int | Unset):  Default: 0.
        environment (str | Unset):  Default: 'production'.
        attributes (PostApiV1TracesSingleBodyAttributes | Unset):
        metadata (PostApiV1TracesSingleBodyMetadata | Unset):
    """

    name: str
    start_time: str
    end_time: str
    duration_ms: float
    status: PostApiV1TracesSingleBodyStatus
    span_count: int
    project: str
    sdk: PostApiV1TracesSingleBodySdk
    spans: list[PostApiV1TracesSingleBodySpansItem]
    trace_id: str | Unset = UNSET
    status_message: None | str | Unset = UNSET
    error_count: int | Unset = 0
    environment: str | Unset = "production"
    attributes: PostApiV1TracesSingleBodyAttributes | Unset = UNSET
    metadata: PostApiV1TracesSingleBodyMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        start_time = self.start_time

        end_time = self.end_time

        duration_ms = self.duration_ms

        status = self.status.value

        span_count = self.span_count

        project = self.project

        sdk = self.sdk.to_dict()

        spans = []
        for spans_item_data in self.spans:
            spans_item = spans_item_data.to_dict()
            spans.append(spans_item)

        trace_id = self.trace_id

        status_message: None | str | Unset
        if isinstance(self.status_message, Unset):
            status_message = UNSET
        else:
            status_message = self.status_message

        error_count = self.error_count

        environment = self.environment

        attributes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = self.attributes.to_dict()

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": duration_ms,
                "status": status,
                "span_count": span_count,
                "project": project,
                "sdk": sdk,
                "spans": spans,
            }
        )
        if trace_id is not UNSET:
            field_dict["trace_id"] = trace_id
        if status_message is not UNSET:
            field_dict["status_message"] = status_message
        if error_count is not UNSET:
            field_dict["error_count"] = error_count
        if environment is not UNSET:
            field_dict["environment"] = environment
        if attributes is not UNSET:
            field_dict["attributes"] = attributes
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_traces_single_body_attributes import PostApiV1TracesSingleBodyAttributes
        from ..models.post_api_v1_traces_single_body_metadata import PostApiV1TracesSingleBodyMetadata
        from ..models.post_api_v1_traces_single_body_sdk import PostApiV1TracesSingleBodySdk
        from ..models.post_api_v1_traces_single_body_spans_item import PostApiV1TracesSingleBodySpansItem

        d = dict(src_dict)
        name = d.pop("name")

        start_time = d.pop("start_time")

        end_time = d.pop("end_time")

        duration_ms = d.pop("duration_ms")

        status = PostApiV1TracesSingleBodyStatus(d.pop("status"))

        span_count = d.pop("span_count")

        project = d.pop("project")

        sdk = PostApiV1TracesSingleBodySdk.from_dict(d.pop("sdk"))

        spans = []
        _spans = d.pop("spans")
        for spans_item_data in _spans:
            spans_item = PostApiV1TracesSingleBodySpansItem.from_dict(spans_item_data)

            spans.append(spans_item)

        trace_id = d.pop("trace_id", UNSET)

        def _parse_status_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status_message = _parse_status_message(d.pop("status_message", UNSET))

        error_count = d.pop("error_count", UNSET)

        environment = d.pop("environment", UNSET)

        _attributes = d.pop("attributes", UNSET)
        attributes: PostApiV1TracesSingleBodyAttributes | Unset
        if isinstance(_attributes, Unset):
            attributes = UNSET
        else:
            attributes = PostApiV1TracesSingleBodyAttributes.from_dict(_attributes)

        _metadata = d.pop("metadata", UNSET)
        metadata: PostApiV1TracesSingleBodyMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PostApiV1TracesSingleBodyMetadata.from_dict(_metadata)

        post_api_v1_traces_single_body = cls(
            name=name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            status=status,
            span_count=span_count,
            project=project,
            sdk=sdk,
            spans=spans,
            trace_id=trace_id,
            status_message=status_message,
            error_count=error_count,
            environment=environment,
            attributes=attributes,
            metadata=metadata,
        )

        post_api_v1_traces_single_body.additional_properties = d
        return post_api_v1_traces_single_body

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

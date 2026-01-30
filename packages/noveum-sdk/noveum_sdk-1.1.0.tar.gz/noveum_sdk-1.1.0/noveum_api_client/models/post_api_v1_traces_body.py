from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_traces_body_traces_item import PostApiV1TracesBodyTracesItem


T = TypeVar("T", bound="PostApiV1TracesBody")


@_attrs_define
class PostApiV1TracesBody:
    """
    Attributes:
        traces (list[PostApiV1TracesBodyTracesItem]):
        timestamp (float | Unset):
    """

    traces: list[PostApiV1TracesBodyTracesItem]
    timestamp: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        traces = []
        for traces_item_data in self.traces:
            traces_item = traces_item_data.to_dict()
            traces.append(traces_item)

        timestamp = self.timestamp

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "traces": traces,
            }
        )
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_traces_body_traces_item import PostApiV1TracesBodyTracesItem

        d = dict(src_dict)
        traces = []
        _traces = d.pop("traces")
        for traces_item_data in _traces:
            traces_item = PostApiV1TracesBodyTracesItem.from_dict(traces_item_data)

            traces.append(traces_item)

        timestamp = d.pop("timestamp", UNSET)

        post_api_v1_traces_body = cls(
            traces=traces,
            timestamp=timestamp,
        )

        post_api_v1_traces_body.additional_properties = d
        return post_api_v1_traces_body

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

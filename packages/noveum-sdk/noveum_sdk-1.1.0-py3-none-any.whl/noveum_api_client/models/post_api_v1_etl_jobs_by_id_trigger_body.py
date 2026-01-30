from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_etl_jobs_by_id_trigger_body_filter_config import (
        PostApiV1EtlJobsByIdTriggerBodyFilterConfig,
    )


T = TypeVar("T", bound="PostApiV1EtlJobsByIdTriggerBody")


@_attrs_define
class PostApiV1EtlJobsByIdTriggerBody:
    """
    Attributes:
        trace_ids (list[str] | Unset):
        filter_config (PostApiV1EtlJobsByIdTriggerBodyFilterConfig | Unset):
        dataset_slug (str | Unset):
    """

    trace_ids: list[str] | Unset = UNSET
    filter_config: PostApiV1EtlJobsByIdTriggerBodyFilterConfig | Unset = UNSET
    dataset_slug: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        trace_ids: list[str] | Unset = UNSET
        if not isinstance(self.trace_ids, Unset):
            trace_ids = self.trace_ids

        filter_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filter_config, Unset):
            filter_config = self.filter_config.to_dict()

        dataset_slug = self.dataset_slug

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if trace_ids is not UNSET:
            field_dict["traceIds"] = trace_ids
        if filter_config is not UNSET:
            field_dict["filterConfig"] = filter_config
        if dataset_slug is not UNSET:
            field_dict["datasetSlug"] = dataset_slug

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_etl_jobs_by_id_trigger_body_filter_config import (
            PostApiV1EtlJobsByIdTriggerBodyFilterConfig,
        )

        d = dict(src_dict)
        trace_ids = cast(list[str], d.pop("traceIds", UNSET))

        _filter_config = d.pop("filterConfig", UNSET)
        filter_config: PostApiV1EtlJobsByIdTriggerBodyFilterConfig | Unset
        if isinstance(_filter_config, Unset):
            filter_config = UNSET
        else:
            filter_config = PostApiV1EtlJobsByIdTriggerBodyFilterConfig.from_dict(_filter_config)

        dataset_slug = d.pop("datasetSlug", UNSET)

        post_api_v1_etl_jobs_by_id_trigger_body = cls(
            trace_ids=trace_ids,
            filter_config=filter_config,
            dataset_slug=dataset_slug,
        )

        post_api_v1_etl_jobs_by_id_trigger_body.additional_properties = d
        return post_api_v1_etl_jobs_by_id_trigger_body

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

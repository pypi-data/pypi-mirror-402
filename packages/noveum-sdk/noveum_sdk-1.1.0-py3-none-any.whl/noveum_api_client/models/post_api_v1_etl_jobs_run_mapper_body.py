from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PostApiV1EtlJobsRunMapperBody")


@_attrs_define
class PostApiV1EtlJobsRunMapperBody:
    """
    Attributes:
        mapper_code (str):
        trace_id (str):
    """

    mapper_code: str
    trace_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mapper_code = self.mapper_code

        trace_id = self.trace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mapperCode": mapper_code,
                "traceId": trace_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        mapper_code = d.pop("mapperCode")

        trace_id = d.pop("traceId")

        post_api_v1_etl_jobs_run_mapper_body = cls(
            mapper_code=mapper_code,
            trace_id=trace_id,
        )

        post_api_v1_etl_jobs_run_mapper_body.additional_properties = d
        return post_api_v1_etl_jobs_run_mapper_body

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

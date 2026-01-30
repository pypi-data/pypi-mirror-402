from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostApiV1EtlJobsRunMapperResponse200")


@_attrs_define
class PostApiV1EtlJobsRunMapperResponse200:
    """
    Attributes:
        success (bool):
        execution_time (float):
        output (Any | Unset):
        error (str | Unset):
    """

    success: bool
    execution_time: float
    output: Any | Unset = UNSET
    error: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        execution_time = self.execution_time

        output = self.output

        error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
                "executionTime": execution_time,
            }
        )
        if output is not UNSET:
            field_dict["output"] = output
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        success = d.pop("success")

        execution_time = d.pop("executionTime")

        output = d.pop("output", UNSET)

        error = d.pop("error", UNSET)

        post_api_v1_etl_jobs_run_mapper_response_200 = cls(
            success=success,
            execution_time=execution_time,
            output=output,
            error=error,
        )

        post_api_v1_etl_jobs_run_mapper_response_200.additional_properties = d
        return post_api_v1_etl_jobs_run_mapper_response_200

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostApiV1EtlJobsByIdTriggerBodyFilterConfig")


@_attrs_define
class PostApiV1EtlJobsByIdTriggerBodyFilterConfig:
    """
    Attributes:
        start_date (str | Unset):
        end_date (str | Unset):
        project_id (str | Unset):
    """

    start_date: str | Unset = UNSET
    end_date: str | Unset = UNSET
    project_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        start_date = self.start_date

        end_date = self.end_date

        project_id = self.project_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if start_date is not UNSET:
            field_dict["startDate"] = start_date
        if end_date is not UNSET:
            field_dict["endDate"] = end_date
        if project_id is not UNSET:
            field_dict["projectId"] = project_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        start_date = d.pop("startDate", UNSET)

        end_date = d.pop("endDate", UNSET)

        project_id = d.pop("projectId", UNSET)

        post_api_v1_etl_jobs_by_id_trigger_body_filter_config = cls(
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
        )

        post_api_v1_etl_jobs_by_id_trigger_body_filter_config.additional_properties = d
        return post_api_v1_etl_jobs_by_id_trigger_body_filter_config

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

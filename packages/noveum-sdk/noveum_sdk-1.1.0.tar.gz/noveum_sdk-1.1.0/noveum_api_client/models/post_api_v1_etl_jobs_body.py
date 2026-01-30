from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostApiV1EtlJobsBody")


@_attrs_define
class PostApiV1EtlJobsBody:
    """
    Attributes:
        name (str):
        project_id (str):
        dataset_slug (str):
        environment (str):
        is_enabled (bool | Unset):  Default: True.
        mapper_code (str | Unset):
        is_configuration_done (bool | Unset):  Default: False.
    """

    name: str
    project_id: str
    dataset_slug: str
    environment: str
    is_enabled: bool | Unset = True
    mapper_code: str | Unset = UNSET
    is_configuration_done: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        project_id = self.project_id

        dataset_slug = self.dataset_slug

        environment = self.environment

        is_enabled = self.is_enabled

        mapper_code = self.mapper_code

        is_configuration_done = self.is_configuration_done

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "projectId": project_id,
                "datasetSlug": dataset_slug,
                "environment": environment,
            }
        )
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled
        if mapper_code is not UNSET:
            field_dict["mapperCode"] = mapper_code
        if is_configuration_done is not UNSET:
            field_dict["isConfigurationDone"] = is_configuration_done

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        project_id = d.pop("projectId")

        dataset_slug = d.pop("datasetSlug")

        environment = d.pop("environment")

        is_enabled = d.pop("isEnabled", UNSET)

        mapper_code = d.pop("mapperCode", UNSET)

        is_configuration_done = d.pop("isConfigurationDone", UNSET)

        post_api_v1_etl_jobs_body = cls(
            name=name,
            project_id=project_id,
            dataset_slug=dataset_slug,
            environment=environment,
            is_enabled=is_enabled,
            mapper_code=mapper_code,
            is_configuration_done=is_configuration_done,
        )

        post_api_v1_etl_jobs_body.additional_properties = d
        return post_api_v1_etl_jobs_body

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

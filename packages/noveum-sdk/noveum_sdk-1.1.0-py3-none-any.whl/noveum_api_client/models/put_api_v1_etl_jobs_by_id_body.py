from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PutApiV1EtlJobsByIdBody")


@_attrs_define
class PutApiV1EtlJobsByIdBody:
    """
    Attributes:
        name (str | Unset):
        project_id (str | Unset):
        dataset_slug (str | Unset):
        is_enabled (bool | Unset):
        mapper_code (str | Unset):
        is_configuration_done (bool | Unset):
        environment (str | Unset):
    """

    name: str | Unset = UNSET
    project_id: str | Unset = UNSET
    dataset_slug: str | Unset = UNSET
    is_enabled: bool | Unset = UNSET
    mapper_code: str | Unset = UNSET
    is_configuration_done: bool | Unset = UNSET
    environment: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        project_id = self.project_id

        dataset_slug = self.dataset_slug

        is_enabled = self.is_enabled

        mapper_code = self.mapper_code

        is_configuration_done = self.is_configuration_done

        environment = self.environment

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if project_id is not UNSET:
            field_dict["projectId"] = project_id
        if dataset_slug is not UNSET:
            field_dict["datasetSlug"] = dataset_slug
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled
        if mapper_code is not UNSET:
            field_dict["mapperCode"] = mapper_code
        if is_configuration_done is not UNSET:
            field_dict["isConfigurationDone"] = is_configuration_done
        if environment is not UNSET:
            field_dict["environment"] = environment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        project_id = d.pop("projectId", UNSET)

        dataset_slug = d.pop("datasetSlug", UNSET)

        is_enabled = d.pop("isEnabled", UNSET)

        mapper_code = d.pop("mapperCode", UNSET)

        is_configuration_done = d.pop("isConfigurationDone", UNSET)

        environment = d.pop("environment", UNSET)

        put_api_v1_etl_jobs_by_id_body = cls(
            name=name,
            project_id=project_id,
            dataset_slug=dataset_slug,
            is_enabled=is_enabled,
            mapper_code=mapper_code,
            is_configuration_done=is_configuration_done,
            environment=environment,
        )

        put_api_v1_etl_jobs_by_id_body.additional_properties = d
        return put_api_v1_etl_jobs_by_id_body

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

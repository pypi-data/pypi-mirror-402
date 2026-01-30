from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GetApiV1EtlJobsByIdResponse200")


@_attrs_define
class GetApiV1EtlJobsByIdResponse200:
    """
    Attributes:
        id (str):
        name (str):
        project_id (str):
        dataset_slug (str):
        organization_id (str):
        is_enabled (bool):
        mapper_code (None | str):
        user_id (str):
        is_configuration_done (bool):
        environment (str):
        created_at (str):
        updated_at (str):
    """

    id: str
    name: str
    project_id: str
    dataset_slug: str
    organization_id: str
    is_enabled: bool
    mapper_code: None | str
    user_id: str
    is_configuration_done: bool
    environment: str
    created_at: str
    updated_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        project_id = self.project_id

        dataset_slug = self.dataset_slug

        organization_id = self.organization_id

        is_enabled = self.is_enabled

        mapper_code: None | str
        mapper_code = self.mapper_code

        user_id = self.user_id

        is_configuration_done = self.is_configuration_done

        environment = self.environment

        created_at = self.created_at

        updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "projectId": project_id,
                "datasetSlug": dataset_slug,
                "organizationId": organization_id,
                "isEnabled": is_enabled,
                "mapperCode": mapper_code,
                "userId": user_id,
                "isConfigurationDone": is_configuration_done,
                "environment": environment,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        project_id = d.pop("projectId")

        dataset_slug = d.pop("datasetSlug")

        organization_id = d.pop("organizationId")

        is_enabled = d.pop("isEnabled")

        def _parse_mapper_code(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        mapper_code = _parse_mapper_code(d.pop("mapperCode"))

        user_id = d.pop("userId")

        is_configuration_done = d.pop("isConfigurationDone")

        environment = d.pop("environment")

        created_at = d.pop("createdAt")

        updated_at = d.pop("updatedAt")

        get_api_v1_etl_jobs_by_id_response_200 = cls(
            id=id,
            name=name,
            project_id=project_id,
            dataset_slug=dataset_slug,
            organization_id=organization_id,
            is_enabled=is_enabled,
            mapper_code=mapper_code,
            user_id=user_id,
            is_configuration_done=is_configuration_done,
            environment=environment,
            created_at=created_at,
            updated_at=updated_at,
        )

        get_api_v1_etl_jobs_by_id_response_200.additional_properties = d
        return get_api_v1_etl_jobs_by_id_response_200

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

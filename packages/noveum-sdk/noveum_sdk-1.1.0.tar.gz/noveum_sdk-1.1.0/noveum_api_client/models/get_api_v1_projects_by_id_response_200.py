from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetApiV1ProjectsByIdResponse200")


@_attrs_define
class GetApiV1ProjectsByIdResponse200:
    """
    Attributes:
        id (str):
        name (str):
        description (str):
        organization_id (str):
        created_at (str):
        updated_at (str):
        environments (list[str] | Unset):
        trace_count (float | Unset):
    """

    id: str
    name: str
    description: str
    organization_id: str
    created_at: str
    updated_at: str
    environments: list[str] | Unset = UNSET
    trace_count: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        description = self.description

        organization_id = self.organization_id

        created_at = self.created_at

        updated_at = self.updated_at

        environments: list[str] | Unset = UNSET
        if not isinstance(self.environments, Unset):
            environments = self.environments

        trace_count = self.trace_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "organizationId": organization_id,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )
        if environments is not UNSET:
            field_dict["environments"] = environments
        if trace_count is not UNSET:
            field_dict["traceCount"] = trace_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        description = d.pop("description")

        organization_id = d.pop("organizationId")

        created_at = d.pop("createdAt")

        updated_at = d.pop("updatedAt")

        environments = cast(list[str], d.pop("environments", UNSET))

        trace_count = d.pop("traceCount", UNSET)

        get_api_v1_projects_by_id_response_200 = cls(
            id=id,
            name=name,
            description=description,
            organization_id=organization_id,
            created_at=created_at,
            updated_at=updated_at,
            environments=environments,
            trace_count=trace_count,
        )

        get_api_v1_projects_by_id_response_200.additional_properties = d
        return get_api_v1_projects_by_id_response_200

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetApiV1ScorersByIdResponse200")


@_attrs_define
class GetApiV1ScorersByIdResponse200:
    """
    Attributes:
        id (str):
        name (str):
        description (str):
        type_ (str):
        tag (str):
        is_default (bool):
        created_at (str):
        updated_at (str):
        config (Any | Unset):
        schema (Any | Unset):
        input_schema (Any | Unset):
        output_schema (Any | Unset):
    """

    id: str
    name: str
    description: str
    type_: str
    tag: str
    is_default: bool
    created_at: str
    updated_at: str
    config: Any | Unset = UNSET
    schema: Any | Unset = UNSET
    input_schema: Any | Unset = UNSET
    output_schema: Any | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        description = self.description

        type_ = self.type_

        tag = self.tag

        is_default = self.is_default

        created_at = self.created_at

        updated_at = self.updated_at

        config = self.config

        schema = self.schema

        input_schema = self.input_schema

        output_schema = self.output_schema

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "tag": tag,
                "isDefault": is_default,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )
        if config is not UNSET:
            field_dict["config"] = config
        if schema is not UNSET:
            field_dict["schema"] = schema
        if input_schema is not UNSET:
            field_dict["inputSchema"] = input_schema
        if output_schema is not UNSET:
            field_dict["outputSchema"] = output_schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        description = d.pop("description")

        type_ = d.pop("type")

        tag = d.pop("tag")

        is_default = d.pop("isDefault")

        created_at = d.pop("createdAt")

        updated_at = d.pop("updatedAt")

        config = d.pop("config", UNSET)

        schema = d.pop("schema", UNSET)

        input_schema = d.pop("inputSchema", UNSET)

        output_schema = d.pop("outputSchema", UNSET)

        get_api_v1_scorers_by_id_response_200 = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            tag=tag,
            is_default=is_default,
            created_at=created_at,
            updated_at=updated_at,
            config=config,
            schema=schema,
            input_schema=input_schema,
            output_schema=output_schema,
        )

        get_api_v1_scorers_by_id_response_200.additional_properties = d
        return get_api_v1_scorers_by_id_response_200

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

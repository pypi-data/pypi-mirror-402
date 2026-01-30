from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PutApiV1ScorersByIdBody")


@_attrs_define
class PutApiV1ScorersByIdBody:
    """
    Attributes:
        name (str | Unset):
        description (str | Unset):
        type_ (str | Unset):
        tag (str | Unset):
        config (Any | Unset):
        schema (Any | Unset):
        input_schema (Any | Unset):
        output_schema (Any | Unset):
        is_default (bool | Unset):
    """

    name: str | Unset = UNSET
    description: str | Unset = UNSET
    type_: str | Unset = UNSET
    tag: str | Unset = UNSET
    config: Any | Unset = UNSET
    schema: Any | Unset = UNSET
    input_schema: Any | Unset = UNSET
    output_schema: Any | Unset = UNSET
    is_default: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_

        tag = self.tag

        config = self.config

        schema = self.schema

        input_schema = self.input_schema

        output_schema = self.output_schema

        is_default = self.is_default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if type_ is not UNSET:
            field_dict["type"] = type_
        if tag is not UNSET:
            field_dict["tag"] = tag
        if config is not UNSET:
            field_dict["config"] = config
        if schema is not UNSET:
            field_dict["schema"] = schema
        if input_schema is not UNSET:
            field_dict["inputSchema"] = input_schema
        if output_schema is not UNSET:
            field_dict["outputSchema"] = output_schema
        if is_default is not UNSET:
            field_dict["isDefault"] = is_default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        type_ = d.pop("type", UNSET)

        tag = d.pop("tag", UNSET)

        config = d.pop("config", UNSET)

        schema = d.pop("schema", UNSET)

        input_schema = d.pop("inputSchema", UNSET)

        output_schema = d.pop("outputSchema", UNSET)

        is_default = d.pop("isDefault", UNSET)

        put_api_v1_scorers_by_id_body = cls(
            name=name,
            description=description,
            type_=type_,
            tag=tag,
            config=config,
            schema=schema,
            input_schema=input_schema,
            output_schema=output_schema,
            is_default=is_default,
        )

        put_api_v1_scorers_by_id_body.additional_properties = d
        return put_api_v1_scorers_by_id_body

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

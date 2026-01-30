from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostApiV1ScorersBody")


@_attrs_define
class PostApiV1ScorersBody:
    """
    Attributes:
        name (str):
        description (str):
        type_ (str):
        tag (str):
        config (Any | Unset):
        schema (Any | Unset):
        input_schema (Any | Unset):
        output_schema (Any | Unset):
        is_default (bool | Unset):  Default: False.
    """

    name: str
    description: str
    type_: str
    tag: str
    config: Any | Unset = UNSET
    schema: Any | Unset = UNSET
    input_schema: Any | Unset = UNSET
    output_schema: Any | Unset = UNSET
    is_default: bool | Unset = False
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
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "tag": tag,
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
        if is_default is not UNSET:
            field_dict["isDefault"] = is_default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = d.pop("type")

        tag = d.pop("tag")

        config = d.pop("config", UNSET)

        schema = d.pop("schema", UNSET)

        input_schema = d.pop("inputSchema", UNSET)

        output_schema = d.pop("outputSchema", UNSET)

        is_default = d.pop("isDefault", UNSET)

        post_api_v1_scorers_body = cls(
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

        post_api_v1_scorers_body.additional_properties = d
        return post_api_v1_scorers_body

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

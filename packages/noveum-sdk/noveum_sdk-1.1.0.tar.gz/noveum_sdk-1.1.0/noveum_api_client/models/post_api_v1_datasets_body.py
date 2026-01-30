from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_api_v1_datasets_body_dataset_type import PostApiV1DatasetsBodyDatasetType
from ..models.post_api_v1_datasets_body_visibility import PostApiV1DatasetsBodyVisibility
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_datasets_body_custom_attributes import PostApiV1DatasetsBodyCustomAttributes


T = TypeVar("T", bound="PostApiV1DatasetsBody")


@_attrs_define
class PostApiV1DatasetsBody:
    """
    Attributes:
        name (str):
        slug (str | Unset):
        description (str | Unset):
        visibility (PostApiV1DatasetsBodyVisibility | Unset):  Default: PostApiV1DatasetsBodyVisibility.ORG.
        dataset_type (PostApiV1DatasetsBodyDatasetType | Unset):  Default: PostApiV1DatasetsBodyDatasetType.CUSTOM.
        environment (str | Unset):
        schema_version (str | Unset):
        tags (list[str] | Unset):
        custom_attributes (PostApiV1DatasetsBodyCustomAttributes | Unset):
    """

    name: str
    slug: str | Unset = UNSET
    description: str | Unset = UNSET
    visibility: PostApiV1DatasetsBodyVisibility | Unset = PostApiV1DatasetsBodyVisibility.ORG
    dataset_type: PostApiV1DatasetsBodyDatasetType | Unset = PostApiV1DatasetsBodyDatasetType.CUSTOM
    environment: str | Unset = UNSET
    schema_version: str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    custom_attributes: PostApiV1DatasetsBodyCustomAttributes | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        description = self.description

        visibility: str | Unset = UNSET
        if not isinstance(self.visibility, Unset):
            visibility = self.visibility.value

        dataset_type: str | Unset = UNSET
        if not isinstance(self.dataset_type, Unset):
            dataset_type = self.dataset_type.value

        environment = self.environment

        schema_version = self.schema_version

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        custom_attributes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.custom_attributes, Unset):
            custom_attributes = self.custom_attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug
        if description is not UNSET:
            field_dict["description"] = description
        if visibility is not UNSET:
            field_dict["visibility"] = visibility
        if dataset_type is not UNSET:
            field_dict["dataset_type"] = dataset_type
        if environment is not UNSET:
            field_dict["environment"] = environment
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if tags is not UNSET:
            field_dict["tags"] = tags
        if custom_attributes is not UNSET:
            field_dict["custom_attributes"] = custom_attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_datasets_body_custom_attributes import PostApiV1DatasetsBodyCustomAttributes

        d = dict(src_dict)
        name = d.pop("name")

        slug = d.pop("slug", UNSET)

        description = d.pop("description", UNSET)

        _visibility = d.pop("visibility", UNSET)
        visibility: PostApiV1DatasetsBodyVisibility | Unset
        if isinstance(_visibility, Unset):
            visibility = UNSET
        else:
            visibility = PostApiV1DatasetsBodyVisibility(_visibility)

        _dataset_type = d.pop("dataset_type", UNSET)
        dataset_type: PostApiV1DatasetsBodyDatasetType | Unset
        if isinstance(_dataset_type, Unset):
            dataset_type = UNSET
        else:
            dataset_type = PostApiV1DatasetsBodyDatasetType(_dataset_type)

        environment = d.pop("environment", UNSET)

        schema_version = d.pop("schema_version", UNSET)

        tags = cast(list[str], d.pop("tags", UNSET))

        _custom_attributes = d.pop("custom_attributes", UNSET)
        custom_attributes: PostApiV1DatasetsBodyCustomAttributes | Unset
        if isinstance(_custom_attributes, Unset):
            custom_attributes = UNSET
        else:
            custom_attributes = PostApiV1DatasetsBodyCustomAttributes.from_dict(_custom_attributes)

        post_api_v1_datasets_body = cls(
            name=name,
            slug=slug,
            description=description,
            visibility=visibility,
            dataset_type=dataset_type,
            environment=environment,
            schema_version=schema_version,
            tags=tags,
            custom_attributes=custom_attributes,
        )

        post_api_v1_datasets_body.additional_properties = d
        return post_api_v1_datasets_body

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

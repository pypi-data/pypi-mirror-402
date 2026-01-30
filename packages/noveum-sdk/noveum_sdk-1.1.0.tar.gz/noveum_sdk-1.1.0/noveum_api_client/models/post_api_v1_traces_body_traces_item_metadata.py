from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_traces_body_traces_item_metadata_custom_attributes import (
        PostApiV1TracesBodyTracesItemMetadataCustomAttributes,
    )
    from ..models.post_api_v1_traces_body_traces_item_metadata_tags import PostApiV1TracesBodyTracesItemMetadataTags


T = TypeVar("T", bound="PostApiV1TracesBodyTracesItemMetadata")


@_attrs_define
class PostApiV1TracesBodyTracesItemMetadata:
    """
    Attributes:
        user_id (None | str | Unset):
        session_id (None | str | Unset):
        request_id (None | str | Unset):
        tags (PostApiV1TracesBodyTracesItemMetadataTags | Unset):
        custom_attributes (PostApiV1TracesBodyTracesItemMetadataCustomAttributes | Unset):
    """

    user_id: None | str | Unset = UNSET
    session_id: None | str | Unset = UNSET
    request_id: None | str | Unset = UNSET
    tags: PostApiV1TracesBodyTracesItemMetadataTags | Unset = UNSET
    custom_attributes: PostApiV1TracesBodyTracesItemMetadataCustomAttributes | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        session_id: None | str | Unset
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        else:
            session_id = self.session_id

        request_id: None | str | Unset
        if isinstance(self.request_id, Unset):
            request_id = UNSET
        else:
            request_id = self.request_id

        tags: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        custom_attributes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.custom_attributes, Unset):
            custom_attributes = self.custom_attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if request_id is not UNSET:
            field_dict["request_id"] = request_id
        if tags is not UNSET:
            field_dict["tags"] = tags
        if custom_attributes is not UNSET:
            field_dict["custom_attributes"] = custom_attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_traces_body_traces_item_metadata_custom_attributes import (
            PostApiV1TracesBodyTracesItemMetadataCustomAttributes,
        )
        from ..models.post_api_v1_traces_body_traces_item_metadata_tags import PostApiV1TracesBodyTracesItemMetadataTags

        d = dict(src_dict)

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_session_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_id = _parse_session_id(d.pop("session_id", UNSET))

        def _parse_request_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        request_id = _parse_request_id(d.pop("request_id", UNSET))

        _tags = d.pop("tags", UNSET)
        tags: PostApiV1TracesBodyTracesItemMetadataTags | Unset
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = PostApiV1TracesBodyTracesItemMetadataTags.from_dict(_tags)

        _custom_attributes = d.pop("custom_attributes", UNSET)
        custom_attributes: PostApiV1TracesBodyTracesItemMetadataCustomAttributes | Unset
        if isinstance(_custom_attributes, Unset):
            custom_attributes = UNSET
        else:
            custom_attributes = PostApiV1TracesBodyTracesItemMetadataCustomAttributes.from_dict(_custom_attributes)

        post_api_v1_traces_body_traces_item_metadata = cls(
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            tags=tags,
            custom_attributes=custom_attributes,
        )

        post_api_v1_traces_body_traces_item_metadata.additional_properties = d
        return post_api_v1_traces_body_traces_item_metadata

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

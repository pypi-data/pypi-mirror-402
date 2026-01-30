from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_v1_datasets_visibility import GetApiV1DatasetsVisibility
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: float | Unset = 20.0,
    offset: float | Unset = 0.0,
    visibility: GetApiV1DatasetsVisibility | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
    include_versions: bool | Unset = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["offset"] = offset

    json_visibility: str | Unset = UNSET
    if not isinstance(visibility, Unset):
        json_visibility = visibility.value

    params["visibility"] = json_visibility

    params["organizationSlug"] = organization_slug

    params["includeVersions"] = include_versions

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/datasets",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 200:
        return None

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: float | Unset = 20.0,
    offset: float | Unset = 0.0,
    visibility: GetApiV1DatasetsVisibility | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
    include_versions: bool | Unset = False,
) -> Response[Any]:
    """List datasets

    Args:
        limit (float | Unset):  Default: 20.0.
        offset (float | Unset):  Default: 0.0.
        visibility (GetApiV1DatasetsVisibility | Unset):
        organization_slug (str | Unset):
        include_versions (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        visibility=visibility,
        organization_slug=organization_slug,
        include_versions=include_versions,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: float | Unset = 20.0,
    offset: float | Unset = 0.0,
    visibility: GetApiV1DatasetsVisibility | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
    include_versions: bool | Unset = False,
) -> Response[Any]:
    """List datasets

    Args:
        limit (float | Unset):  Default: 20.0.
        offset (float | Unset):  Default: 0.0.
        visibility (GetApiV1DatasetsVisibility | Unset):
        organization_slug (str | Unset):
        include_versions (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        visibility=visibility,
        organization_slug=organization_slug,
        include_versions=include_versions,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)

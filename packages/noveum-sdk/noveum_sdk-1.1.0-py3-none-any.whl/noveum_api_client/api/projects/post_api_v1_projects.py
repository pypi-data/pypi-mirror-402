from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_api_v1_projects_body import PostApiV1ProjectsBody
from ...models.post_api_v1_projects_response_201 import PostApiV1ProjectsResponse201
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: PostApiV1ProjectsBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["organizationId"] = organization_id

    params["organizationSlug"] = organization_slug

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/projects",
        "params": params,
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | PostApiV1ProjectsResponse201 | None:
    if response.status_code == 201:
        response_201 = PostApiV1ProjectsResponse201.from_dict(response.json())

        return response_201

    if response.status_code == 409:
        response_409 = cast(Any, None)
        return response_409

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | PostApiV1ProjectsResponse201]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostApiV1ProjectsBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Response[Any | PostApiV1ProjectsResponse201]:
    """Create a new project

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        body (PostApiV1ProjectsBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PostApiV1ProjectsResponse201]
    """

    kwargs = _get_kwargs(
        body=body,
        organization_id=organization_id,
        organization_slug=organization_slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: PostApiV1ProjectsBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Any | PostApiV1ProjectsResponse201 | None:
    """Create a new project

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        body (PostApiV1ProjectsBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PostApiV1ProjectsResponse201
    """

    return sync_detailed(
        client=client,
        body=body,
        organization_id=organization_id,
        organization_slug=organization_slug,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostApiV1ProjectsBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Response[Any | PostApiV1ProjectsResponse201]:
    """Create a new project

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        body (PostApiV1ProjectsBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PostApiV1ProjectsResponse201]
    """

    kwargs = _get_kwargs(
        body=body,
        organization_id=organization_id,
        organization_slug=organization_slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostApiV1ProjectsBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Any | PostApiV1ProjectsResponse201 | None:
    """Create a new project

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        body (PostApiV1ProjectsBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PostApiV1ProjectsResponse201
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            organization_id=organization_id,
            organization_slug=organization_slug,
        )
    ).parsed

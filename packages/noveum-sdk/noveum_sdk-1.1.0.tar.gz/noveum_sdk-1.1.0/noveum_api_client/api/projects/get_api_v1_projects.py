from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_v1_projects_response_200_item import GetApiV1ProjectsResponse200Item
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
    include_environments: str | Unset = UNSET,
    include_trace_counts: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["organizationId"] = organization_id

    params["organizationSlug"] = organization_slug

    params["includeEnvironments"] = include_environments

    params["includeTraceCounts"] = include_trace_counts

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/projects",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> list[GetApiV1ProjectsResponse200Item] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = GetApiV1ProjectsResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[list[GetApiV1ProjectsResponse200Item]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
    include_environments: str | Unset = UNSET,
    include_trace_counts: str | Unset = UNSET,
) -> Response[list[GetApiV1ProjectsResponse200Item]]:
    """Get all projects

     Get all projects for an organization. Optional flags: includeEnvironments=true to include
    environment names, includeTraceCounts=true to include trace counts per project.

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        include_environments (str | Unset):
        include_trace_counts (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[GetApiV1ProjectsResponse200Item]]
    """

    kwargs = _get_kwargs(
        organization_id=organization_id,
        organization_slug=organization_slug,
        include_environments=include_environments,
        include_trace_counts=include_trace_counts,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
    include_environments: str | Unset = UNSET,
    include_trace_counts: str | Unset = UNSET,
) -> list[GetApiV1ProjectsResponse200Item] | None:
    """Get all projects

     Get all projects for an organization. Optional flags: includeEnvironments=true to include
    environment names, includeTraceCounts=true to include trace counts per project.

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        include_environments (str | Unset):
        include_trace_counts (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[GetApiV1ProjectsResponse200Item]
    """

    return sync_detailed(
        client=client,
        organization_id=organization_id,
        organization_slug=organization_slug,
        include_environments=include_environments,
        include_trace_counts=include_trace_counts,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
    include_environments: str | Unset = UNSET,
    include_trace_counts: str | Unset = UNSET,
) -> Response[list[GetApiV1ProjectsResponse200Item]]:
    """Get all projects

     Get all projects for an organization. Optional flags: includeEnvironments=true to include
    environment names, includeTraceCounts=true to include trace counts per project.

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        include_environments (str | Unset):
        include_trace_counts (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[GetApiV1ProjectsResponse200Item]]
    """

    kwargs = _get_kwargs(
        organization_id=organization_id,
        organization_slug=organization_slug,
        include_environments=include_environments,
        include_trace_counts=include_trace_counts,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
    include_environments: str | Unset = UNSET,
    include_trace_counts: str | Unset = UNSET,
) -> list[GetApiV1ProjectsResponse200Item] | None:
    """Get all projects

     Get all projects for an organization. Optional flags: includeEnvironments=true to include
    environment names, includeTraceCounts=true to include trace counts per project.

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        include_environments (str | Unset):
        include_trace_counts (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[GetApiV1ProjectsResponse200Item]
    """

    return (
        await asyncio_detailed(
            client=client,
            organization_id=organization_id,
            organization_slug=organization_slug,
            include_environments=include_environments,
            include_trace_counts=include_trace_counts,
        )
    ).parsed

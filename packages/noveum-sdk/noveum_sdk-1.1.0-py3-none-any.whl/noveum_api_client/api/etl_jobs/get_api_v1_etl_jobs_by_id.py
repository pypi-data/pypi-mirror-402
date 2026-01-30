from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_v1_etl_jobs_by_id_response_200 import GetApiV1EtlJobsByIdResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["organizationId"] = organization_id

    params["organizationSlug"] = organization_slug

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/etl-jobs/{id}".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | GetApiV1EtlJobsByIdResponse200 | None:
    if response.status_code == 200:
        response_200 = GetApiV1EtlJobsByIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | GetApiV1EtlJobsByIdResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Response[Any | GetApiV1EtlJobsByIdResponse200]:
    """Get a single ETL job

    Args:
        id (str):
        organization_id (str | Unset):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | GetApiV1EtlJobsByIdResponse200]
    """

    kwargs = _get_kwargs(
        id=id,
        organization_id=organization_id,
        organization_slug=organization_slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Any | GetApiV1EtlJobsByIdResponse200 | None:
    """Get a single ETL job

    Args:
        id (str):
        organization_id (str | Unset):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | GetApiV1EtlJobsByIdResponse200
    """

    return sync_detailed(
        id=id,
        client=client,
        organization_id=organization_id,
        organization_slug=organization_slug,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Response[Any | GetApiV1EtlJobsByIdResponse200]:
    """Get a single ETL job

    Args:
        id (str):
        organization_id (str | Unset):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | GetApiV1EtlJobsByIdResponse200]
    """

    kwargs = _get_kwargs(
        id=id,
        organization_id=organization_id,
        organization_slug=organization_slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Any | GetApiV1EtlJobsByIdResponse200 | None:
    """Get a single ETL job

    Args:
        id (str):
        organization_id (str | Unset):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | GetApiV1EtlJobsByIdResponse200
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            organization_id=organization_id,
            organization_slug=organization_slug,
        )
    ).parsed

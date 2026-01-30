from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_v1_scorers_by_id_response_200 import GetApiV1ScorersByIdResponse200
from ...models.get_api_v1_scorers_by_id_response_401 import GetApiV1ScorersByIdResponse401
from ...models.get_api_v1_scorers_by_id_response_404 import GetApiV1ScorersByIdResponse404
from ...models.get_api_v1_scorers_by_id_response_500 import GetApiV1ScorersByIdResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id_path: str,
    *,
    id_query: str,
    organization_slug: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["id"] = id_query

    params["organizationSlug"] = organization_slug

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/scorers/{id_path}".format(
            id_path=quote(str(id_path), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetApiV1ScorersByIdResponse200
    | GetApiV1ScorersByIdResponse401
    | GetApiV1ScorersByIdResponse404
    | GetApiV1ScorersByIdResponse500
    | None
):
    if response.status_code == 200:
        response_200 = GetApiV1ScorersByIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = GetApiV1ScorersByIdResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = GetApiV1ScorersByIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetApiV1ScorersByIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetApiV1ScorersByIdResponse200
    | GetApiV1ScorersByIdResponse401
    | GetApiV1ScorersByIdResponse404
    | GetApiV1ScorersByIdResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id_path: str,
    *,
    client: AuthenticatedClient | Client,
    id_query: str,
    organization_slug: str | Unset = UNSET,
) -> Response[
    GetApiV1ScorersByIdResponse200
    | GetApiV1ScorersByIdResponse401
    | GetApiV1ScorersByIdResponse404
    | GetApiV1ScorersByIdResponse500
]:
    """Get a single scorer by ID

     Retrieves detailed information about a specific scorer by its unique identifier. Returns the
    complete scorer configuration including name, description, type, schemas, and metadata. This
    endpoint can be used to retrieve both default (system-wide) scorers and organization-specific
    scorers.

    Args:
        id_path (str):
        id_query (str):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetApiV1ScorersByIdResponse200 | GetApiV1ScorersByIdResponse401 | GetApiV1ScorersByIdResponse404 | GetApiV1ScorersByIdResponse500]
    """

    kwargs = _get_kwargs(
        id_path=id_path,
        id_query=id_query,
        organization_slug=organization_slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id_path: str,
    *,
    client: AuthenticatedClient | Client,
    id_query: str,
    organization_slug: str | Unset = UNSET,
) -> (
    GetApiV1ScorersByIdResponse200
    | GetApiV1ScorersByIdResponse401
    | GetApiV1ScorersByIdResponse404
    | GetApiV1ScorersByIdResponse500
    | None
):
    """Get a single scorer by ID

     Retrieves detailed information about a specific scorer by its unique identifier. Returns the
    complete scorer configuration including name, description, type, schemas, and metadata. This
    endpoint can be used to retrieve both default (system-wide) scorers and organization-specific
    scorers.

    Args:
        id_path (str):
        id_query (str):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetApiV1ScorersByIdResponse200 | GetApiV1ScorersByIdResponse401 | GetApiV1ScorersByIdResponse404 | GetApiV1ScorersByIdResponse500
    """

    return sync_detailed(
        id_path=id_path,
        client=client,
        id_query=id_query,
        organization_slug=organization_slug,
    ).parsed


async def asyncio_detailed(
    id_path: str,
    *,
    client: AuthenticatedClient | Client,
    id_query: str,
    organization_slug: str | Unset = UNSET,
) -> Response[
    GetApiV1ScorersByIdResponse200
    | GetApiV1ScorersByIdResponse401
    | GetApiV1ScorersByIdResponse404
    | GetApiV1ScorersByIdResponse500
]:
    """Get a single scorer by ID

     Retrieves detailed information about a specific scorer by its unique identifier. Returns the
    complete scorer configuration including name, description, type, schemas, and metadata. This
    endpoint can be used to retrieve both default (system-wide) scorers and organization-specific
    scorers.

    Args:
        id_path (str):
        id_query (str):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetApiV1ScorersByIdResponse200 | GetApiV1ScorersByIdResponse401 | GetApiV1ScorersByIdResponse404 | GetApiV1ScorersByIdResponse500]
    """

    kwargs = _get_kwargs(
        id_path=id_path,
        id_query=id_query,
        organization_slug=organization_slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id_path: str,
    *,
    client: AuthenticatedClient | Client,
    id_query: str,
    organization_slug: str | Unset = UNSET,
) -> (
    GetApiV1ScorersByIdResponse200
    | GetApiV1ScorersByIdResponse401
    | GetApiV1ScorersByIdResponse404
    | GetApiV1ScorersByIdResponse500
    | None
):
    """Get a single scorer by ID

     Retrieves detailed information about a specific scorer by its unique identifier. Returns the
    complete scorer configuration including name, description, type, schemas, and metadata. This
    endpoint can be used to retrieve both default (system-wide) scorers and organization-specific
    scorers.

    Args:
        id_path (str):
        id_query (str):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetApiV1ScorersByIdResponse200 | GetApiV1ScorersByIdResponse401 | GetApiV1ScorersByIdResponse404 | GetApiV1ScorersByIdResponse500
    """

    return (
        await asyncio_detailed(
            id_path=id_path,
            client=client,
            id_query=id_query,
            organization_slug=organization_slug,
        )
    ).parsed

from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.put_api_v1_scorers_by_id_body import PutApiV1ScorersByIdBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id_path: str,
    *,
    body: PutApiV1ScorersByIdBody | Unset = UNSET,
    id_query: str,
    organization_slug: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["id"] = id_query

    params["organizationSlug"] = organization_slug

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/v1/scorers/{id_path}".format(
            id_path=quote(str(id_path), safe=""),
        ),
        "params": params,
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 200:
        return None

    if response.status_code == 400:
        return None

    if response.status_code == 401:
        return None

    if response.status_code == 403:
        return None

    if response.status_code == 404:
        return None

    if response.status_code == 500:
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
    id_path: str,
    *,
    client: AuthenticatedClient | Client,
    body: PutApiV1ScorersByIdBody | Unset = UNSET,
    id_query: str,
    organization_slug: str | Unset = UNSET,
) -> Response[Any]:
    """Update a scorer

     Updates an existing scorer for the organization. Only organization-specific scorers can be modified
    - default scorers and scorers from other organizations cannot be updated. All fields in the request
    body are optional and only provided fields will be updated.

    Args:
        id_path (str):
        id_query (str):
        organization_slug (str | Unset):
        body (PutApiV1ScorersByIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        id_path=id_path,
        body=body,
        id_query=id_query,
        organization_slug=organization_slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    id_path: str,
    *,
    client: AuthenticatedClient | Client,
    body: PutApiV1ScorersByIdBody | Unset = UNSET,
    id_query: str,
    organization_slug: str | Unset = UNSET,
) -> Response[Any]:
    """Update a scorer

     Updates an existing scorer for the organization. Only organization-specific scorers can be modified
    - default scorers and scorers from other organizations cannot be updated. All fields in the request
    body are optional and only provided fields will be updated.

    Args:
        id_path (str):
        id_query (str):
        organization_slug (str | Unset):
        body (PutApiV1ScorersByIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        id_path=id_path,
        body=body,
        id_query=id_query,
        organization_slug=organization_slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)

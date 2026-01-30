from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...types import UNSET, Response, Unset


def _get_kwargs(
    dataset_slug_path: str,
    item_id_path: str,
    scorer_id_path: str,
    *,
    dataset_slug_query: str,
    item_id_query: str,
    scorer_id_query: str,
    organization_slug: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["datasetSlug"] = dataset_slug_query

    params["itemId"] = item_id_query

    params["scorerId"] = scorer_id_query

    params["organizationSlug"] = organization_slug

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/scorers/results/{dataset_slug_path}/{item_id_path}/{scorer_id_path}".format(
            dataset_slug_path=quote(str(dataset_slug_path), safe=""),
            item_id_path=quote(str(item_id_path), safe=""),
            scorer_id_path=quote(str(scorer_id_path), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 200:
        return None

    if response.status_code == 401:
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
    dataset_slug_path: str,
    item_id_path: str,
    scorer_id_path: str,
    *,
    client: AuthenticatedClient | Client,
    dataset_slug_query: str,
    item_id_query: str,
    scorer_id_query: str,
    organization_slug: str | Unset = UNSET,
) -> Response[Any]:
    """Get scorer result by ID

     Retrieves a specific scorer result for an item.

    Args:
        dataset_slug_path (str):
        item_id_path (str):
        scorer_id_path (str):
        dataset_slug_query (str):
        item_id_query (str):
        scorer_id_query (str):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        dataset_slug_path=dataset_slug_path,
        item_id_path=item_id_path,
        scorer_id_path=scorer_id_path,
        dataset_slug_query=dataset_slug_query,
        item_id_query=item_id_query,
        scorer_id_query=scorer_id_query,
        organization_slug=organization_slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    dataset_slug_path: str,
    item_id_path: str,
    scorer_id_path: str,
    *,
    client: AuthenticatedClient | Client,
    dataset_slug_query: str,
    item_id_query: str,
    scorer_id_query: str,
    organization_slug: str | Unset = UNSET,
) -> Response[Any]:
    """Get scorer result by ID

     Retrieves a specific scorer result for an item.

    Args:
        dataset_slug_path (str):
        item_id_path (str):
        scorer_id_path (str):
        dataset_slug_query (str):
        item_id_query (str):
        scorer_id_query (str):
        organization_slug (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        dataset_slug_path=dataset_slug_path,
        item_id_path=item_id_path,
        scorer_id_path=scorer_id_path,
        dataset_slug_query=dataset_slug_query,
        item_id_query=item_id_query,
        scorer_id_query=scorer_id_query,
        organization_slug=organization_slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)

from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_v1_datasets_by_dataset_slug_items_sort_order import GetApiV1DatasetsByDatasetSlugItemsSortOrder
from ...types import UNSET, Response, Unset


def _get_kwargs(
    dataset_slug: str,
    *,
    version: str | Unset = UNSET,
    limit: float | Unset = 50.0,
    offset: float | Unset = 0.0,
    item_type: str | Unset = UNSET,
    search: str | Unset = UNSET,
    sort_by: str | Unset = UNSET,
    sort_order: GetApiV1DatasetsByDatasetSlugItemsSortOrder | Unset = GetApiV1DatasetsByDatasetSlugItemsSortOrder.ASC,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["version"] = version

    params["limit"] = limit

    params["offset"] = offset

    params["item_type"] = item_type

    params["search"] = search

    params["sort_by"] = sort_by

    json_sort_order: str | Unset = UNSET
    if not isinstance(sort_order, Unset):
        json_sort_order = sort_order.value

    params["sort_order"] = json_sort_order

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/datasets/{dataset_slug}/items".format(
            dataset_slug=quote(str(dataset_slug), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 200:
        return None

    if response.status_code == 404:
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
    dataset_slug: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,
    limit: float | Unset = 50.0,
    offset: float | Unset = 0.0,
    item_type: str | Unset = UNSET,
    search: str | Unset = UNSET,
    sort_by: str | Unset = UNSET,
    sort_order: GetApiV1DatasetsByDatasetSlugItemsSortOrder | Unset = GetApiV1DatasetsByDatasetSlugItemsSortOrder.ASC,
) -> Response[Any]:
    """List dataset items for a specific version

     Retrieves items from a specific version. Defaults to current_release if no version specified. Items
    marked as deleted (via deleted_at_version) are automatically filtered out for the requested version.
    Returns 404 if the specified version does not exist.

    Args:
        dataset_slug (str):
        version (str | Unset):
        limit (float | Unset):  Default: 50.0.
        offset (float | Unset):  Default: 0.0.
        item_type (str | Unset):
        search (str | Unset):
        sort_by (str | Unset):
        sort_order (GetApiV1DatasetsByDatasetSlugItemsSortOrder | Unset):  Default:
            GetApiV1DatasetsByDatasetSlugItemsSortOrder.ASC.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        dataset_slug=dataset_slug,
        version=version,
        limit=limit,
        offset=offset,
        item_type=item_type,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    dataset_slug: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,
    limit: float | Unset = 50.0,
    offset: float | Unset = 0.0,
    item_type: str | Unset = UNSET,
    search: str | Unset = UNSET,
    sort_by: str | Unset = UNSET,
    sort_order: GetApiV1DatasetsByDatasetSlugItemsSortOrder | Unset = GetApiV1DatasetsByDatasetSlugItemsSortOrder.ASC,
) -> Response[Any]:
    """List dataset items for a specific version

     Retrieves items from a specific version. Defaults to current_release if no version specified. Items
    marked as deleted (via deleted_at_version) are automatically filtered out for the requested version.
    Returns 404 if the specified version does not exist.

    Args:
        dataset_slug (str):
        version (str | Unset):
        limit (float | Unset):  Default: 50.0.
        offset (float | Unset):  Default: 0.0.
        item_type (str | Unset):
        search (str | Unset):
        sort_by (str | Unset):
        sort_order (GetApiV1DatasetsByDatasetSlugItemsSortOrder | Unset):  Default:
            GetApiV1DatasetsByDatasetSlugItemsSortOrder.ASC.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        dataset_slug=dataset_slug,
        version=version,
        limit=limit,
        offset=offset,
        item_type=item_type,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)

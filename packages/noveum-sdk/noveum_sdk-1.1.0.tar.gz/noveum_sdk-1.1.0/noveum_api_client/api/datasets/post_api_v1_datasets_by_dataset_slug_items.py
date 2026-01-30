from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_api_v1_datasets_by_dataset_slug_items_body import PostApiV1DatasetsByDatasetSlugItemsBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    dataset_slug: str,
    *,
    body: PostApiV1DatasetsByDatasetSlugItemsBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/datasets/{dataset_slug}/items".format(
            dataset_slug=quote(str(dataset_slug), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 201:
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
    body: PostApiV1DatasetsByDatasetSlugItemsBody | Unset = UNSET,
) -> Response[Any]:
    """Batch create dataset items in next_release version

     Creates multiple dataset items that will be added to the dataset's next_release version. These items
    will become part of the published dataset when you call the publish endpoint.

    Args:
        dataset_slug (str):
        body (PostApiV1DatasetsByDatasetSlugItemsBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        dataset_slug=dataset_slug,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    dataset_slug: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostApiV1DatasetsByDatasetSlugItemsBody | Unset = UNSET,
) -> Response[Any]:
    """Batch create dataset items in next_release version

     Creates multiple dataset items that will be added to the dataset's next_release version. These items
    will become part of the published dataset when you call the publish endpoint.

    Args:
        dataset_slug (str):
        body (PostApiV1DatasetsByDatasetSlugItemsBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        dataset_slug=dataset_slug,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)

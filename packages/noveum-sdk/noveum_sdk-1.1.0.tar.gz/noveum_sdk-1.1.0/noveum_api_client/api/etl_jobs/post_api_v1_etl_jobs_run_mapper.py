from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_api_v1_etl_jobs_run_mapper_body import PostApiV1EtlJobsRunMapperBody
from ...models.post_api_v1_etl_jobs_run_mapper_response_200 import PostApiV1EtlJobsRunMapperResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: PostApiV1EtlJobsRunMapperBody | Unset = UNSET,
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
        "url": "/api/v1/etl-jobs/run-mapper",
        "params": params,
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | PostApiV1EtlJobsRunMapperResponse200 | None:
    if response.status_code == 200:
        response_200 = PostApiV1EtlJobsRunMapperResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | PostApiV1EtlJobsRunMapperResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostApiV1EtlJobsRunMapperBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Response[Any | PostApiV1EtlJobsRunMapperResponse200]:
    """Run mapper code with trace ID

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        body (PostApiV1EtlJobsRunMapperBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PostApiV1EtlJobsRunMapperResponse200]
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
    body: PostApiV1EtlJobsRunMapperBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Any | PostApiV1EtlJobsRunMapperResponse200 | None:
    """Run mapper code with trace ID

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        body (PostApiV1EtlJobsRunMapperBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PostApiV1EtlJobsRunMapperResponse200
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
    body: PostApiV1EtlJobsRunMapperBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Response[Any | PostApiV1EtlJobsRunMapperResponse200]:
    """Run mapper code with trace ID

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        body (PostApiV1EtlJobsRunMapperBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PostApiV1EtlJobsRunMapperResponse200]
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
    body: PostApiV1EtlJobsRunMapperBody | Unset = UNSET,
    organization_id: str | Unset = UNSET,
    organization_slug: str | Unset = UNSET,
) -> Any | PostApiV1EtlJobsRunMapperResponse200 | None:
    """Run mapper code with trace ID

    Args:
        organization_id (str | Unset):
        organization_slug (str | Unset):
        body (PostApiV1EtlJobsRunMapperBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PostApiV1EtlJobsRunMapperResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            organization_id=organization_id,
            organization_slug=organization_slug,
        )
    ).parsed

from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_v1_traces_sort import GetApiV1TracesSort
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    organization_id: str | Unset = UNSET,
    from_: float | Unset = 0.0,
    size: float | Unset = UNSET,
    start_time: str | Unset = UNSET,
    end_time: str | Unset = UNSET,
    project: str | Unset = UNSET,
    environment: str | Unset = UNSET,
    status: str | Unset = UNSET,
    user_id: str | Unset = UNSET,
    session_id: str | Unset = UNSET,
    tags: list[str] | Unset = UNSET,
    sort: GetApiV1TracesSort | Unset = GetApiV1TracesSort.START_TIMEDESC,
    search_term: str | Unset = UNSET,
    include_spans: bool | Unset = False,
    trace_id_neq: str | Unset = UNSET,
    name_neq: str | Unset = UNSET,
    environment_neq: str | Unset = UNSET,
    user_id_neq: str | Unset = UNSET,
    session_id_neq: str | Unset = UNSET,
    status_neq: str | Unset = UNSET,
    project_neq: str | Unset = UNSET,
    service_name: str | Unset = UNSET,
    service_name_neq: str | Unset = UNSET,
    duration_ms_gt: str | Unset = UNSET,
    duration_ms_gte: str | Unset = UNSET,
    duration_ms_lt: str | Unset = UNSET,
    duration_ms_lte: str | Unset = UNSET,
    duration_ms_eq: str | Unset = UNSET,
    duration_ms_neq: str | Unset = UNSET,
    span_count_gt: str | Unset = UNSET,
    span_count_gte: str | Unset = UNSET,
    span_count_lt: str | Unset = UNSET,
    span_count_lte: str | Unset = UNSET,
    span_count_eq: str | Unset = UNSET,
    span_count_neq: str | Unset = UNSET,
    error_count_gt: str | Unset = UNSET,
    error_count_gte: str | Unset = UNSET,
    error_count_lt: str | Unset = UNSET,
    error_count_lte: str | Unset = UNSET,
    error_count_eq: str | Unset = UNSET,
    error_count_neq: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["organizationId"] = organization_id

    params["from"] = from_

    params["size"] = size

    params["startTime"] = start_time

    params["endTime"] = end_time

    params["project"] = project

    params["environment"] = environment

    params["status"] = status

    params["userId"] = user_id

    params["sessionId"] = session_id

    json_tags: list[str] | Unset = UNSET
    if not isinstance(tags, Unset):
        json_tags = tags

    params["tags"] = json_tags

    json_sort: str | Unset = UNSET
    if not isinstance(sort, Unset):
        json_sort = sort.value

    params["sort"] = json_sort

    params["searchTerm"] = search_term

    params["includeSpans"] = include_spans

    params["trace_id_neq"] = trace_id_neq

    params["name_neq"] = name_neq

    params["environment_neq"] = environment_neq

    params["user_id_neq"] = user_id_neq

    params["session_id_neq"] = session_id_neq

    params["status_neq"] = status_neq

    params["project_neq"] = project_neq

    params["service_name"] = service_name

    params["service_name_neq"] = service_name_neq

    params["duration_ms_gt"] = duration_ms_gt

    params["duration_ms_gte"] = duration_ms_gte

    params["duration_ms_lt"] = duration_ms_lt

    params["duration_ms_lte"] = duration_ms_lte

    params["duration_ms_eq"] = duration_ms_eq

    params["duration_ms_neq"] = duration_ms_neq

    params["span_count_gt"] = span_count_gt

    params["span_count_gte"] = span_count_gte

    params["span_count_lt"] = span_count_lt

    params["span_count_lte"] = span_count_lte

    params["span_count_eq"] = span_count_eq

    params["span_count_neq"] = span_count_neq

    params["error_count_gt"] = error_count_gt

    params["error_count_gte"] = error_count_gte

    params["error_count_lt"] = error_count_lt

    params["error_count_lte"] = error_count_lte

    params["error_count_eq"] = error_count_eq

    params["error_count_neq"] = error_count_neq

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/traces",
        "params": params,
    }

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
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    from_: float | Unset = 0.0,
    size: float | Unset = UNSET,
    start_time: str | Unset = UNSET,
    end_time: str | Unset = UNSET,
    project: str | Unset = UNSET,
    environment: str | Unset = UNSET,
    status: str | Unset = UNSET,
    user_id: str | Unset = UNSET,
    session_id: str | Unset = UNSET,
    tags: list[str] | Unset = UNSET,
    sort: GetApiV1TracesSort | Unset = GetApiV1TracesSort.START_TIMEDESC,
    search_term: str | Unset = UNSET,
    include_spans: bool | Unset = False,
    trace_id_neq: str | Unset = UNSET,
    name_neq: str | Unset = UNSET,
    environment_neq: str | Unset = UNSET,
    user_id_neq: str | Unset = UNSET,
    session_id_neq: str | Unset = UNSET,
    status_neq: str | Unset = UNSET,
    project_neq: str | Unset = UNSET,
    service_name: str | Unset = UNSET,
    service_name_neq: str | Unset = UNSET,
    duration_ms_gt: str | Unset = UNSET,
    duration_ms_gte: str | Unset = UNSET,
    duration_ms_lt: str | Unset = UNSET,
    duration_ms_lte: str | Unset = UNSET,
    duration_ms_eq: str | Unset = UNSET,
    duration_ms_neq: str | Unset = UNSET,
    span_count_gt: str | Unset = UNSET,
    span_count_gte: str | Unset = UNSET,
    span_count_lt: str | Unset = UNSET,
    span_count_lte: str | Unset = UNSET,
    span_count_eq: str | Unset = UNSET,
    span_count_neq: str | Unset = UNSET,
    error_count_gt: str | Unset = UNSET,
    error_count_gte: str | Unset = UNSET,
    error_count_lt: str | Unset = UNSET,
    error_count_lte: str | Unset = UNSET,
    error_count_eq: str | Unset = UNSET,
    error_count_neq: str | Unset = UNSET,
) -> Response[Any]:
    """Query traces

     Query traces with optional filters and pagination. Supports API key auth (org inferred) and session
    auth (org required via X-Organization-Id/Slug header or organizationId param). Supports comma-
    separated values for multiple filters (e.g., project=proj1,proj2&status=ok,error), negation filters
    (*_neq), and numeric comparison operators (gt/gte/lt/lte/eq/neq) for duration_ms, span_count, and
    error_count. Example: ?duration_ms_gt=100&duration_ms_lt=500&span_count_gte=10

    Args:
        organization_id (str | Unset):
        from_ (float | Unset):  Default: 0.0.
        size (float | Unset):
        start_time (str | Unset):
        end_time (str | Unset):
        project (str | Unset):
        environment (str | Unset):
        status (str | Unset):
        user_id (str | Unset):
        session_id (str | Unset):
        tags (list[str] | Unset):
        sort (GetApiV1TracesSort | Unset):  Default: GetApiV1TracesSort.START_TIMEDESC.
        search_term (str | Unset):
        include_spans (bool | Unset):  Default: False.
        trace_id_neq (str | Unset):
        name_neq (str | Unset):
        environment_neq (str | Unset):
        user_id_neq (str | Unset):
        session_id_neq (str | Unset):
        status_neq (str | Unset):
        project_neq (str | Unset):
        service_name (str | Unset):
        service_name_neq (str | Unset):
        duration_ms_gt (str | Unset):
        duration_ms_gte (str | Unset):
        duration_ms_lt (str | Unset):
        duration_ms_lte (str | Unset):
        duration_ms_eq (str | Unset):
        duration_ms_neq (str | Unset):
        span_count_gt (str | Unset):
        span_count_gte (str | Unset):
        span_count_lt (str | Unset):
        span_count_lte (str | Unset):
        span_count_eq (str | Unset):
        span_count_neq (str | Unset):
        error_count_gt (str | Unset):
        error_count_gte (str | Unset):
        error_count_lt (str | Unset):
        error_count_lte (str | Unset):
        error_count_eq (str | Unset):
        error_count_neq (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        organization_id=organization_id,
        from_=from_,
        size=size,
        start_time=start_time,
        end_time=end_time,
        project=project,
        environment=environment,
        status=status,
        user_id=user_id,
        session_id=session_id,
        tags=tags,
        sort=sort,
        search_term=search_term,
        include_spans=include_spans,
        trace_id_neq=trace_id_neq,
        name_neq=name_neq,
        environment_neq=environment_neq,
        user_id_neq=user_id_neq,
        session_id_neq=session_id_neq,
        status_neq=status_neq,
        project_neq=project_neq,
        service_name=service_name,
        service_name_neq=service_name_neq,
        duration_ms_gt=duration_ms_gt,
        duration_ms_gte=duration_ms_gte,
        duration_ms_lt=duration_ms_lt,
        duration_ms_lte=duration_ms_lte,
        duration_ms_eq=duration_ms_eq,
        duration_ms_neq=duration_ms_neq,
        span_count_gt=span_count_gt,
        span_count_gte=span_count_gte,
        span_count_lt=span_count_lt,
        span_count_lte=span_count_lte,
        span_count_eq=span_count_eq,
        span_count_neq=span_count_neq,
        error_count_gt=error_count_gt,
        error_count_gte=error_count_gte,
        error_count_lt=error_count_lt,
        error_count_lte=error_count_lte,
        error_count_eq=error_count_eq,
        error_count_neq=error_count_neq,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    organization_id: str | Unset = UNSET,
    from_: float | Unset = 0.0,
    size: float | Unset = UNSET,
    start_time: str | Unset = UNSET,
    end_time: str | Unset = UNSET,
    project: str | Unset = UNSET,
    environment: str | Unset = UNSET,
    status: str | Unset = UNSET,
    user_id: str | Unset = UNSET,
    session_id: str | Unset = UNSET,
    tags: list[str] | Unset = UNSET,
    sort: GetApiV1TracesSort | Unset = GetApiV1TracesSort.START_TIMEDESC,
    search_term: str | Unset = UNSET,
    include_spans: bool | Unset = False,
    trace_id_neq: str | Unset = UNSET,
    name_neq: str | Unset = UNSET,
    environment_neq: str | Unset = UNSET,
    user_id_neq: str | Unset = UNSET,
    session_id_neq: str | Unset = UNSET,
    status_neq: str | Unset = UNSET,
    project_neq: str | Unset = UNSET,
    service_name: str | Unset = UNSET,
    service_name_neq: str | Unset = UNSET,
    duration_ms_gt: str | Unset = UNSET,
    duration_ms_gte: str | Unset = UNSET,
    duration_ms_lt: str | Unset = UNSET,
    duration_ms_lte: str | Unset = UNSET,
    duration_ms_eq: str | Unset = UNSET,
    duration_ms_neq: str | Unset = UNSET,
    span_count_gt: str | Unset = UNSET,
    span_count_gte: str | Unset = UNSET,
    span_count_lt: str | Unset = UNSET,
    span_count_lte: str | Unset = UNSET,
    span_count_eq: str | Unset = UNSET,
    span_count_neq: str | Unset = UNSET,
    error_count_gt: str | Unset = UNSET,
    error_count_gte: str | Unset = UNSET,
    error_count_lt: str | Unset = UNSET,
    error_count_lte: str | Unset = UNSET,
    error_count_eq: str | Unset = UNSET,
    error_count_neq: str | Unset = UNSET,
) -> Response[Any]:
    """Query traces

     Query traces with optional filters and pagination. Supports API key auth (org inferred) and session
    auth (org required via X-Organization-Id/Slug header or organizationId param). Supports comma-
    separated values for multiple filters (e.g., project=proj1,proj2&status=ok,error), negation filters
    (*_neq), and numeric comparison operators (gt/gte/lt/lte/eq/neq) for duration_ms, span_count, and
    error_count. Example: ?duration_ms_gt=100&duration_ms_lt=500&span_count_gte=10

    Args:
        organization_id (str | Unset):
        from_ (float | Unset):  Default: 0.0.
        size (float | Unset):
        start_time (str | Unset):
        end_time (str | Unset):
        project (str | Unset):
        environment (str | Unset):
        status (str | Unset):
        user_id (str | Unset):
        session_id (str | Unset):
        tags (list[str] | Unset):
        sort (GetApiV1TracesSort | Unset):  Default: GetApiV1TracesSort.START_TIMEDESC.
        search_term (str | Unset):
        include_spans (bool | Unset):  Default: False.
        trace_id_neq (str | Unset):
        name_neq (str | Unset):
        environment_neq (str | Unset):
        user_id_neq (str | Unset):
        session_id_neq (str | Unset):
        status_neq (str | Unset):
        project_neq (str | Unset):
        service_name (str | Unset):
        service_name_neq (str | Unset):
        duration_ms_gt (str | Unset):
        duration_ms_gte (str | Unset):
        duration_ms_lt (str | Unset):
        duration_ms_lte (str | Unset):
        duration_ms_eq (str | Unset):
        duration_ms_neq (str | Unset):
        span_count_gt (str | Unset):
        span_count_gte (str | Unset):
        span_count_lt (str | Unset):
        span_count_lte (str | Unset):
        span_count_eq (str | Unset):
        span_count_neq (str | Unset):
        error_count_gt (str | Unset):
        error_count_gte (str | Unset):
        error_count_lt (str | Unset):
        error_count_lte (str | Unset):
        error_count_eq (str | Unset):
        error_count_neq (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        organization_id=organization_id,
        from_=from_,
        size=size,
        start_time=start_time,
        end_time=end_time,
        project=project,
        environment=environment,
        status=status,
        user_id=user_id,
        session_id=session_id,
        tags=tags,
        sort=sort,
        search_term=search_term,
        include_spans=include_spans,
        trace_id_neq=trace_id_neq,
        name_neq=name_neq,
        environment_neq=environment_neq,
        user_id_neq=user_id_neq,
        session_id_neq=session_id_neq,
        status_neq=status_neq,
        project_neq=project_neq,
        service_name=service_name,
        service_name_neq=service_name_neq,
        duration_ms_gt=duration_ms_gt,
        duration_ms_gte=duration_ms_gte,
        duration_ms_lt=duration_ms_lt,
        duration_ms_lte=duration_ms_lte,
        duration_ms_eq=duration_ms_eq,
        duration_ms_neq=duration_ms_neq,
        span_count_gt=span_count_gt,
        span_count_gte=span_count_gte,
        span_count_lt=span_count_lt,
        span_count_lte=span_count_lte,
        span_count_eq=span_count_eq,
        span_count_neq=span_count_neq,
        error_count_gt=error_count_gt,
        error_count_gte=error_count_gte,
        error_count_lt=error_count_lt,
        error_count_lte=error_count_lte,
        error_count_eq=error_count_eq,
        error_count_neq=error_count_neq,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)

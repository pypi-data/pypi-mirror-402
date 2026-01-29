from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_application_logs_level import GetApplicationLogsLevel
from ...models.get_application_logs_response_200 import GetApplicationLogsResponse200
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    line_count: int,
    level: Union[Unset, GetApplicationLogsLevel] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["lineCount"] = line_count

    json_level: Union[Unset, str] = UNSET
    if not isinstance(level, Unset):
        json_level = level.value

    params["level"] = json_level

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/application/logs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetApplicationLogsResponse200, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetApplicationLogsResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        response_500 = UnknownError.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[GetApplicationLogsResponse200, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    line_count: int,
    level: Union[Unset, GetApplicationLogsLevel] = UNSET,
) -> Response[Union[GetApplicationLogsResponse200, UnknownError]]:
    """Logs

     Get a list of the last N log entries, this will ignore the header of the file. The endpoint is
    limited by the log level set in NINA

    Args:
        line_count (int):
        level (Union[Unset, GetApplicationLogsLevel]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetApplicationLogsResponse200, UnknownError]]
    """

    kwargs = _get_kwargs(
        line_count=line_count,
        level=level,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    line_count: int,
    level: Union[Unset, GetApplicationLogsLevel] = UNSET,
) -> Optional[Union[GetApplicationLogsResponse200, UnknownError]]:
    """Logs

     Get a list of the last N log entries, this will ignore the header of the file. The endpoint is
    limited by the log level set in NINA

    Args:
        line_count (int):
        level (Union[Unset, GetApplicationLogsLevel]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetApplicationLogsResponse200, UnknownError]
    """

    return sync_detailed(
        client=client,
        line_count=line_count,
        level=level,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    line_count: int,
    level: Union[Unset, GetApplicationLogsLevel] = UNSET,
) -> Response[Union[GetApplicationLogsResponse200, UnknownError]]:
    """Logs

     Get a list of the last N log entries, this will ignore the header of the file. The endpoint is
    limited by the log level set in NINA

    Args:
        line_count (int):
        level (Union[Unset, GetApplicationLogsLevel]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetApplicationLogsResponse200, UnknownError]]
    """

    kwargs = _get_kwargs(
        line_count=line_count,
        level=level,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    line_count: int,
    level: Union[Unset, GetApplicationLogsLevel] = UNSET,
) -> Optional[Union[GetApplicationLogsResponse200, UnknownError]]:
    """Logs

     Get a list of the last N log entries, this will ignore the header of the file. The endpoint is
    limited by the log level set in NINA

    Args:
        line_count (int):
        level (Union[Unset, GetApplicationLogsLevel]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetApplicationLogsResponse200, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            line_count=line_count,
            level=level,
        )
    ).parsed

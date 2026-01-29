from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_framing_set_source_response_200 import GetFramingSetSourceResponse200
from ...models.get_framing_set_source_response_400 import GetFramingSetSourceResponse400
from ...models.get_framing_set_source_source import GetFramingSetSourceSource
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    source: GetFramingSetSourceSource,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    json_source = source.value
    params["source"] = json_source

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/framing/set-source",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetFramingSetSourceResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetFramingSetSourceResponse400.from_dict(response.json())

        return response_400
    if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        response_500 = UnknownError.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    source: GetFramingSetSourceSource,
) -> Response[Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]]:
    """Set Source

     Set framing assistant source. This requires the framing assistant to be initalized, which can by
    achieved by openening it once.

    Args:
        source (GetFramingSetSourceSource):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        source=source,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    source: GetFramingSetSourceSource,
) -> Optional[Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]]:
    """Set Source

     Set framing assistant source. This requires the framing assistant to be initalized, which can by
    achieved by openening it once.

    Args:
        source (GetFramingSetSourceSource):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        source=source,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    source: GetFramingSetSourceSource,
) -> Response[Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]]:
    """Set Source

     Set framing assistant source. This requires the framing assistant to be initalized, which can by
    achieved by openening it once.

    Args:
        source (GetFramingSetSourceSource):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        source=source,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    source: GetFramingSetSourceSource,
) -> Optional[Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]]:
    """Set Source

     Set framing assistant source. This requires the framing assistant to be initalized, which can by
    achieved by openening it once.

    Args:
        source (GetFramingSetSourceSource):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFramingSetSourceResponse200, GetFramingSetSourceResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            source=source,
        )
    ).parsed

from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.flat_device_info import FlatDeviceInfo
from ...models.unknown_error import UnknownError
from ...types import Response


def _get_kwargs() -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/flatdevice/info",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[FlatDeviceInfo, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = FlatDeviceInfo.from_dict(response.json())

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
) -> Response[Union[FlatDeviceInfo, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[FlatDeviceInfo, UnknownError]]:
    """Information

     Get information about the flat panel, Coverstate represents the following values&#58; 0&#58;
    Unknown, 1&#58; NeitherOpenNorClosed, 2&#58; Closed, 3&#58; Open, 4&#58; Error, 5&#58; Not present

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[FlatDeviceInfo, UnknownError]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[FlatDeviceInfo, UnknownError]]:
    """Information

     Get information about the flat panel, Coverstate represents the following values&#58; 0&#58;
    Unknown, 1&#58; NeitherOpenNorClosed, 2&#58; Closed, 3&#58; Open, 4&#58; Error, 5&#58; Not present

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[FlatDeviceInfo, UnknownError]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[FlatDeviceInfo, UnknownError]]:
    """Information

     Get information about the flat panel, Coverstate represents the following values&#58; 0&#58;
    Unknown, 1&#58; NeitherOpenNorClosed, 2&#58; Closed, 3&#58; Open, 4&#58; Error, 5&#58; Not present

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[FlatDeviceInfo, UnknownError]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[FlatDeviceInfo, UnknownError]]:
    """Information

     Get information about the flat panel, Coverstate represents the following values&#58; 0&#58;
    Unknown, 1&#58; NeitherOpenNorClosed, 2&#58; Closed, 3&#58; Open, 4&#58; Error, 5&#58; Not present

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[FlatDeviceInfo, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed

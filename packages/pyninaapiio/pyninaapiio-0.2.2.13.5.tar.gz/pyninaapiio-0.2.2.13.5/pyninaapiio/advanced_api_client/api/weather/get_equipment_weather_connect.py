from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_weather_connect_response_200 import GetEquipmentWeatherConnectResponse200
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    to: Union[Unset, str] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["to"] = to

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/weather/connect",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetEquipmentWeatherConnectResponse200, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentWeatherConnectResponse200.from_dict(response.json())

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
) -> Response[Union[GetEquipmentWeatherConnectResponse200, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    to: Union[Unset, str] = UNSET,
) -> Response[Union[GetEquipmentWeatherConnectResponse200, UnknownError]]:
    """Connect

     Connect to weather source

    Args:
        to (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentWeatherConnectResponse200, UnknownError]]
    """

    kwargs = _get_kwargs(
        to=to,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    to: Union[Unset, str] = UNSET,
) -> Optional[Union[GetEquipmentWeatherConnectResponse200, UnknownError]]:
    """Connect

     Connect to weather source

    Args:
        to (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentWeatherConnectResponse200, UnknownError]
    """

    return sync_detailed(
        client=client,
        to=to,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    to: Union[Unset, str] = UNSET,
) -> Response[Union[GetEquipmentWeatherConnectResponse200, UnknownError]]:
    """Connect

     Connect to weather source

    Args:
        to (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentWeatherConnectResponse200, UnknownError]]
    """

    kwargs = _get_kwargs(
        to=to,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    to: Union[Unset, str] = UNSET,
) -> Optional[Union[GetEquipmentWeatherConnectResponse200, UnknownError]]:
    """Connect

     Connect to weather source

    Args:
        to (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentWeatherConnectResponse200, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            to=to,
        )
    ).parsed

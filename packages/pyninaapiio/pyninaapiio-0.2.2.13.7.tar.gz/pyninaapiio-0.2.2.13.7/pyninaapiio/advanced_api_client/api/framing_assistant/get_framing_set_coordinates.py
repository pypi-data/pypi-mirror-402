from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_framing_set_coordinates_response_200 import GetFramingSetCoordinatesResponse200
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    r_aangle: float,
    dec_angle: float,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["RAangle"] = r_aangle

    params["DecAngle"] = dec_angle

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/framing/set-coordinates",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetFramingSetCoordinatesResponse200, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetFramingSetCoordinatesResponse200.from_dict(response.json())

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
) -> Response[Union[GetFramingSetCoordinatesResponse200, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    r_aangle: float,
    dec_angle: float,
) -> Response[Union[GetFramingSetCoordinatesResponse200, UnknownError]]:
    """Set Coordinates

     Set framing assistant coordinates. This requires the framing assistant to be initalized, which can
    by achieved by openening it once.

    Args:
        r_aangle (float):
        dec_angle (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFramingSetCoordinatesResponse200, UnknownError]]
    """

    kwargs = _get_kwargs(
        r_aangle=r_aangle,
        dec_angle=dec_angle,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    r_aangle: float,
    dec_angle: float,
) -> Optional[Union[GetFramingSetCoordinatesResponse200, UnknownError]]:
    """Set Coordinates

     Set framing assistant coordinates. This requires the framing assistant to be initalized, which can
    by achieved by openening it once.

    Args:
        r_aangle (float):
        dec_angle (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFramingSetCoordinatesResponse200, UnknownError]
    """

    return sync_detailed(
        client=client,
        r_aangle=r_aangle,
        dec_angle=dec_angle,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    r_aangle: float,
    dec_angle: float,
) -> Response[Union[GetFramingSetCoordinatesResponse200, UnknownError]]:
    """Set Coordinates

     Set framing assistant coordinates. This requires the framing assistant to be initalized, which can
    by achieved by openening it once.

    Args:
        r_aangle (float):
        dec_angle (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFramingSetCoordinatesResponse200, UnknownError]]
    """

    kwargs = _get_kwargs(
        r_aangle=r_aangle,
        dec_angle=dec_angle,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    r_aangle: float,
    dec_angle: float,
) -> Optional[Union[GetFramingSetCoordinatesResponse200, UnknownError]]:
    """Set Coordinates

     Set framing assistant coordinates. This requires the framing assistant to be initalized, which can
    by achieved by openening it once.

    Args:
        r_aangle (float):
        dec_angle (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFramingSetCoordinatesResponse200, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            r_aangle=r_aangle,
            dec_angle=dec_angle,
        )
    ).parsed

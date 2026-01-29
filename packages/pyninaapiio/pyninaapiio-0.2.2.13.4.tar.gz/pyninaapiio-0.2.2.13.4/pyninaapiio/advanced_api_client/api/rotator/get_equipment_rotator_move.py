from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_rotator_move_response_200 import GetEquipmentRotatorMoveResponse200
from ...models.get_equipment_rotator_move_response_409 import GetEquipmentRotatorMoveResponse409
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    position: float,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["position"] = position

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/rotator/move",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentRotatorMoveResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = GetEquipmentRotatorMoveResponse409.from_dict(response.json())

        return response_409
    if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        response_500 = UnknownError.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    position: float,
) -> Response[Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]]:
    """Move

     Move the rotator

    Args:
        position (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        position=position,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    position: float,
) -> Optional[Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]]:
    """Move

     Move the rotator

    Args:
        position (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]
    """

    return sync_detailed(
        client=client,
        position=position,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    position: float,
) -> Response[Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]]:
    """Move

     Move the rotator

    Args:
        position (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        position=position,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    position: float,
) -> Optional[Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]]:
    """Move

     Move the rotator

    Args:
        position (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentRotatorMoveResponse200, GetEquipmentRotatorMoveResponse409, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            position=position,
        )
    ).parsed

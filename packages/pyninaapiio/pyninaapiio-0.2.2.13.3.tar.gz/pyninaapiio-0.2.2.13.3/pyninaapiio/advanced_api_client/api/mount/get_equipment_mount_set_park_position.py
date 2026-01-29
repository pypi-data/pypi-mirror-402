from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_mount_set_park_position_response_200 import GetEquipmentMountSetParkPositionResponse200
from ...models.get_equipment_mount_set_park_position_response_400 import GetEquipmentMountSetParkPositionResponse400
from ...models.unknown_error import UnknownError
from ...types import Response


def _get_kwargs() -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/mount/set-park-position",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]
]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentMountSetParkPositionResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetEquipmentMountSetParkPositionResponse400.from_dict(response.json())

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
) -> Response[
    Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]
]:
    """Set Park Position

     Sets the current mount position as park position. This requires the mount to be unparked.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]
]:
    """Set Park Position

     Sets the current mount position as park position. This requires the mount to be unparked.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]
]:
    """Set Park Position

     Sets the current mount position as park position. This requires the mount to be unparked.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]
]:
    """Set Park Position

     Sets the current mount position as park position. This requires the mount to be unparked.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentMountSetParkPositionResponse200, GetEquipmentMountSetParkPositionResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed

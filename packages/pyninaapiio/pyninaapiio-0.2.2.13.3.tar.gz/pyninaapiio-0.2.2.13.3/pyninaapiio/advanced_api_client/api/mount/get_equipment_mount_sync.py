from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_mount_sync_response_200 import GetEquipmentMountSyncResponse200
from ...models.get_equipment_mount_sync_response_400 import GetEquipmentMountSyncResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ra: Union[Unset, float] = UNSET,
    dec: Union[Unset, float] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["ra"] = ra

    params["dec"] = dec

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/mount/sync",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentMountSyncResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetEquipmentMountSyncResponse400.from_dict(response.json())

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
) -> Response[Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    ra: Union[Unset, float] = UNSET,
    dec: Union[Unset, float] = UNSET,
) -> Response[Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]]:
    """Sync

     Sync the scope, either by manually supplying the coordinates or by solving and syncing. If the
    coordinates are omitted, a platesolve will be performed.

    Args:
        ra (Union[Unset, float]):
        dec (Union[Unset, float]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        ra=ra,
        dec=dec,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    ra: Union[Unset, float] = UNSET,
    dec: Union[Unset, float] = UNSET,
) -> Optional[Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]]:
    """Sync

     Sync the scope, either by manually supplying the coordinates or by solving and syncing. If the
    coordinates are omitted, a platesolve will be performed.

    Args:
        ra (Union[Unset, float]):
        dec (Union[Unset, float]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        ra=ra,
        dec=dec,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    ra: Union[Unset, float] = UNSET,
    dec: Union[Unset, float] = UNSET,
) -> Response[Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]]:
    """Sync

     Sync the scope, either by manually supplying the coordinates or by solving and syncing. If the
    coordinates are omitted, a platesolve will be performed.

    Args:
        ra (Union[Unset, float]):
        dec (Union[Unset, float]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        ra=ra,
        dec=dec,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    ra: Union[Unset, float] = UNSET,
    dec: Union[Unset, float] = UNSET,
) -> Optional[Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]]:
    """Sync

     Sync the scope, either by manually supplying the coordinates or by solving and syncing. If the
    coordinates are omitted, a platesolve will be performed.

    Args:
        ra (Union[Unset, float]):
        dec (Union[Unset, float]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentMountSyncResponse200, GetEquipmentMountSyncResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            ra=ra,
            dec=dec,
        )
    ).parsed

from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_flatdevice_set_cover_response_200 import GetEquipmentFlatdeviceSetCoverResponse200
from ...models.get_equipment_flatdevice_set_cover_response_409 import GetEquipmentFlatdeviceSetCoverResponse409
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    closed: bool,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["closed"] = closed

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/flatdevice/set-cover",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]
]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentFlatdeviceSetCoverResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = GetEquipmentFlatdeviceSetCoverResponse409.from_dict(response.json())

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
) -> Response[
    Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]
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
    closed: bool,
) -> Response[
    Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]
]:
    """Set Cover

     Set the cover to the specified position

    Args:
        closed (bool):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        closed=closed,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    closed: bool,
) -> Optional[
    Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]
]:
    """Set Cover

     Set the cover to the specified position

    Args:
        closed (bool):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]
    """

    return sync_detailed(
        client=client,
        closed=closed,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    closed: bool,
) -> Response[
    Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]
]:
    """Set Cover

     Set the cover to the specified position

    Args:
        closed (bool):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        closed=closed,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    closed: bool,
) -> Optional[
    Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]
]:
    """Set Cover

     Set the cover to the specified position

    Args:
        closed (bool):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentFlatdeviceSetCoverResponse200, GetEquipmentFlatdeviceSetCoverResponse409, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            closed=closed,
        )
    ).parsed

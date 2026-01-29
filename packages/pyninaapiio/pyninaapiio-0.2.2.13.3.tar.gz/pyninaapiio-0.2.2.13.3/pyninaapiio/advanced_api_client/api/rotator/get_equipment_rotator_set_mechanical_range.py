from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_rotator_set_mechanical_range_range import GetEquipmentRotatorSetMechanicalRangeRange
from ...models.get_equipment_rotator_set_mechanical_range_response_200 import (
    GetEquipmentRotatorSetMechanicalRangeResponse200,
)
from ...models.get_equipment_rotator_set_mechanical_range_response_409 import (
    GetEquipmentRotatorSetMechanicalRangeResponse409,
)
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    range_: GetEquipmentRotatorSetMechanicalRangeRange,
    range_start_position: Union[Unset, float] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    json_range_ = range_.value
    params["range"] = json_range_

    params["rangeStartPosition"] = range_start_position

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/rotator/set-mechanical-range",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError
    ]
]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentRotatorSetMechanicalRangeResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = GetEquipmentRotatorSetMechanicalRangeResponse409.from_dict(response.json())

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
    Union[
        GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError
    ]
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
    range_: GetEquipmentRotatorSetMechanicalRangeRange,
    range_start_position: Union[Unset, float] = UNSET,
) -> Response[
    Union[
        GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError
    ]
]:
    """Set Range

     Sets the mechanical range of the rotator to full, 180° (half) or 90° (quarter)

    Args:
        range_ (GetEquipmentRotatorSetMechanicalRangeRange):
        range_start_position (Union[Unset, float]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        range_=range_,
        range_start_position=range_start_position,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    range_: GetEquipmentRotatorSetMechanicalRangeRange,
    range_start_position: Union[Unset, float] = UNSET,
) -> Optional[
    Union[
        GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError
    ]
]:
    """Set Range

     Sets the mechanical range of the rotator to full, 180° (half) or 90° (quarter)

    Args:
        range_ (GetEquipmentRotatorSetMechanicalRangeRange):
        range_start_position (Union[Unset, float]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError]
    """

    return sync_detailed(
        client=client,
        range_=range_,
        range_start_position=range_start_position,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    range_: GetEquipmentRotatorSetMechanicalRangeRange,
    range_start_position: Union[Unset, float] = UNSET,
) -> Response[
    Union[
        GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError
    ]
]:
    """Set Range

     Sets the mechanical range of the rotator to full, 180° (half) or 90° (quarter)

    Args:
        range_ (GetEquipmentRotatorSetMechanicalRangeRange):
        range_start_position (Union[Unset, float]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        range_=range_,
        range_start_position=range_start_position,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    range_: GetEquipmentRotatorSetMechanicalRangeRange,
    range_start_position: Union[Unset, float] = UNSET,
) -> Optional[
    Union[
        GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError
    ]
]:
    """Set Range

     Sets the mechanical range of the rotator to full, 180° (half) or 90° (quarter)

    Args:
        range_ (GetEquipmentRotatorSetMechanicalRangeRange):
        range_start_position (Union[Unset, float]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentRotatorSetMechanicalRangeResponse200, GetEquipmentRotatorSetMechanicalRangeResponse409, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            range_=range_,
            range_start_position=range_start_position,
        )
    ).parsed

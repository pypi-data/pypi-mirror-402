from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_focuser_auto_focus_response_200 import GetEquipmentFocuserAutoFocusResponse200
from ...models.get_equipment_focuser_auto_focus_response_409 import GetEquipmentFocuserAutoFocusResponse409
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    cancel: Union[Unset, bool] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["cancel"] = cancel

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/focuser/auto-focus",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentFocuserAutoFocusResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = GetEquipmentFocuserAutoFocusResponse409.from_dict(response.json())

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
) -> Response[Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    cancel: Union[Unset, bool] = UNSET,
) -> Response[Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]]:
    """Auto Focus

     Start an AF

    Args:
        cancel (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        cancel=cancel,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    cancel: Union[Unset, bool] = UNSET,
) -> Optional[Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]]:
    """Auto Focus

     Start an AF

    Args:
        cancel (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]
    """

    return sync_detailed(
        client=client,
        cancel=cancel,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    cancel: Union[Unset, bool] = UNSET,
) -> Response[Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]]:
    """Auto Focus

     Start an AF

    Args:
        cancel (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        cancel=cancel,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    cancel: Union[Unset, bool] = UNSET,
) -> Optional[Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]]:
    """Auto Focus

     Start an AF

    Args:
        cancel (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentFocuserAutoFocusResponse200, GetEquipmentFocuserAutoFocusResponse409, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            cancel=cancel,
        )
    ).parsed

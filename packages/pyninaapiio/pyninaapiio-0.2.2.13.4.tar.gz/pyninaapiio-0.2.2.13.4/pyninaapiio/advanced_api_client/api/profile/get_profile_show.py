from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.profile_info import ProfileInfo
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    active: Union[Unset, bool] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["active"] = active

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/profile/show",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ProfileInfo, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = ProfileInfo.from_dict(response.json())

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
) -> Response[Union[ProfileInfo, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    active: Union[Unset, bool] = UNSET,
) -> Response[Union[ProfileInfo, UnknownError]]:
    """Show Profile

     Shows the profile

    Args:
        active (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProfileInfo, UnknownError]]
    """

    kwargs = _get_kwargs(
        active=active,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    active: Union[Unset, bool] = UNSET,
) -> Optional[Union[ProfileInfo, UnknownError]]:
    """Show Profile

     Shows the profile

    Args:
        active (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProfileInfo, UnknownError]
    """

    return sync_detailed(
        client=client,
        active=active,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    active: Union[Unset, bool] = UNSET,
) -> Response[Union[ProfileInfo, UnknownError]]:
    """Show Profile

     Shows the profile

    Args:
        active (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProfileInfo, UnknownError]]
    """

    kwargs = _get_kwargs(
        active=active,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    active: Union[Unset, bool] = UNSET,
) -> Optional[Union[ProfileInfo, UnknownError]]:
    """Show Profile

     Shows the profile

    Args:
        active (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProfileInfo, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            active=active,
        )
    ).parsed

from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_application_switch_tab_response_200 import GetApplicationSwitchTabResponse200
from ...models.get_application_switch_tab_response_400 import GetApplicationSwitchTabResponse400
from ...models.get_application_switch_tab_tab import GetApplicationSwitchTabTab
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    tab: GetApplicationSwitchTabTab,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    json_tab = tab.value
    params["tab"] = json_tab

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/application/switch-tab",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetApplicationSwitchTabResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetApplicationSwitchTabResponse400.from_dict(response.json())

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
) -> Response[Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    tab: GetApplicationSwitchTabTab,
) -> Response[Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]]:
    """Switch Tab

     Switches the application tab

    Args:
        tab (GetApplicationSwitchTabTab):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        tab=tab,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    tab: GetApplicationSwitchTabTab,
) -> Optional[Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]]:
    """Switch Tab

     Switches the application tab

    Args:
        tab (GetApplicationSwitchTabTab):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        tab=tab,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    tab: GetApplicationSwitchTabTab,
) -> Response[Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]]:
    """Switch Tab

     Switches the application tab

    Args:
        tab (GetApplicationSwitchTabTab):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        tab=tab,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    tab: GetApplicationSwitchTabTab,
) -> Optional[Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]]:
    """Switch Tab

     Switches the application tab

    Args:
        tab (GetApplicationSwitchTabTab):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetApplicationSwitchTabResponse200, GetApplicationSwitchTabResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            tab=tab,
        )
    ).parsed

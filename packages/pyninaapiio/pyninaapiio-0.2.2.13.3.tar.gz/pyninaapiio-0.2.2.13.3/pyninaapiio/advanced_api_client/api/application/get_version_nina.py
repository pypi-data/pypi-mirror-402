from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_version_nina_response_200 import GetVersionNinaResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    friendly: Union[Unset, bool] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["friendly"] = friendly

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/version/nina",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetVersionNinaResponse200]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetVersionNinaResponse200.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetVersionNinaResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    friendly: Union[Unset, bool] = UNSET,
) -> Response[GetVersionNinaResponse200]:
    """NINA Version

     Returns the version of NINA.

    Args:
        friendly (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetVersionNinaResponse200]
    """

    kwargs = _get_kwargs(
        friendly=friendly,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    friendly: Union[Unset, bool] = UNSET,
) -> Optional[GetVersionNinaResponse200]:
    """NINA Version

     Returns the version of NINA.

    Args:
        friendly (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetVersionNinaResponse200
    """

    return sync_detailed(
        client=client,
        friendly=friendly,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    friendly: Union[Unset, bool] = UNSET,
) -> Response[GetVersionNinaResponse200]:
    """NINA Version

     Returns the version of NINA.

    Args:
        friendly (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetVersionNinaResponse200]
    """

    kwargs = _get_kwargs(
        friendly=friendly,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    friendly: Union[Unset, bool] = UNSET,
) -> Optional[GetVersionNinaResponse200]:
    """NINA Version

     Returns the version of NINA.

    Args:
        friendly (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetVersionNinaResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            friendly=friendly,
        )
    ).parsed

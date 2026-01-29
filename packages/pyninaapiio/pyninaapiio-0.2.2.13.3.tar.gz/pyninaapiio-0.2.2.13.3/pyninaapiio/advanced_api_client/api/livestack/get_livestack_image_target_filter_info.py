from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_livestack_image_target_filter_info_response_200 import GetLivestackImageTargetFilterInfoResponse200
from ...models.unknown_error import UnknownError
from ...types import Response


def _get_kwargs(
    target: str,
    filter_: str,
) -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/livestack/image/{target}/{filter_}/info",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetLivestackImageTargetFilterInfoResponse200.from_dict(response.json())

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
) -> Response[Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    target: str,
    filter_: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]]:
    """Get Stacked Image Info

     Gets information about the stacked image, like filter, target and stack count.

    Args:
        target (str):  Example: M31.
        filter_ (str):  Example: RGB.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]]
    """

    kwargs = _get_kwargs(
        target=target,
        filter_=filter_,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    target: str,
    filter_: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]]:
    """Get Stacked Image Info

     Gets information about the stacked image, like filter, target and stack count.

    Args:
        target (str):  Example: M31.
        filter_ (str):  Example: RGB.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]
    """

    return sync_detailed(
        target=target,
        filter_=filter_,
        client=client,
    ).parsed


async def asyncio_detailed(
    target: str,
    filter_: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]]:
    """Get Stacked Image Info

     Gets information about the stacked image, like filter, target and stack count.

    Args:
        target (str):  Example: M31.
        filter_ (str):  Example: RGB.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]]
    """

    kwargs = _get_kwargs(
        target=target,
        filter_=filter_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    target: str,
    filter_: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]]:
    """Get Stacked Image Info

     Gets information about the stacked image, like filter, target and stack count.

    Args:
        target (str):  Example: M31.
        filter_ (str):  Example: RGB.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetLivestackImageTargetFilterInfoResponse200, UnknownError]
    """

    return (
        await asyncio_detailed(
            target=target,
            filter_=filter_,
            client=client,
        )
    ).parsed

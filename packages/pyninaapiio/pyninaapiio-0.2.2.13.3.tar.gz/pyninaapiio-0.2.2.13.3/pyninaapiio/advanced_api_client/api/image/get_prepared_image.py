from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_prepared_image_bayer_pattern import GetPreparedImageBayerPattern
from ...models.get_prepared_image_response_400 import GetPreparedImageResponse400
from ...models.get_prepared_image_response_404 import GetPreparedImageResponse404
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetPreparedImageBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["resize"] = resize

    params["quality"] = quality

    params["size"] = size

    params["scale"] = scale

    params["factor"] = factor

    params["blackClipping"] = black_clipping

    params["unlinked"] = unlinked

    params["debayer"] = debayer

    json_bayer_pattern: Union[Unset, str] = UNSET
    if not isinstance(bayer_pattern, Unset):
        json_bayer_pattern = bayer_pattern.value

    params["bayerPattern"] = json_bayer_pattern

    params["autoPrepare"] = auto_prepare

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/prepared-image",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]]:
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetPreparedImageResponse400.from_dict(response.json())

        return response_400
    if response.status_code == HTTPStatus.NOT_FOUND:
        response_404 = GetPreparedImageResponse404.from_dict(response.json())

        return response_404
    if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        response_500 = UnknownError.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetPreparedImageBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
) -> Response[Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]]:
    """Get Prepared Image

     Get the last prepared image. This is the image that is shown in NINA in the image dockable.

    Args:
        resize (Union[Unset, bool]):
        quality (Union[Unset, int]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        unlinked (Union[Unset, bool]):
        debayer (Union[Unset, bool]):
        bayer_pattern (Union[Unset, GetPreparedImageBayerPattern]):
        auto_prepare (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]]
    """

    kwargs = _get_kwargs(
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        factor=factor,
        black_clipping=black_clipping,
        unlinked=unlinked,
        debayer=debayer,
        bayer_pattern=bayer_pattern,
        auto_prepare=auto_prepare,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetPreparedImageBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
) -> Optional[Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]]:
    """Get Prepared Image

     Get the last prepared image. This is the image that is shown in NINA in the image dockable.

    Args:
        resize (Union[Unset, bool]):
        quality (Union[Unset, int]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        unlinked (Union[Unset, bool]):
        debayer (Union[Unset, bool]):
        bayer_pattern (Union[Unset, GetPreparedImageBayerPattern]):
        auto_prepare (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]
    """

    return sync_detailed(
        client=client,
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        factor=factor,
        black_clipping=black_clipping,
        unlinked=unlinked,
        debayer=debayer,
        bayer_pattern=bayer_pattern,
        auto_prepare=auto_prepare,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetPreparedImageBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
) -> Response[Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]]:
    """Get Prepared Image

     Get the last prepared image. This is the image that is shown in NINA in the image dockable.

    Args:
        resize (Union[Unset, bool]):
        quality (Union[Unset, int]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        unlinked (Union[Unset, bool]):
        debayer (Union[Unset, bool]):
        bayer_pattern (Union[Unset, GetPreparedImageBayerPattern]):
        auto_prepare (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]]
    """

    kwargs = _get_kwargs(
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        factor=factor,
        black_clipping=black_clipping,
        unlinked=unlinked,
        debayer=debayer,
        bayer_pattern=bayer_pattern,
        auto_prepare=auto_prepare,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetPreparedImageBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
) -> Optional[Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]]:
    """Get Prepared Image

     Get the last prepared image. This is the image that is shown in NINA in the image dockable.

    Args:
        resize (Union[Unset, bool]):
        quality (Union[Unset, int]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        unlinked (Union[Unset, bool]):
        debayer (Union[Unset, bool]):
        bayer_pattern (Union[Unset, GetPreparedImageBayerPattern]):
        auto_prepare (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetPreparedImageResponse400, GetPreparedImageResponse404, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            resize=resize,
            quality=quality,
            size=size,
            scale=scale,
            factor=factor,
            black_clipping=black_clipping,
            unlinked=unlinked,
            debayer=debayer,
            bayer_pattern=bayer_pattern,
            auto_prepare=auto_prepare,
        )
    ).parsed

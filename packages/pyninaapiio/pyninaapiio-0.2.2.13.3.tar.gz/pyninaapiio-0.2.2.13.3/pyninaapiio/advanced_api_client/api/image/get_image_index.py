from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_image_index_bayer_pattern import GetImageIndexBayerPattern
from ...models.get_image_index_image_type import GetImageIndexImageType
from ...models.get_image_index_response_200 import GetImageIndexResponse200
from ...models.get_image_index_response_400 import GetImageIndexResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    index: int,
    *,
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetImageIndexBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageIndexImageType] = UNSET,
    raw_fits: Union[Unset, bool] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["resize"] = resize

    params["quality"] = quality

    params["size"] = size

    params["scale"] = scale

    params["factor"] = factor

    params["blackClipping"] = black_clipping

    params["unlinked"] = unlinked

    params["stream"] = stream

    params["debayer"] = debayer

    json_bayer_pattern: Union[Unset, str] = UNSET
    if not isinstance(bayer_pattern, Unset):
        json_bayer_pattern = bayer_pattern.value

    params["bayerPattern"] = json_bayer_pattern

    params["autoPrepare"] = auto_prepare

    json_image_type: Union[Unset, str] = UNSET
    if not isinstance(image_type, Unset):
        json_image_type = image_type.value

    params["imageType"] = json_image_type

    params["raw_fits"] = raw_fits

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/image/{index}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetImageIndexResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetImageIndexResponse400.from_dict(response.json())

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
) -> Response[Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetImageIndexBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageIndexImageType] = UNSET,
    raw_fits: Union[Unset, bool] = UNSET,
) -> Response[Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]]:
    """Get Image

     Get image

    Args:
        index (int):
        resize (Union[Unset, bool]):
        quality (Union[Unset, int]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        unlinked (Union[Unset, bool]):
        stream (Union[Unset, bool]):
        debayer (Union[Unset, bool]):
        bayer_pattern (Union[Unset, GetImageIndexBayerPattern]):
        auto_prepare (Union[Unset, bool]):
        image_type (Union[Unset, GetImageIndexImageType]):
        raw_fits (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        index=index,
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        factor=factor,
        black_clipping=black_clipping,
        unlinked=unlinked,
        stream=stream,
        debayer=debayer,
        bayer_pattern=bayer_pattern,
        auto_prepare=auto_prepare,
        image_type=image_type,
        raw_fits=raw_fits,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetImageIndexBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageIndexImageType] = UNSET,
    raw_fits: Union[Unset, bool] = UNSET,
) -> Optional[Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]]:
    """Get Image

     Get image

    Args:
        index (int):
        resize (Union[Unset, bool]):
        quality (Union[Unset, int]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        unlinked (Union[Unset, bool]):
        stream (Union[Unset, bool]):
        debayer (Union[Unset, bool]):
        bayer_pattern (Union[Unset, GetImageIndexBayerPattern]):
        auto_prepare (Union[Unset, bool]):
        image_type (Union[Unset, GetImageIndexImageType]):
        raw_fits (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]
    """

    return sync_detailed(
        index=index,
        client=client,
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        factor=factor,
        black_clipping=black_clipping,
        unlinked=unlinked,
        stream=stream,
        debayer=debayer,
        bayer_pattern=bayer_pattern,
        auto_prepare=auto_prepare,
        image_type=image_type,
        raw_fits=raw_fits,
    ).parsed


async def asyncio_detailed(
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetImageIndexBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageIndexImageType] = UNSET,
    raw_fits: Union[Unset, bool] = UNSET,
) -> Response[Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]]:
    """Get Image

     Get image

    Args:
        index (int):
        resize (Union[Unset, bool]):
        quality (Union[Unset, int]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        unlinked (Union[Unset, bool]):
        stream (Union[Unset, bool]):
        debayer (Union[Unset, bool]):
        bayer_pattern (Union[Unset, GetImageIndexBayerPattern]):
        auto_prepare (Union[Unset, bool]):
        image_type (Union[Unset, GetImageIndexImageType]):
        raw_fits (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        index=index,
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        factor=factor,
        black_clipping=black_clipping,
        unlinked=unlinked,
        stream=stream,
        debayer=debayer,
        bayer_pattern=bayer_pattern,
        auto_prepare=auto_prepare,
        image_type=image_type,
        raw_fits=raw_fits,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, int] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    factor: Union[Unset, float] = UNSET,
    black_clipping: Union[Unset, float] = UNSET,
    unlinked: Union[Unset, bool] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    debayer: Union[Unset, bool] = UNSET,
    bayer_pattern: Union[Unset, GetImageIndexBayerPattern] = UNSET,
    auto_prepare: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageIndexImageType] = UNSET,
    raw_fits: Union[Unset, bool] = UNSET,
) -> Optional[Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]]:
    """Get Image

     Get image

    Args:
        index (int):
        resize (Union[Unset, bool]):
        quality (Union[Unset, int]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        factor (Union[Unset, float]):
        black_clipping (Union[Unset, float]):
        unlinked (Union[Unset, bool]):
        stream (Union[Unset, bool]):
        debayer (Union[Unset, bool]):
        bayer_pattern (Union[Unset, GetImageIndexBayerPattern]):
        auto_prepare (Union[Unset, bool]):
        image_type (Union[Unset, GetImageIndexImageType]):
        raw_fits (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetImageIndexResponse200, GetImageIndexResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            index=index,
            client=client,
            resize=resize,
            quality=quality,
            size=size,
            scale=scale,
            factor=factor,
            black_clipping=black_clipping,
            unlinked=unlinked,
            stream=stream,
            debayer=debayer,
            bayer_pattern=bayer_pattern,
            auto_prepare=auto_prepare,
            image_type=image_type,
            raw_fits=raw_fits,
        )
    ).parsed

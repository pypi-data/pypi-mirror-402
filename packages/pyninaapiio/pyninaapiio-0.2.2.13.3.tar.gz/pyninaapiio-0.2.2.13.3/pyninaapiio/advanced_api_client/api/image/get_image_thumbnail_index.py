from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_image_thumbnail_index_image_type import GetImageThumbnailIndexImageType
from ...models.get_image_thumbnail_index_response_400 import GetImageThumbnailIndexResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    index: int,
    *,
    image_type: Union[Unset, GetImageThumbnailIndexImageType] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    json_image_type: Union[Unset, str] = UNSET
    if not isinstance(image_type, Unset):
        json_image_type = image_type.value

    params["imageType"] = json_image_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/image/thumbnail/{index}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetImageThumbnailIndexResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetImageThumbnailIndexResponse400.from_dict(response.json())

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
) -> Response[Union[GetImageThumbnailIndexResponse400, UnknownError]]:
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
    image_type: Union[Unset, GetImageThumbnailIndexImageType] = UNSET,
) -> Response[Union[GetImageThumbnailIndexResponse400, UnknownError]]:
    """Get Thumbnail

     Get the thumbnail of an image. This requies Create Thumbnails to be enabled in NINA. Otherwise, use
    the image endpoint and resize the image. This thumbnail has a width of 256px.

    Args:
        index (int):
        image_type (Union[Unset, GetImageThumbnailIndexImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetImageThumbnailIndexResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        index=index,
        image_type=image_type,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    image_type: Union[Unset, GetImageThumbnailIndexImageType] = UNSET,
) -> Optional[Union[GetImageThumbnailIndexResponse400, UnknownError]]:
    """Get Thumbnail

     Get the thumbnail of an image. This requies Create Thumbnails to be enabled in NINA. Otherwise, use
    the image endpoint and resize the image. This thumbnail has a width of 256px.

    Args:
        index (int):
        image_type (Union[Unset, GetImageThumbnailIndexImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetImageThumbnailIndexResponse400, UnknownError]
    """

    return sync_detailed(
        index=index,
        client=client,
        image_type=image_type,
    ).parsed


async def asyncio_detailed(
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    image_type: Union[Unset, GetImageThumbnailIndexImageType] = UNSET,
) -> Response[Union[GetImageThumbnailIndexResponse400, UnknownError]]:
    """Get Thumbnail

     Get the thumbnail of an image. This requies Create Thumbnails to be enabled in NINA. Otherwise, use
    the image endpoint and resize the image. This thumbnail has a width of 256px.

    Args:
        index (int):
        image_type (Union[Unset, GetImageThumbnailIndexImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetImageThumbnailIndexResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        index=index,
        image_type=image_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    image_type: Union[Unset, GetImageThumbnailIndexImageType] = UNSET,
) -> Optional[Union[GetImageThumbnailIndexResponse400, UnknownError]]:
    """Get Thumbnail

     Get the thumbnail of an image. This requies Create Thumbnails to be enabled in NINA. Otherwise, use
    the image endpoint and resize the image. This thumbnail has a width of 256px.

    Args:
        index (int):
        image_type (Union[Unset, GetImageThumbnailIndexImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetImageThumbnailIndexResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            index=index,
            client=client,
            image_type=image_type,
        )
    ).parsed

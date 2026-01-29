from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_image_history_image_type import GetImageHistoryImageType
from ...models.get_image_history_response_200 import GetImageHistoryResponse200
from ...models.get_image_history_response_400 import GetImageHistoryResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    all_: Union[Unset, bool] = UNSET,
    index: Union[Unset, int] = UNSET,
    count: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageHistoryImageType] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["all"] = all_

    params["index"] = index

    params["count"] = count

    json_image_type: Union[Unset, str] = UNSET
    if not isinstance(image_type, Unset):
        json_image_type = image_type.value

    params["imageType"] = json_image_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/image-history",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetImageHistoryResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetImageHistoryResponse400.from_dict(response.json())

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
) -> Response[Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    all_: Union[Unset, bool] = UNSET,
    index: Union[Unset, int] = UNSET,
    count: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageHistoryImageType] = UNSET,
) -> Response[Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]]:
    """Get Image History

     Get image history. Only one parameter is required

    Args:
        all_ (Union[Unset, bool]):
        index (Union[Unset, int]):
        count (Union[Unset, bool]):
        image_type (Union[Unset, GetImageHistoryImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        all_=all_,
        index=index,
        count=count,
        image_type=image_type,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    all_: Union[Unset, bool] = UNSET,
    index: Union[Unset, int] = UNSET,
    count: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageHistoryImageType] = UNSET,
) -> Optional[Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]]:
    """Get Image History

     Get image history. Only one parameter is required

    Args:
        all_ (Union[Unset, bool]):
        index (Union[Unset, int]):
        count (Union[Unset, bool]):
        image_type (Union[Unset, GetImageHistoryImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        all_=all_,
        index=index,
        count=count,
        image_type=image_type,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    all_: Union[Unset, bool] = UNSET,
    index: Union[Unset, int] = UNSET,
    count: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageHistoryImageType] = UNSET,
) -> Response[Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]]:
    """Get Image History

     Get image history. Only one parameter is required

    Args:
        all_ (Union[Unset, bool]):
        index (Union[Unset, int]):
        count (Union[Unset, bool]):
        image_type (Union[Unset, GetImageHistoryImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        all_=all_,
        index=index,
        count=count,
        image_type=image_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    all_: Union[Unset, bool] = UNSET,
    index: Union[Unset, int] = UNSET,
    count: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetImageHistoryImageType] = UNSET,
) -> Optional[Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]]:
    """Get Image History

     Get image history. Only one parameter is required

    Args:
        all_ (Union[Unset, bool]):
        index (Union[Unset, int]):
        count (Union[Unset, bool]):
        image_type (Union[Unset, GetImageHistoryImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetImageHistoryResponse200, GetImageHistoryResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            all_=all_,
            index=index,
            count=count,
            image_type=image_type,
        )
    ).parsed

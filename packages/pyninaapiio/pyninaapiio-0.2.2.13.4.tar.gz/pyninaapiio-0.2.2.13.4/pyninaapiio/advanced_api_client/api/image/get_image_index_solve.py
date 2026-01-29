from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_image_index_solve_image_type import GetImageIndexSolveImageType
from ...models.get_image_index_solve_response_200 import GetImageIndexSolveResponse200
from ...models.get_image_index_solve_response_400 import GetImageIndexSolveResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    index: int,
    *,
    image_type: Union[Unset, GetImageIndexSolveImageType] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    json_image_type: Union[Unset, str] = UNSET
    if not isinstance(image_type, Unset):
        json_image_type = image_type.value

    params["imageType"] = json_image_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/image/{index}/solve",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetImageIndexSolveResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetImageIndexSolveResponse400.from_dict(response.json())

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
) -> Response[Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]]:
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
    image_type: Union[Unset, GetImageIndexSolveImageType] = UNSET,
) -> Response[Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]]:
    """Solve image

     Solves the specified image, the result is returned immediately (blocking request)

    Args:
        index (int):
        image_type (Union[Unset, GetImageIndexSolveImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]]
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
    image_type: Union[Unset, GetImageIndexSolveImageType] = UNSET,
) -> Optional[Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]]:
    """Solve image

     Solves the specified image, the result is returned immediately (blocking request)

    Args:
        index (int):
        image_type (Union[Unset, GetImageIndexSolveImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]
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
    image_type: Union[Unset, GetImageIndexSolveImageType] = UNSET,
) -> Response[Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]]:
    """Solve image

     Solves the specified image, the result is returned immediately (blocking request)

    Args:
        index (int):
        image_type (Union[Unset, GetImageIndexSolveImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]]
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
    image_type: Union[Unset, GetImageIndexSolveImageType] = UNSET,
) -> Optional[Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]]:
    """Solve image

     Solves the specified image, the result is returned immediately (blocking request)

    Args:
        index (int):
        image_type (Union[Unset, GetImageIndexSolveImageType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetImageIndexSolveResponse200, GetImageIndexSolveResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            index=index,
            client=client,
            image_type=image_type,
        )
    ).parsed

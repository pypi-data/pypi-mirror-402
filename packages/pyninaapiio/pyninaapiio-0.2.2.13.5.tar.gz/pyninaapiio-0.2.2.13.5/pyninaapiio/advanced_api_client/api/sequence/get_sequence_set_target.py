from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_sequence_set_target_response_200 import GetSequenceSetTargetResponse200
from ...models.get_sequence_set_target_response_400 import GetSequenceSetTargetResponse400
from ...models.get_sequence_set_target_response_409 import GetSequenceSetTargetResponse409
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    name: str,
    ra: float,
    dec: float,
    rotation: float,
    index: int,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["name"] = name

    params["ra"] = ra

    params["dec"] = dec

    params["rotation"] = rotation

    params["index"] = index

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/sequence/set-target",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError
    ]
]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetSequenceSetTargetResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetSequenceSetTargetResponse400.from_dict(response.json())

        return response_400
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = GetSequenceSetTargetResponse409.from_dict(response.json())

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
) -> Response[
    Union[
        GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
    ra: float,
    dec: float,
    rotation: float,
    index: int,
) -> Response[
    Union[
        GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError
    ]
]:
    """Set Target

     Set the target of any one of the active target containers in the sequence

    Args:
        name (str):  Example: Orion.
        ra (float):
        dec (float):
        rotation (float):
        index (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        name=name,
        ra=ra,
        dec=dec,
        rotation=rotation,
        index=index,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
    ra: float,
    dec: float,
    rotation: float,
    index: int,
) -> Optional[
    Union[
        GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError
    ]
]:
    """Set Target

     Set the target of any one of the active target containers in the sequence

    Args:
        name (str):  Example: Orion.
        ra (float):
        dec (float):
        rotation (float):
        index (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError]
    """

    return sync_detailed(
        client=client,
        name=name,
        ra=ra,
        dec=dec,
        rotation=rotation,
        index=index,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
    ra: float,
    dec: float,
    rotation: float,
    index: int,
) -> Response[
    Union[
        GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError
    ]
]:
    """Set Target

     Set the target of any one of the active target containers in the sequence

    Args:
        name (str):  Example: Orion.
        ra (float):
        dec (float):
        rotation (float):
        index (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        name=name,
        ra=ra,
        dec=dec,
        rotation=rotation,
        index=index,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
    ra: float,
    dec: float,
    rotation: float,
    index: int,
) -> Optional[
    Union[
        GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError
    ]
]:
    """Set Target

     Set the target of any one of the active target containers in the sequence

    Args:
        name (str):  Example: Orion.
        ra (float):
        dec (float):
        rotation (float):
        index (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSequenceSetTargetResponse200, GetSequenceSetTargetResponse400, GetSequenceSetTargetResponse409, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            name=name,
            ra=ra,
            dec=dec,
            rotation=rotation,
            index=index,
        )
    ).parsed

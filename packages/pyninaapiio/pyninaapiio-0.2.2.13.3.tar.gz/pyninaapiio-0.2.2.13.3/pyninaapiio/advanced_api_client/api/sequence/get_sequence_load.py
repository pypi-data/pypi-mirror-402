from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_sequence_load_response_200 import GetSequenceLoadResponse200
from ...models.get_sequence_load_response_400 import GetSequenceLoadResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    sequence_name: str,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["sequenceName"] = sequence_name

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/sequence/load",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetSequenceLoadResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetSequenceLoadResponse400.from_dict(response.json())

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
) -> Response[Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    sequence_name: str,
) -> Response[Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]]:
    """Load Sequence from file

     Loads a sequence from a file from the default sequence folders, the names can be retrieved using the
    `sequence/list-available` endpoint

    Args:
        sequence_name (str):  Example: Orion.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        sequence_name=sequence_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    sequence_name: str,
) -> Optional[Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]]:
    """Load Sequence from file

     Loads a sequence from a file from the default sequence folders, the names can be retrieved using the
    `sequence/list-available` endpoint

    Args:
        sequence_name (str):  Example: Orion.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        sequence_name=sequence_name,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    sequence_name: str,
) -> Response[Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]]:
    """Load Sequence from file

     Loads a sequence from a file from the default sequence folders, the names can be retrieved using the
    `sequence/list-available` endpoint

    Args:
        sequence_name (str):  Example: Orion.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        sequence_name=sequence_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    sequence_name: str,
) -> Optional[Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]]:
    """Load Sequence from file

     Loads a sequence from a file from the default sequence folders, the names can be retrieved using the
    `sequence/list-available` endpoint

    Args:
        sequence_name (str):  Example: Orion.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSequenceLoadResponse200, GetSequenceLoadResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            sequence_name=sequence_name,
        )
    ).parsed

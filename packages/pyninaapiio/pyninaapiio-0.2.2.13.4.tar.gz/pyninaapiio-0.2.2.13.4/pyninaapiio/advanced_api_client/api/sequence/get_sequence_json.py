from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_sequence_json_response_409 import GetSequenceJsonResponse409
from ...models.sequence_base_json import SequenceBaseJson
from ...models.unknown_error import UnknownError
from ...types import Response


def _get_kwargs() -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/sequence/json",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = SequenceBaseJson.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = GetSequenceJsonResponse409.from_dict(response.json())

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
) -> Response[Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]]:
    """JSON

     Get sequence as json. This endpoint is generally advised to use over state since it gives more
    reliable results.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]]:
    """JSON

     Get sequence as json. This endpoint is generally advised to use over state since it gives more
    reliable results.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]]:
    """JSON

     Get sequence as json. This endpoint is generally advised to use over state since it gives more
    reliable results.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]]:
    """JSON

     Get sequence as json. This endpoint is generally advised to use over state since it gives more
    reliable results.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSequenceJsonResponse409, SequenceBaseJson, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed

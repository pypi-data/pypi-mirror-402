from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_sequence_edit_response_200 import GetSequenceEditResponse200
from ...models.get_sequence_edit_response_400 import GetSequenceEditResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    path: str,
    value: str,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["path"] = path

    params["value"] = value

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/sequence/edit",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetSequenceEditResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetSequenceEditResponse400.from_dict(response.json())

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
) -> Response[Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    path: str,
    value: str,
) -> Response[Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]]:
    """Edit a Sequence

     This works similary to profile/set-value. Note that this mainly supports fields that expect simple
    types like strings, numbers etc, and may not work for things like enums or objects (filter, time
    source, ...). This is an experimental feature, and it could have unexpected side effects or simply
    not work for some instructions or fields. If you encounter any bugs (except that it is not working
    with enums or objects), feel free to create an issue on github or contact me on the NINA discord.

    Args:
        path (str):  Example: Imaging-Items-0-Items-0-ExposureTime.
        value (str):  Example: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        path=path,
        value=value,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    path: str,
    value: str,
) -> Optional[Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]]:
    """Edit a Sequence

     This works similary to profile/set-value. Note that this mainly supports fields that expect simple
    types like strings, numbers etc, and may not work for things like enums or objects (filter, time
    source, ...). This is an experimental feature, and it could have unexpected side effects or simply
    not work for some instructions or fields. If you encounter any bugs (except that it is not working
    with enums or objects), feel free to create an issue on github or contact me on the NINA discord.

    Args:
        path (str):  Example: Imaging-Items-0-Items-0-ExposureTime.
        value (str):  Example: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        path=path,
        value=value,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    path: str,
    value: str,
) -> Response[Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]]:
    """Edit a Sequence

     This works similary to profile/set-value. Note that this mainly supports fields that expect simple
    types like strings, numbers etc, and may not work for things like enums or objects (filter, time
    source, ...). This is an experimental feature, and it could have unexpected side effects or simply
    not work for some instructions or fields. If you encounter any bugs (except that it is not working
    with enums or objects), feel free to create an issue on github or contact me on the NINA discord.

    Args:
        path (str):  Example: Imaging-Items-0-Items-0-ExposureTime.
        value (str):  Example: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        path=path,
        value=value,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    path: str,
    value: str,
) -> Optional[Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]]:
    """Edit a Sequence

     This works similary to profile/set-value. Note that this mainly supports fields that expect simple
    types like strings, numbers etc, and may not work for things like enums or objects (filter, time
    source, ...). This is an experimental feature, and it could have unexpected side effects or simply
    not work for some instructions or fields. If you encounter any bugs (except that it is not working
    with enums or objects), feel free to create an issue on github or contact me on the NINA discord.

    Args:
        path (str):  Example: Imaging-Items-0-Items-0-ExposureTime.
        value (str):  Example: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSequenceEditResponse200, GetSequenceEditResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            path=path,
            value=value,
        )
    ).parsed

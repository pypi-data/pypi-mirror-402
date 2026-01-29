from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.framing_assistant_info import FramingAssistantInfo
from ...models.get_framing_determine_rotation_response_200_type_0 import GetFramingDetermineRotationResponse200Type0
from ...models.get_framing_determine_rotation_response_400 import GetFramingDetermineRotationResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    wait_for_result: Union[Unset, bool] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["waitForResult"] = wait_for_result

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/framing/determine-rotation",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetFramingDetermineRotationResponse400,
        Union["FramingAssistantInfo", "GetFramingDetermineRotationResponse200Type0"],
        UnknownError,
    ]
]:
    if response.status_code == HTTPStatus.OK:

        def _parse_response_200(
            data: object,
        ) -> Union["FramingAssistantInfo", "GetFramingDetermineRotationResponse200Type0"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = GetFramingDetermineRotationResponse200Type0.from_dict(data)

                return response_200_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = FramingAssistantInfo.from_dict(data)

            return response_200_type_1

        response_200 = _parse_response_200(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetFramingDetermineRotationResponse400.from_dict(response.json())

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
) -> Response[
    Union[
        GetFramingDetermineRotationResponse400,
        Union["FramingAssistantInfo", "GetFramingDetermineRotationResponse200Type0"],
        UnknownError,
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
    wait_for_result: Union[Unset, bool] = UNSET,
) -> Response[
    Union[
        GetFramingDetermineRotationResponse400,
        Union["FramingAssistantInfo", "GetFramingDetermineRotationResponse200Type0"],
        UnknownError,
    ]
]:
    """Determine Rotation

     Determine rotation from camera. This does nothing else than what the button in the framing assistant
    does. If waitForResult is set to true, the method will wait until the rotation is determined. This
    will only work if an image is loaded in the framing assistant

    Args:
        wait_for_result (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFramingDetermineRotationResponse400, Union['FramingAssistantInfo', 'GetFramingDetermineRotationResponse200Type0'], UnknownError]]
    """

    kwargs = _get_kwargs(
        wait_for_result=wait_for_result,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    wait_for_result: Union[Unset, bool] = UNSET,
) -> Optional[
    Union[
        GetFramingDetermineRotationResponse400,
        Union["FramingAssistantInfo", "GetFramingDetermineRotationResponse200Type0"],
        UnknownError,
    ]
]:
    """Determine Rotation

     Determine rotation from camera. This does nothing else than what the button in the framing assistant
    does. If waitForResult is set to true, the method will wait until the rotation is determined. This
    will only work if an image is loaded in the framing assistant

    Args:
        wait_for_result (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFramingDetermineRotationResponse400, Union['FramingAssistantInfo', 'GetFramingDetermineRotationResponse200Type0'], UnknownError]
    """

    return sync_detailed(
        client=client,
        wait_for_result=wait_for_result,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    wait_for_result: Union[Unset, bool] = UNSET,
) -> Response[
    Union[
        GetFramingDetermineRotationResponse400,
        Union["FramingAssistantInfo", "GetFramingDetermineRotationResponse200Type0"],
        UnknownError,
    ]
]:
    """Determine Rotation

     Determine rotation from camera. This does nothing else than what the button in the framing assistant
    does. If waitForResult is set to true, the method will wait until the rotation is determined. This
    will only work if an image is loaded in the framing assistant

    Args:
        wait_for_result (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFramingDetermineRotationResponse400, Union['FramingAssistantInfo', 'GetFramingDetermineRotationResponse200Type0'], UnknownError]]
    """

    kwargs = _get_kwargs(
        wait_for_result=wait_for_result,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    wait_for_result: Union[Unset, bool] = UNSET,
) -> Optional[
    Union[
        GetFramingDetermineRotationResponse400,
        Union["FramingAssistantInfo", "GetFramingDetermineRotationResponse200Type0"],
        UnknownError,
    ]
]:
    """Determine Rotation

     Determine rotation from camera. This does nothing else than what the button in the framing assistant
    does. If waitForResult is set to true, the method will wait until the rotation is determined. This
    will only work if an image is loaded in the framing assistant

    Args:
        wait_for_result (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFramingDetermineRotationResponse400, Union['FramingAssistantInfo', 'GetFramingDetermineRotationResponse200Type0'], UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            wait_for_result=wait_for_result,
        )
    ).parsed

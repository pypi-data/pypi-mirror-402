from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_camera_set_binning_response_200 import GetEquipmentCameraSetBinningResponse200
from ...models.get_equipment_camera_set_binning_response_409 import GetEquipmentCameraSetBinningResponse409
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    binning: str,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["binning"] = binning

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/camera/set-binning",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentCameraSetBinningResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = GetEquipmentCameraSetBinningResponse409.from_dict(response.json())

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
) -> Response[Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    binning: str,
) -> Response[Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]]:
    """Set Binning

     This endpoint sets the binning of the camera, if the specified binning is supported

    Args:
        binning (str):  Example: 2x2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        binning=binning,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    binning: str,
) -> Optional[Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]]:
    """Set Binning

     This endpoint sets the binning of the camera, if the specified binning is supported

    Args:
        binning (str):  Example: 2x2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]
    """

    return sync_detailed(
        client=client,
        binning=binning,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    binning: str,
) -> Response[Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]]:
    """Set Binning

     This endpoint sets the binning of the camera, if the specified binning is supported

    Args:
        binning (str):  Example: 2x2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        binning=binning,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    binning: str,
) -> Optional[Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]]:
    """Set Binning

     This endpoint sets the binning of the camera, if the specified binning is supported

    Args:
        binning (str):  Example: 2x2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentCameraSetBinningResponse200, GetEquipmentCameraSetBinningResponse409, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            binning=binning,
        )
    ).parsed

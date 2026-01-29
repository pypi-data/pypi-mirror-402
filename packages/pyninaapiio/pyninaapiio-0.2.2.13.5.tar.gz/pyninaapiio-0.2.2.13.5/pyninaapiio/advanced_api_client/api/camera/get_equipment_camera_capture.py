from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_equipment_camera_capture_image_type import GetEquipmentCameraCaptureImageType
from ...models.get_equipment_camera_capture_response_200 import GetEquipmentCameraCaptureResponse200
from ...models.get_equipment_camera_capture_response_409 import GetEquipmentCameraCaptureResponse409
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    solve: Union[Unset, bool] = UNSET,
    duration: Union[Unset, float] = UNSET,
    gain: Union[Unset, float] = UNSET,
    get_result: Union[Unset, bool] = UNSET,
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, float] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    omit_image: Union[Unset, bool] = UNSET,
    wait_for_result: Union[Unset, bool] = UNSET,
    target_name: Union[Unset, str] = UNSET,
    save: Union[Unset, bool] = UNSET,
    only_await_capture_completion: Union[Unset, bool] = UNSET,
    only_save_raw: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetEquipmentCameraCaptureImageType] = GetEquipmentCameraCaptureImageType.SNAPSHOT,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["solve"] = solve

    params["duration"] = duration

    params["gain"] = gain

    params["getResult"] = get_result

    params["resize"] = resize

    params["quality"] = quality

    params["size"] = size

    params["scale"] = scale

    params["stream"] = stream

    params["omitImage"] = omit_image

    params["waitForResult"] = wait_for_result

    params["targetName"] = target_name

    params["save"] = save

    params["onlyAwaitCaptureCompletion"] = only_await_capture_completion

    params["onlySaveRaw"] = only_save_raw

    json_image_type: Union[Unset, str] = UNSET
    if not isinstance(image_type, Unset):
        json_image_type = image_type.value

    params["imageType"] = json_image_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/equipment/camera/capture",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetEquipmentCameraCaptureResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = GetEquipmentCameraCaptureResponse409.from_dict(response.json())

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
) -> Response[Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    solve: Union[Unset, bool] = UNSET,
    duration: Union[Unset, float] = UNSET,
    gain: Union[Unset, float] = UNSET,
    get_result: Union[Unset, bool] = UNSET,
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, float] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    omit_image: Union[Unset, bool] = UNSET,
    wait_for_result: Union[Unset, bool] = UNSET,
    target_name: Union[Unset, str] = UNSET,
    save: Union[Unset, bool] = UNSET,
    only_await_capture_completion: Union[Unset, bool] = UNSET,
    only_save_raw: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetEquipmentCameraCaptureImageType] = GetEquipmentCameraCaptureImageType.SNAPSHOT,
) -> Response[Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]]:
    """Capture / Platesolve

     This endpoint captures and/or returns an image. Can optionally solve the image.

    Args:
        solve (Union[Unset, bool]):
        duration (Union[Unset, float]):
        gain (Union[Unset, float]):
        get_result (Union[Unset, bool]):
        resize (Union[Unset, bool]):
        quality (Union[Unset, float]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        stream (Union[Unset, bool]):
        omit_image (Union[Unset, bool]):
        wait_for_result (Union[Unset, bool]):
        target_name (Union[Unset, str]):
        save (Union[Unset, bool]):
        only_await_capture_completion (Union[Unset, bool]):
        only_save_raw (Union[Unset, bool]):
        image_type (Union[Unset, GetEquipmentCameraCaptureImageType]):  Default:
            GetEquipmentCameraCaptureImageType.SNAPSHOT.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        solve=solve,
        duration=duration,
        gain=gain,
        get_result=get_result,
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        stream=stream,
        omit_image=omit_image,
        wait_for_result=wait_for_result,
        target_name=target_name,
        save=save,
        only_await_capture_completion=only_await_capture_completion,
        only_save_raw=only_save_raw,
        image_type=image_type,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    solve: Union[Unset, bool] = UNSET,
    duration: Union[Unset, float] = UNSET,
    gain: Union[Unset, float] = UNSET,
    get_result: Union[Unset, bool] = UNSET,
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, float] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    omit_image: Union[Unset, bool] = UNSET,
    wait_for_result: Union[Unset, bool] = UNSET,
    target_name: Union[Unset, str] = UNSET,
    save: Union[Unset, bool] = UNSET,
    only_await_capture_completion: Union[Unset, bool] = UNSET,
    only_save_raw: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetEquipmentCameraCaptureImageType] = GetEquipmentCameraCaptureImageType.SNAPSHOT,
) -> Optional[Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]]:
    """Capture / Platesolve

     This endpoint captures and/or returns an image. Can optionally solve the image.

    Args:
        solve (Union[Unset, bool]):
        duration (Union[Unset, float]):
        gain (Union[Unset, float]):
        get_result (Union[Unset, bool]):
        resize (Union[Unset, bool]):
        quality (Union[Unset, float]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        stream (Union[Unset, bool]):
        omit_image (Union[Unset, bool]):
        wait_for_result (Union[Unset, bool]):
        target_name (Union[Unset, str]):
        save (Union[Unset, bool]):
        only_await_capture_completion (Union[Unset, bool]):
        only_save_raw (Union[Unset, bool]):
        image_type (Union[Unset, GetEquipmentCameraCaptureImageType]):  Default:
            GetEquipmentCameraCaptureImageType.SNAPSHOT.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]
    """

    return sync_detailed(
        client=client,
        solve=solve,
        duration=duration,
        gain=gain,
        get_result=get_result,
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        stream=stream,
        omit_image=omit_image,
        wait_for_result=wait_for_result,
        target_name=target_name,
        save=save,
        only_await_capture_completion=only_await_capture_completion,
        only_save_raw=only_save_raw,
        image_type=image_type,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    solve: Union[Unset, bool] = UNSET,
    duration: Union[Unset, float] = UNSET,
    gain: Union[Unset, float] = UNSET,
    get_result: Union[Unset, bool] = UNSET,
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, float] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    omit_image: Union[Unset, bool] = UNSET,
    wait_for_result: Union[Unset, bool] = UNSET,
    target_name: Union[Unset, str] = UNSET,
    save: Union[Unset, bool] = UNSET,
    only_await_capture_completion: Union[Unset, bool] = UNSET,
    only_save_raw: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetEquipmentCameraCaptureImageType] = GetEquipmentCameraCaptureImageType.SNAPSHOT,
) -> Response[Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]]:
    """Capture / Platesolve

     This endpoint captures and/or returns an image. Can optionally solve the image.

    Args:
        solve (Union[Unset, bool]):
        duration (Union[Unset, float]):
        gain (Union[Unset, float]):
        get_result (Union[Unset, bool]):
        resize (Union[Unset, bool]):
        quality (Union[Unset, float]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        stream (Union[Unset, bool]):
        omit_image (Union[Unset, bool]):
        wait_for_result (Union[Unset, bool]):
        target_name (Union[Unset, str]):
        save (Union[Unset, bool]):
        only_await_capture_completion (Union[Unset, bool]):
        only_save_raw (Union[Unset, bool]):
        image_type (Union[Unset, GetEquipmentCameraCaptureImageType]):  Default:
            GetEquipmentCameraCaptureImageType.SNAPSHOT.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]]
    """

    kwargs = _get_kwargs(
        solve=solve,
        duration=duration,
        gain=gain,
        get_result=get_result,
        resize=resize,
        quality=quality,
        size=size,
        scale=scale,
        stream=stream,
        omit_image=omit_image,
        wait_for_result=wait_for_result,
        target_name=target_name,
        save=save,
        only_await_capture_completion=only_await_capture_completion,
        only_save_raw=only_save_raw,
        image_type=image_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    solve: Union[Unset, bool] = UNSET,
    duration: Union[Unset, float] = UNSET,
    gain: Union[Unset, float] = UNSET,
    get_result: Union[Unset, bool] = UNSET,
    resize: Union[Unset, bool] = UNSET,
    quality: Union[Unset, float] = UNSET,
    size: Union[Unset, str] = UNSET,
    scale: Union[Unset, float] = UNSET,
    stream: Union[Unset, bool] = UNSET,
    omit_image: Union[Unset, bool] = UNSET,
    wait_for_result: Union[Unset, bool] = UNSET,
    target_name: Union[Unset, str] = UNSET,
    save: Union[Unset, bool] = UNSET,
    only_await_capture_completion: Union[Unset, bool] = UNSET,
    only_save_raw: Union[Unset, bool] = UNSET,
    image_type: Union[Unset, GetEquipmentCameraCaptureImageType] = GetEquipmentCameraCaptureImageType.SNAPSHOT,
) -> Optional[Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]]:
    """Capture / Platesolve

     This endpoint captures and/or returns an image. Can optionally solve the image.

    Args:
        solve (Union[Unset, bool]):
        duration (Union[Unset, float]):
        gain (Union[Unset, float]):
        get_result (Union[Unset, bool]):
        resize (Union[Unset, bool]):
        quality (Union[Unset, float]):
        size (Union[Unset, str]):
        scale (Union[Unset, float]):
        stream (Union[Unset, bool]):
        omit_image (Union[Unset, bool]):
        wait_for_result (Union[Unset, bool]):
        target_name (Union[Unset, str]):
        save (Union[Unset, bool]):
        only_await_capture_completion (Union[Unset, bool]):
        only_save_raw (Union[Unset, bool]):
        image_type (Union[Unset, GetEquipmentCameraCaptureImageType]):  Default:
            GetEquipmentCameraCaptureImageType.SNAPSHOT.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetEquipmentCameraCaptureResponse200, GetEquipmentCameraCaptureResponse409, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            solve=solve,
            duration=duration,
            gain=gain,
            get_result=get_result,
            resize=resize,
            quality=quality,
            size=size,
            scale=scale,
            stream=stream,
            omit_image=omit_image,
            wait_for_result=wait_for_result,
            target_name=target_name,
            save=save,
            only_await_capture_completion=only_await_capture_completion,
            only_save_raw=only_save_raw,
            image_type=image_type,
        )
    ).parsed

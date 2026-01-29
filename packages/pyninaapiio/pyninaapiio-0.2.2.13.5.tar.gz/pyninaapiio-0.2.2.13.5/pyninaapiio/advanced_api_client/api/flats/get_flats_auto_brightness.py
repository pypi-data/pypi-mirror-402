from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_flats_auto_brightness_response_200 import GetFlatsAutoBrightnessResponse200
from ...models.get_flats_auto_brightness_response_400 import GetFlatsAutoBrightnessResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    count: int,
    exposure_time: float,
    min_brightness: Union[Unset, int] = UNSET,
    max_brightness: Union[Unset, int] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
    keep_closed: Union[Unset, bool] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["count"] = count

    params["exposureTime"] = exposure_time

    params["minBrightness"] = min_brightness

    params["maxBrightness"] = max_brightness

    params["histogramMean"] = histogram_mean

    params["meanTolerance"] = mean_tolerance

    params["filterId"] = filter_id

    params["binning"] = binning

    params["gain"] = gain

    params["offset"] = offset

    params["keepClosed"] = keep_closed

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/flats/auto-brightness",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetFlatsAutoBrightnessResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetFlatsAutoBrightnessResponse400.from_dict(response.json())

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
) -> Response[Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    count: int,
    exposure_time: float,
    min_brightness: Union[Unset, int] = UNSET,
    max_brightness: Union[Unset, int] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
    keep_closed: Union[Unset, bool] = UNSET,
) -> Response[Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]]:
    """Auto Brightness Flats

     Start capturing auto brightness flats. This requires the camera to be connected. NINA will pick the
    best flat panel brightness for a fixed exposure time. Any omitted parameter will default to the
    instruction default.

    Args:
        count (int):
        exposure_time (float):
        min_brightness (Union[Unset, int]):
        max_brightness (Union[Unset, int]):
        histogram_mean (Union[Unset, float]):
        mean_tolerance (Union[Unset, float]):
        filter_id (Union[Unset, int]):
        binning (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):
        keep_closed (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        count=count,
        exposure_time=exposure_time,
        min_brightness=min_brightness,
        max_brightness=max_brightness,
        histogram_mean=histogram_mean,
        mean_tolerance=mean_tolerance,
        filter_id=filter_id,
        binning=binning,
        gain=gain,
        offset=offset,
        keep_closed=keep_closed,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    count: int,
    exposure_time: float,
    min_brightness: Union[Unset, int] = UNSET,
    max_brightness: Union[Unset, int] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
    keep_closed: Union[Unset, bool] = UNSET,
) -> Optional[Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]]:
    """Auto Brightness Flats

     Start capturing auto brightness flats. This requires the camera to be connected. NINA will pick the
    best flat panel brightness for a fixed exposure time. Any omitted parameter will default to the
    instruction default.

    Args:
        count (int):
        exposure_time (float):
        min_brightness (Union[Unset, int]):
        max_brightness (Union[Unset, int]):
        histogram_mean (Union[Unset, float]):
        mean_tolerance (Union[Unset, float]):
        filter_id (Union[Unset, int]):
        binning (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):
        keep_closed (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        count=count,
        exposure_time=exposure_time,
        min_brightness=min_brightness,
        max_brightness=max_brightness,
        histogram_mean=histogram_mean,
        mean_tolerance=mean_tolerance,
        filter_id=filter_id,
        binning=binning,
        gain=gain,
        offset=offset,
        keep_closed=keep_closed,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    count: int,
    exposure_time: float,
    min_brightness: Union[Unset, int] = UNSET,
    max_brightness: Union[Unset, int] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
    keep_closed: Union[Unset, bool] = UNSET,
) -> Response[Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]]:
    """Auto Brightness Flats

     Start capturing auto brightness flats. This requires the camera to be connected. NINA will pick the
    best flat panel brightness for a fixed exposure time. Any omitted parameter will default to the
    instruction default.

    Args:
        count (int):
        exposure_time (float):
        min_brightness (Union[Unset, int]):
        max_brightness (Union[Unset, int]):
        histogram_mean (Union[Unset, float]):
        mean_tolerance (Union[Unset, float]):
        filter_id (Union[Unset, int]):
        binning (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):
        keep_closed (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        count=count,
        exposure_time=exposure_time,
        min_brightness=min_brightness,
        max_brightness=max_brightness,
        histogram_mean=histogram_mean,
        mean_tolerance=mean_tolerance,
        filter_id=filter_id,
        binning=binning,
        gain=gain,
        offset=offset,
        keep_closed=keep_closed,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    count: int,
    exposure_time: float,
    min_brightness: Union[Unset, int] = UNSET,
    max_brightness: Union[Unset, int] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
    keep_closed: Union[Unset, bool] = UNSET,
) -> Optional[Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]]:
    """Auto Brightness Flats

     Start capturing auto brightness flats. This requires the camera to be connected. NINA will pick the
    best flat panel brightness for a fixed exposure time. Any omitted parameter will default to the
    instruction default.

    Args:
        count (int):
        exposure_time (float):
        min_brightness (Union[Unset, int]):
        max_brightness (Union[Unset, int]):
        histogram_mean (Union[Unset, float]):
        mean_tolerance (Union[Unset, float]):
        filter_id (Union[Unset, int]):
        binning (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):
        keep_closed (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFlatsAutoBrightnessResponse200, GetFlatsAutoBrightnessResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            count=count,
            exposure_time=exposure_time,
            min_brightness=min_brightness,
            max_brightness=max_brightness,
            histogram_mean=histogram_mean,
            mean_tolerance=mean_tolerance,
            filter_id=filter_id,
            binning=binning,
            gain=gain,
            offset=offset,
            keep_closed=keep_closed,
        )
    ).parsed

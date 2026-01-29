from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_flats_skyflat_response_200 import GetFlatsSkyflatResponse200
from ...models.get_flats_skyflat_response_400 import GetFlatsSkyflatResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    count: int,
    min_exposure: Union[Unset, float] = UNSET,
    max_exposure: Union[Unset, float] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    dither: Union[Unset, bool] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["count"] = count

    params["minExposure"] = min_exposure

    params["maxExposure"] = max_exposure

    params["histogramMean"] = histogram_mean

    params["meanTolerance"] = mean_tolerance

    params["dither"] = dither

    params["filterId"] = filter_id

    params["binning"] = binning

    params["gain"] = gain

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/flats/skyflat",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetFlatsSkyflatResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetFlatsSkyflatResponse400.from_dict(response.json())

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
) -> Response[Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]]:
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
    min_exposure: Union[Unset, float] = UNSET,
    max_exposure: Union[Unset, float] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    dither: Union[Unset, bool] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Response[Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]]:
    """Sky flats

     Start capturing sky flats. This requires the camera and mount to be connected. Any omitted parameter
    will default to the instruction default.

    Args:
        count (int):
        min_exposure (Union[Unset, float]):
        max_exposure (Union[Unset, float]):
        histogram_mean (Union[Unset, float]):
        mean_tolerance (Union[Unset, float]):
        dither (Union[Unset, bool]):
        filter_id (Union[Unset, int]):
        binning (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        count=count,
        min_exposure=min_exposure,
        max_exposure=max_exposure,
        histogram_mean=histogram_mean,
        mean_tolerance=mean_tolerance,
        dither=dither,
        filter_id=filter_id,
        binning=binning,
        gain=gain,
        offset=offset,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    count: int,
    min_exposure: Union[Unset, float] = UNSET,
    max_exposure: Union[Unset, float] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    dither: Union[Unset, bool] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Optional[Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]]:
    """Sky flats

     Start capturing sky flats. This requires the camera and mount to be connected. Any omitted parameter
    will default to the instruction default.

    Args:
        count (int):
        min_exposure (Union[Unset, float]):
        max_exposure (Union[Unset, float]):
        histogram_mean (Union[Unset, float]):
        mean_tolerance (Union[Unset, float]):
        dither (Union[Unset, bool]):
        filter_id (Union[Unset, int]):
        binning (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        count=count,
        min_exposure=min_exposure,
        max_exposure=max_exposure,
        histogram_mean=histogram_mean,
        mean_tolerance=mean_tolerance,
        dither=dither,
        filter_id=filter_id,
        binning=binning,
        gain=gain,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    count: int,
    min_exposure: Union[Unset, float] = UNSET,
    max_exposure: Union[Unset, float] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    dither: Union[Unset, bool] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Response[Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]]:
    """Sky flats

     Start capturing sky flats. This requires the camera and mount to be connected. Any omitted parameter
    will default to the instruction default.

    Args:
        count (int):
        min_exposure (Union[Unset, float]):
        max_exposure (Union[Unset, float]):
        histogram_mean (Union[Unset, float]):
        mean_tolerance (Union[Unset, float]):
        dither (Union[Unset, bool]):
        filter_id (Union[Unset, int]):
        binning (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        count=count,
        min_exposure=min_exposure,
        max_exposure=max_exposure,
        histogram_mean=histogram_mean,
        mean_tolerance=mean_tolerance,
        dither=dither,
        filter_id=filter_id,
        binning=binning,
        gain=gain,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    count: int,
    min_exposure: Union[Unset, float] = UNSET,
    max_exposure: Union[Unset, float] = UNSET,
    histogram_mean: Union[Unset, float] = UNSET,
    mean_tolerance: Union[Unset, float] = UNSET,
    dither: Union[Unset, bool] = UNSET,
    filter_id: Union[Unset, int] = UNSET,
    binning: Union[Unset, str] = UNSET,
    gain: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Optional[Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]]:
    """Sky flats

     Start capturing sky flats. This requires the camera and mount to be connected. Any omitted parameter
    will default to the instruction default.

    Args:
        count (int):
        min_exposure (Union[Unset, float]):
        max_exposure (Union[Unset, float]):
        histogram_mean (Union[Unset, float]):
        mean_tolerance (Union[Unset, float]):
        dither (Union[Unset, bool]):
        filter_id (Union[Unset, int]):
        binning (Union[Unset, str]):
        gain (Union[Unset, int]):
        offset (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetFlatsSkyflatResponse200, GetFlatsSkyflatResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            count=count,
            min_exposure=min_exposure,
            max_exposure=max_exposure,
            histogram_mean=histogram_mean,
            mean_tolerance=mean_tolerance,
            dither=dither,
            filter_id=filter_id,
            binning=binning,
            gain=gain,
            offset=offset,
        )
    ).parsed

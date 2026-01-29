from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_profile_change_value_new_value import GetProfileChangeValueNewValue
from ...models.get_profile_change_value_response_200 import GetProfileChangeValueResponse200
from ...models.get_profile_change_value_response_400 import GetProfileChangeValueResponse400
from ...models.unknown_error import UnknownError
from ...types import UNSET, Response


def _get_kwargs(
    *,
    settingpath: str,
    new_value: "GetProfileChangeValueNewValue",
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["settingpath"] = settingpath

    json_new_value = new_value.to_dict()
    params.update(json_new_value)

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/profile/change-value",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetProfileChangeValueResponse200.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = GetProfileChangeValueResponse400.from_dict(response.json())

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
) -> Response[Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    settingpath: str,
    new_value: "GetProfileChangeValueNewValue",
) -> Response[Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]]:
    """Change Profile Value

     Changes a value in the profile

    Args:
        settingpath (str):  Example: CameraSettings-PixelSize.
        new_value (GetProfileChangeValueNewValue):  Example: 3.2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        settingpath=settingpath,
        new_value=new_value,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    settingpath: str,
    new_value: "GetProfileChangeValueNewValue",
) -> Optional[Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]]:
    """Change Profile Value

     Changes a value in the profile

    Args:
        settingpath (str):  Example: CameraSettings-PixelSize.
        new_value (GetProfileChangeValueNewValue):  Example: 3.2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]
    """

    return sync_detailed(
        client=client,
        settingpath=settingpath,
        new_value=new_value,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    settingpath: str,
    new_value: "GetProfileChangeValueNewValue",
) -> Response[Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]]:
    """Change Profile Value

     Changes a value in the profile

    Args:
        settingpath (str):  Example: CameraSettings-PixelSize.
        new_value (GetProfileChangeValueNewValue):  Example: 3.2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]]
    """

    kwargs = _get_kwargs(
        settingpath=settingpath,
        new_value=new_value,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    settingpath: str,
    new_value: "GetProfileChangeValueNewValue",
) -> Optional[Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]]:
    """Change Profile Value

     Changes a value in the profile

    Args:
        settingpath (str):  Example: CameraSettings-PixelSize.
        new_value (GetProfileChangeValueNewValue):  Example: 3.2.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetProfileChangeValueResponse200, GetProfileChangeValueResponse400, UnknownError]
    """

    return (
        await asyncio_detailed(
            client=client,
            settingpath=settingpath,
            new_value=new_value,
        )
    ).parsed

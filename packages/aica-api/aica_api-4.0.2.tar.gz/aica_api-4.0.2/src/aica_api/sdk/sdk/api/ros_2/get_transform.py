from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.transform import Transform
from ...types import UNSET, Response, Unset


def _get_kwargs(
    frame: str,
    *,
    reference_frame: Union[Unset, str] = "world",
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["reference_frame"] = reference_frame

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v3/ros/transforms/{frame}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorResponse, Transform]]:
    if response.status_code == 200:
        response_200 = Transform.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorResponse, Transform]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    frame: str,
    *,
    client: AuthenticatedClient,
    reference_frame: Union[Unset, str] = "world",
) -> Response[Union[ErrorResponse, Transform]]:
    """Lookup a transform from the TF buffer

    Args:
        frame (str):
        reference_frame (Union[Unset, str]):  Default: 'world'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, Transform]]
    """

    kwargs = _get_kwargs(
        frame=frame,
        reference_frame=reference_frame,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    frame: str,
    *,
    client: AuthenticatedClient,
    reference_frame: Union[Unset, str] = "world",
) -> Optional[Union[ErrorResponse, Transform]]:
    """Lookup a transform from the TF buffer

    Args:
        frame (str):
        reference_frame (Union[Unset, str]):  Default: 'world'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, Transform]
    """

    return sync_detailed(
        frame=frame,
        client=client,
        reference_frame=reference_frame,
    ).parsed


async def asyncio_detailed(
    frame: str,
    *,
    client: AuthenticatedClient,
    reference_frame: Union[Unset, str] = "world",
) -> Response[Union[ErrorResponse, Transform]]:
    """Lookup a transform from the TF buffer

    Args:
        frame (str):
        reference_frame (Union[Unset, str]):  Default: 'world'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, Transform]]
    """

    kwargs = _get_kwargs(
        frame=frame,
        reference_frame=reference_frame,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    frame: str,
    *,
    client: AuthenticatedClient,
    reference_frame: Union[Unset, str] = "world",
) -> Optional[Union[ErrorResponse, Transform]]:
    """Lookup a transform from the TF buffer

    Args:
        frame (str):
        reference_frame (Union[Unset, str]):  Default: 'world'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, Transform]
    """

    return (
        await asyncio_detailed(
            frame=frame,
            client=client,
            reference_frame=reference_frame,
        )
    ).parsed

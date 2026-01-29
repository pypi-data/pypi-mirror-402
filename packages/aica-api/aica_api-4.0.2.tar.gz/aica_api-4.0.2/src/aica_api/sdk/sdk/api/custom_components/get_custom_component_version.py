from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.custom_component_version import CustomComponentVersion
from ...models.error_response import ErrorResponse
from ...types import Response


def _get_kwargs(
    id: UUID,
    version_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v3/custom-components/{id}/version/{version_id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CustomComponentVersion, ErrorResponse]]:
    if response.status_code == 200:
        response_200 = CustomComponentVersion.from_dict(response.json())

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
) -> Response[Union[CustomComponentVersion, ErrorResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    version_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Union[CustomComponentVersion, ErrorResponse]]:
    """Get a specific version of a custom component

    Args:
        id (UUID):
        version_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CustomComponentVersion, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        id=id,
        version_id=version_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    version_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[CustomComponentVersion, ErrorResponse]]:
    """Get a specific version of a custom component

    Args:
        id (UUID):
        version_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CustomComponentVersion, ErrorResponse]
    """

    return sync_detailed(
        id=id,
        version_id=version_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    version_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Union[CustomComponentVersion, ErrorResponse]]:
    """Get a specific version of a custom component

    Args:
        id (UUID):
        version_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CustomComponentVersion, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        id=id,
        version_id=version_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    version_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[CustomComponentVersion, ErrorResponse]]:
    """Get a specific version of a custom component

    Args:
        id (UUID):
        version_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CustomComponentVersion, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            id=id,
            version_id=version_id,
            client=client,
        )
    ).parsed

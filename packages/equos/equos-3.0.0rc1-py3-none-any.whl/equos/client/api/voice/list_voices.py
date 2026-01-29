from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_equos_voices_response import ListEquosVoicesResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    take: float | Unset = 20.0,
    skip: float | Unset = 0.0,
    client_query: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["take"] = take

    params["skip"] = skip

    params["client"] = client_query

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v3/voices",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ListEquosVoicesResponse | None:
    if response.status_code == 200:
        response_200 = ListEquosVoicesResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ListEquosVoicesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    take: float | Unset = 20.0,
    skip: float | Unset = 0.0,
    client_query: str | Unset = UNSET,
) -> Response[ListEquosVoicesResponse]:
    """List Equos Voices.

    Args:
        take (float | Unset):  Default: 20.0.
        skip (float | Unset):  Default: 0.0.
        client_query (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListEquosVoicesResponse]
    """

    kwargs = _get_kwargs(
        take=take,
        skip=skip,
        client_query=client_query,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    take: float | Unset = 20.0,
    skip: float | Unset = 0.0,
    client_query: str | Unset = UNSET,
) -> ListEquosVoicesResponse | None:
    """List Equos Voices.

    Args:
        take (float | Unset):  Default: 20.0.
        skip (float | Unset):  Default: 0.0.
        client_query (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListEquosVoicesResponse
    """

    return sync_detailed(
        client=client,
        take=take,
        skip=skip,
        client_query=client_query,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    take: float | Unset = 20.0,
    skip: float | Unset = 0.0,
    client_query: str | Unset = UNSET,
) -> Response[ListEquosVoicesResponse]:
    """List Equos Voices.

    Args:
        take (float | Unset):  Default: 20.0.
        skip (float | Unset):  Default: 0.0.
        client_query (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListEquosVoicesResponse]
    """

    kwargs = _get_kwargs(
        take=take,
        skip=skip,
        client_query=client_query,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    take: float | Unset = 20.0,
    skip: float | Unset = 0.0,
    client_query: str | Unset = UNSET,
) -> ListEquosVoicesResponse | None:
    """List Equos Voices.

    Args:
        take (float | Unset):  Default: 20.0.
        skip (float | Unset):  Default: 0.0.
        client_query (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListEquosVoicesResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            take=take,
            skip=skip,
            client_query=client_query,
        )
    ).parsed

from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.equos_document import EquosDocument
from ...types import Response


def _get_kwargs(
    id: str,
    doc: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v3/knowledge-bases/{id}/documents/{doc}/index".format(
            id=quote(str(id), safe=""),
            doc=quote(str(doc), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> EquosDocument | None:
    if response.status_code == 200:
        response_200 = EquosDocument.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[EquosDocument]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    doc: str,
    *,
    client: AuthenticatedClient,
) -> Response[EquosDocument]:
    """Index a document in a Knowledge Base.

    Args:
        id (str):
        doc (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EquosDocument]
    """

    kwargs = _get_kwargs(
        id=id,
        doc=doc,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    doc: str,
    *,
    client: AuthenticatedClient,
) -> EquosDocument | None:
    """Index a document in a Knowledge Base.

    Args:
        id (str):
        doc (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EquosDocument
    """

    return sync_detailed(
        id=id,
        doc=doc,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: str,
    doc: str,
    *,
    client: AuthenticatedClient,
) -> Response[EquosDocument]:
    """Index a document in a Knowledge Base.

    Args:
        id (str):
        doc (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EquosDocument]
    """

    kwargs = _get_kwargs(
        id=id,
        doc=doc,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    doc: str,
    *,
    client: AuthenticatedClient,
) -> EquosDocument | None:
    """Index a document in a Knowledge Base.

    Args:
        id (str):
        doc (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EquosDocument
    """

    return (
        await asyncio_detailed(
            id=id,
            doc=doc,
            client=client,
        )
    ).parsed

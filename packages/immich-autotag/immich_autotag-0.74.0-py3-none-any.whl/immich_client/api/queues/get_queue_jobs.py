from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.queue_job_response_dto import QueueJobResponseDto
from ...models.queue_job_status import QueueJobStatus
from ...models.queue_name import QueueName
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: QueueName,
    *,
    status: list[QueueJobStatus] | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_status: list[str] | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = []
        for status_item_data in status:
            status_item = status_item_data.value
            json_status.append(status_item)

    params["status"] = json_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/queues/{name}/jobs".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> list[QueueJobResponseDto] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = QueueJobResponseDto.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[list[QueueJobResponseDto]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: QueueName,
    *,
    client: AuthenticatedClient,
    status: list[QueueJobStatus] | Unset = UNSET,
) -> Response[list[QueueJobResponseDto]]:
    """Retrieve queue jobs

     Retrieves a list of queue jobs from the specified queue.

    Args:
        name (QueueName):
        status (list[QueueJobStatus] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[QueueJobResponseDto]]
    """

    kwargs = _get_kwargs(
        name=name,
        status=status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: QueueName,
    *,
    client: AuthenticatedClient,
    status: list[QueueJobStatus] | Unset = UNSET,
) -> list[QueueJobResponseDto] | None:
    """Retrieve queue jobs

     Retrieves a list of queue jobs from the specified queue.

    Args:
        name (QueueName):
        status (list[QueueJobStatus] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[QueueJobResponseDto]
    """

    return sync_detailed(
        name=name,
        client=client,
        status=status,
    ).parsed


async def asyncio_detailed(
    name: QueueName,
    *,
    client: AuthenticatedClient,
    status: list[QueueJobStatus] | Unset = UNSET,
) -> Response[list[QueueJobResponseDto]]:
    """Retrieve queue jobs

     Retrieves a list of queue jobs from the specified queue.

    Args:
        name (QueueName):
        status (list[QueueJobStatus] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[QueueJobResponseDto]]
    """

    kwargs = _get_kwargs(
        name=name,
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: QueueName,
    *,
    client: AuthenticatedClient,
    status: list[QueueJobStatus] | Unset = UNSET,
) -> list[QueueJobResponseDto] | None:
    """Retrieve queue jobs

     Retrieves a list of queue jobs from the specified queue.

    Args:
        name (QueueName):
        status (list[QueueJobStatus] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[QueueJobResponseDto]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            status=status,
        )
    ).parsed

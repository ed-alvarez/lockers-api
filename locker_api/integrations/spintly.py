import httpx
from config import get_spintly_config

from .request_util import build_headers
from .types import SpintlyTokenResponse


async def get_token(client: httpx.AsyncClient) -> httpx.Response:
    settings = get_spintly_config()
    data = dict(
        grant_type="urn:ietf:params:oauth:grant-type:client-credentials",
        client_id=f"{settings.client_id}",
        client_secret=f"{settings.client_secret}",
    )
    response = await client.post(
        url="https://acaas.api.spintly.com/identityManagement/v2/oauth/token", data=data
    )

    return response


async def activate(
    client: httpx.AsyncClient, token: SpintlyTokenResponse, access_point_id: int
) -> httpx.Response:
    headers = build_headers(token=token)
    data = dict(accessPointId=access_point_id)
    response = await client.post(
        url="https://acaas.api.spintly.com/acaasController/v2/remoteAccess",
        json=data,
        headers=headers,
    )
    return response


async def get_sites(
    client: httpx.AsyncClient, token: SpintlyTokenResponse
) -> httpx.Response:
    headers = build_headers(token=token)

    response = await client.get(
        url="https://acaas.api.spintly.com/permissionManagement/v2/sites",
        headers=headers,
    )

    return response


async def get_access_points(
    site_id: int, client: httpx.AsyncClient, token: SpintlyTokenResponse
) -> httpx.Response:
    headers = build_headers(token=token)

    response = await client.get(
        url=f"https://acaas.api.spintly.com/permissionManagement/v2/sites/{site_id}/accessPoint",
        headers=headers,
    )

    return response

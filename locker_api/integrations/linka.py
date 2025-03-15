import httpx
from config import get_linka_config
from fastapi import HTTPException

from .types import LinkaMessage, LinkaTokenResponse


class LinkaResponseBoundsException(Exception):
    message = "Device error: Returned response outside of HTTP/1.1 standard specifications. Please check your device and try again."


async def get_token() -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(
        api_key=f"{_linka_config.api_key}",
        secret_key=f"{_linka_config.secret_key}",
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{_linka_config.root_url}/fetch_access_token", data=data
        )
        resp = response.json()

    return LinkaTokenResponse.parse_obj(resp["data"])


async def test_token(token: LinkaTokenResponse) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(
        access_token=f"{token.access_token}",
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{_linka_config.root_url}/test_access_token", data=data
        )

    return response


async def unlock(
    token: LinkaTokenResponse,
    mac_addr: str,
) -> LinkaMessage:
    return await command(token=token, mac_addr=mac_addr, command="unlock")


async def command(
    token: LinkaTokenResponse,
    command: str,  # lock, unlock, siren
    mac_addr: str,
) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(access_token=f"{token.access_token}", mac_addr=f"{mac_addr}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url=f"{_linka_config.root_url}/command_{command}", data=data
            )
        except httpx.RemoteProtocolError:
            raise HTTPException(
                status_code=400,
                detail="Failed to unlock linka device, make sure the device is properly connected via cellular and try again",
            )

    return response


async def modify_lock_setting(
    client: httpx.AsyncClient,
    token: LinkaTokenResponse,
    mac_addr: str,
) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(
        access_token=f"{token.access_token}",
        mac_addr=f"{mac_addr}",
    )
    response = await client.post(
        url=f"{_linka_config.root_url}/modify_settings_lock", data=data
    )

    return response


async def modify_global_setting(
    client: httpx.AsyncClient,
    token: LinkaTokenResponse,
) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(
        access_token=f"{token.access_token}",
    )
    response = await client.post(
        url=f"{_linka_config.root_url}/modify_settings_global", data=data
    )

    return response


async def get_lock_setting(
    client: httpx.AsyncClient,
    token: LinkaTokenResponse,
    mac_addr: str,
) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(
        access_token=f"{token.access_token}",
        mac_addr=f"{mac_addr}",
    )
    response = await client.post(
        url=f"{_linka_config.root_url}/get_settings_lock", data=data
    )

    return response


async def get_global_setting(
    client: httpx.AsyncClient,
    token: LinkaTokenResponse,
) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(
        access_token=f"{token.access_token}",
    )
    response = await client.post(
        url=f"{_linka_config.root_url}/get_settings_global", data=data
    )

    return response


async def sim_conn(
    client: httpx.AsyncClient, token: LinkaTokenResponse, mac_addr: str
) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(token=f"{token.access_token}", mac_addr=f"{mac_addr}")

    response = await client.post(
        url=f"{_linka_config.root_url}/sim_connection", data=data
    )

    return response


async def command_status(
    client: httpx.AsyncClient, token: LinkaTokenResponse, command_id: str
) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(token=f"{token.access_token}", command_id=f"{command_id}")

    response = await client.post(
        url=f"{_linka_config.root_url}/get_remote_command", data=data
    )

    return response


async def latest_location(
    client: httpx.AsyncClient, token: LinkaTokenResponse, mac_addr: str
) -> httpx.Response:
    _linka_config = get_linka_config()
    data = dict(token=f"{token.access_token}", mac_addr=f"{mac_addr}")

    response = await client.post(url=f"{_linka_config.root_url}/gps_latest", data=data)

    return response

from urllib.parse import urlencode
from uuid import UUID

import httpx
from config import get_harbor_config
from fastapi import HTTPException


class LockerStatus:
    name: str
    id: int


class LockerType:
    name: str
    description: str
    id: int


class HarborLocker:
    id: int
    name: str
    isLowLocker: bool
    towerId: str
    status: LockerStatus
    type: LockerType


class HarborLockerStep:
    dropoff = "dropoff"
    pickup = "pickup"


class SessionLockerTokenResponse:
    tower_id: str
    locker: HarborLocker
    payload_auth: str
    payload: str
    expires: str


async def get_harbor_client():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "client_credentials",
        "client_id": get_harbor_config().client_id,
        "client_secret": get_harbor_config().client_secret,
        "scope": "service_provider",
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=get_harbor_config().login_api_url,
            headers=headers,
            content=urlencode(data),
        )

        print("Attempting to create Harbor client")

        print(res.json())

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail="Failed to create Harbor client",
            )

        return res.json()["access_token"]


async def get_harbor_sdk_client():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "client_credentials",
        "client_id": get_harbor_config().client_id,
        "client_secret": get_harbor_config().client_secret,
        "scope": "tower_access",
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=get_harbor_config().login_api_url,
            headers=headers,
            content=urlencode(data),
        )

        print("Attempting to create Harbor SDK client")

        print(res.json())

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail="Failed to create SDK Harbor client",
            )

        return res.json()["access_token"]


async def cancel_reservation(
    svc_token: str,  # Authentication token generated by get_client()
    reservation_id: str,
):
    url = f"{get_harbor_config().api_url}/api/v1/towers/reservations/{reservation_id}/cancel"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {svc_token}",
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=url,
            headers=headers,
        )

        print(res.json())

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail=f"Failed to cancel Harbor reservation {reservation_id}",
            )

        return res.json()


async def create_reservation(
    svc_token: str,  # Authentication token generated by get_client()
    tower_id: str,
    locker_id: str,
):
    url = f"{get_harbor_config().api_url}/api/v1/towers/{tower_id}/lockers/{locker_id}/reservations"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {svc_token}",
    }

    data = {"duration": 300}

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=url,
            headers=headers,
            json=data,
        )

        print(res.json())

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail=f"Failed to reserve for Harbor tower {tower_id}",
            )

        return res.json()["id"]


async def create_session(tower_id: str):
    svc_token = await get_harbor_sdk_client()

    url = f"{get_harbor_config().api_url}/sdk/v1/towers/{tower_id}/session-token"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {svc_token}",
    }

    print(f"Attempting to create session token for Harbor tower {tower_id}")

    data = {"duration": 300, "claims": ["owner"], "version": "0.10.6"}

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=url,
            headers=headers,
            json=data,
        )

        print(res)

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail=f"Failed to create session for Harbor tower {tower_id}",
            )

        return res.json()


async def get_tower_lockers(
    tower_id: str,
    svc_token: str,  # Authentication token generated by get_client()
):
    url = f"{get_harbor_config().api_url}/api/v1/towers/{tower_id}/lockers"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {svc_token}",
    }

    print(f"Attempting to get available lockers for Harbor tower {tower_id}")

    async with httpx.AsyncClient() as client:
        res = await client.get(
            url=url,
            headers=headers,
        )

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail=f"Failed to get available lockers for Harbor tower {tower_id}",
            )

        return res.json()


async def create_locker_token(
    svc_token: str,  # Authentication token generated by get_client()
    tower_id: str,
    locker_id: str,
    step: HarborLockerStep,
    device_uuid: UUID,  # Custom information to associate with token
) -> SessionLockerTokenResponse | HTTPException:
    url = f"{get_harbor_config().api_url}/api/v1/towers/{tower_id}/lockers/{locker_id}/{step}-locker-tokens"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {svc_token}",
    }

    print(f"Attempting to create locker token for Harbor tower {tower_id}")

    data = {"duration": 300, "client_info": str(device_uuid)}

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=url,
            headers=headers,
            json=data,
        )

        json_data = res.json()

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail=f"Failed to create {step} session for Harbor tower {tower_id}. {json_data['detail']}",
            )

        return res.json()

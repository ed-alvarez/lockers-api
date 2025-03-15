from uuid import UUID

import httpx
from config import get_keynius_config
from fastapi import HTTPException


async def get_client():
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": get_keynius_config().sub_key,
    }

    data = {
        "email": get_keynius_config().email,
        "password": get_keynius_config().password,
        "deviceId": get_keynius_config().device_id,
        "platform": "Web",
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=f"{get_keynius_config().api_url}/Account/login",
            headers=headers,
            json=data,
        )

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail="Keynius API failed to unlock device. Unable to create"
                + " Keynius connection.",
            )

        return res.json()["result"]


async def unlock(token: str, locker_id: UUID):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Ocp-Apim-Subscription-Key": get_keynius_config().sub_key,
    }

    print(f"Attempting to unlock Keynius device {locker_id}")

    data = {"lockerId": locker_id, "lockerOpenType": 1}

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url=f"{get_keynius_config().api_url}/SmartHubUsers/OpenLocker",
            headers=headers,
            json=data,
        )

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail="Keynius API failed to unlock device. Please check"
                + " the device is connected and the ID is correct.",
            )

        return res.json()

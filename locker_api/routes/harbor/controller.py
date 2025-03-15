from integrations.harbor import (
    create_locker_token,
    get_harbor_client,
    get_harbor_sdk_client,
    get_tower_lockers,
)


async def get_available_lockers(
    tower_id: str,
    svc_token: str,
):
    # {
    #     "id": 363,
    #     "name": "57",
    #     "isLowLocker": false,
    #     "towerId": "0100000000000014",
    #     "status": {"name": "available", "id": 1},
    #     "type": {"name": "small", "description": null, "id": 1},
    # }

    lockers = await get_tower_lockers(
        tower_id=tower_id,
        svc_token=svc_token,
    )

    available_lockers = []

    for lock in lockers:
        if lock["status"]["name"] == "available":
            available_lockers.append(lock)

    return available_lockers


async def generate_access_tokens():
    api_access_token = await get_harbor_client()

    sdk_access_token = await get_harbor_sdk_client()

    return {
        "api_access_token": api_access_token,
        "sdk_access_token": sdk_access_token,
    }


async def generate_locker_token(
    tower_id: str,
    locker_id: str,
    step: str,
    svc_token: str,  # Service Provider token used to generate Dropoff/Pickup token
):
    token = await create_locker_token(
        tower_id=tower_id,
        locker_id=locker_id,
        step=step,
        svc_token=svc_token,
        device_uuid=tower_id,
    )

    return token

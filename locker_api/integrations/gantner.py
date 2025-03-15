import json

import asyncpg
from config import get_settings
from util.connection_manager import connection_manager
from routes.logger.controller import add_to_logger_gantner
from routes.logger.model import LogType


async def connect_to_database():
    connection = await asyncpg.connect(
        user=get_settings().database_user,
        password=get_settings().database_password,
        host=get_settings().database_host,
        port=str(get_settings().database_port),
        database=get_settings().database_name,
    )

    return connection


async def unlock(locker_id: str):
    await connection_manager.broadcast(
        json.dumps({"Cmd": "App.Locks.Get", "MT": "Req", "TID": 1336, "Data": {}})
    )

    await connection_manager.broadcast(
        json.dumps(
            {
                "Cmd": "App.SetLockState",
                "MT": "Req",
                "TID": 1337,
                "Data": {"Id": locker_id, "LockStatus": "Unlock"},
            }
        )
    )
    connection = await connect_to_database()

    await connection.execute(
        "UPDATE device SET lock_status = $1 WHERE gantner_id = $2",
        "open",
        locker_id,
    )


async def refresh_gantner_lock_states(sql_pool, data):
    try:
        for lock in data["Locks"]:
            print(f"Updating lock {lock['Id']} to {lock['Status']['LockStatus']}")

            async with sql_pool.acquire() as connection:
                await connection.fetch(
                    "UPDATE device SET lock_status = $1 WHERE gantner_id = $2",
                    lock["Status"]["LockStatus"].lower(),
                    lock["Id"],
                )
                await add_to_logger_gantner(
                    lock["Id"],
                    LogType.lock
                    if lock["Status"]["LockStatus"].lower() == "locked"
                    else LogType.unlock,
                )

    except KeyError as e:
        print(f"Error: {e}")
        print("Gantner Data: ", data)


async def refresh_gantner_lock(sql_pool, data):
    async with sql_pool.acquire() as connection:
        await connection.fetch(
            "UPDATE device SET lock_status = $1 WHERE gantner_id = $2",
            data["Status"]["LockStatus"].lower(),
            data["Id"],
        )

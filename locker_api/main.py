import json
import logging
import asyncpg
import sentry_sdk
import uuid
import uvicorn
from gmqtt import Client as MQTTClient
from async_stripe import stripe
from botocore.errorfactory import ClientError
from config import get_settings
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from httpx import Request
from integrations.gantner import refresh_gantner_lock, refresh_gantner_lock_states
from pydantic import PostgresDsn
from redis import asyncio as aioredis
from routes.router import central_router
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.pool import NullPool
from twilio.base.exceptions import TwilioRestException
from util.connection_manager import connection_manager
from util.exception import format_error
from routes.logger.controller import add_to_logger_dclock
from routes.logger.model import LogType

from util.scheduler import start_scheduler

# from rate_limit.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="Koloni API",
    version="3.0.0",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

app.include_router(central_router, prefix="/v3")

# Add CORS middleware

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Add SQLAlchemy middleware
app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=PostgresDsn.build(
        scheme="postgresql+asyncpg",
        user=get_settings().database_user,
        password=get_settings().database_password,
        host=get_settings().database_host,
        port=str(get_settings().database_port),
        path=f"/{get_settings().database_name}",
    ),
    engine_args={
        "echo": False,
        "pool_pre_ping": True,
        # "pool_size": get_settings().pool_size,
        # "max_overflow": 64,
        "poolclass": NullPool,
    },
)

# Add LimitUploadSize middleware
# app.add_middleware(LimitUploadSize, max_upload_size=get_settings().MAX_REQ_SIZE)

# Add Sentry middleware if environment is not local
if get_settings().environment != "local":
    sentry_sdk.init(
        dsn=get_settings().sentry_dsn,
        traces_sample_rate=0.2,
        environment=get_settings().environment,
        release="2.0.0",
    )
    app.add_middleware(SentryAsgiMiddleware)


@app.on_event("startup")
async def startup_event():
    start_scheduler()
    redis = aioredis.from_url(get_settings().redis_url)
    db = await create_pool()

    await redis.flushall()
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache", expire=600)
    client = MQTTClient(str(uuid.uuid4()))

    client.set_auth_credentials(get_settings().mqtt_user, get_settings().mqtt_pass)

    handler = DcClient(db, redis)

    client.on_connect = on_connect
    client.on_message = handler.update_dclock

    await client.connect(get_settings().mqtt_host, get_settings().mqtt_port, True)


# Redirect to koloni.io
@app.get("/")
async def root():
    return RedirectResponse(url="https://www.koloni.io")


async def create_pool():
    db_params = {
        "user": get_settings().database_user,
        "password": get_settings().database_password,
        "host": get_settings().database_host,
        "port": str(get_settings().database_port),
        "database": get_settings().database_name,
    }

    pool = await asyncpg.create_pool(
        **db_params,
        min_size=2,
        max_size=8,
    )

    return pool


def on_connect(client, flags, rc, properties):
    client.subscribe("/status")
    print("Connected to MQTT Broker")


class DcClient:
    db: asyncpg.Pool = None
    redis: aioredis.Redis = None

    def __init__(self, db, redis):
        self.db = db
        self.redis = redis

    async def update_dclock(self, client, topic, payload, qos, properties):
        # "5ae5b5159f862c28,1,0 : Door closed and has something in box"
        payload_str: str = payload.decode()
        payload = payload_str.split(",")

        curr_val = await self.redis.get(f"{payload[0]}:{payload[1]}")
        # print("RECV: ", payload_str)
        # Update DB
        if curr_val:
            if curr_val.decode() != payload[2]:
                print("Updating DCLock Status")
                async with self.db.acquire() as conn:
                    await conn.fetch(
                        "UPDATE device SET lock_status = $1 WHERE dclock_terminal_no = $2 AND dclock_box_no = $3",
                        "open" if payload[2][0] == "1" else "locked",
                        payload[0],
                        payload[1],
                    )
                    await add_to_logger_dclock(
                        payload[0],
                        payload[1],
                        LogType.unlock if payload[2][0] == "1" else LogType.lock,
                    )
        else:
            print("Updating DClock (First Time)")
            async with self.db.acquire() as conn:
                await conn.fetch(
                    "UPDATE device SET lock_status = $1 WHERE dclock_terminal_no = $2 AND dclock_box_no = $3 RETURNING *",
                    "open" if payload[2][0] == "1" else "locked",
                    payload[0],
                    payload[1],
                )

        await self.redis.set(f"{payload[0]}:{payload[1]}", payload[2], 10)
        await self.redis.close()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, sql_pool=Depends(create_pool)):
    await connection_manager.connect(websocket)
    await websocket.send_text(
        json.dumps({"Cmd": "App.Locks.Get", "MT": "Req", "TID": 1336, "Data": {}})
    )

    try:
        while True:
            data = await websocket.receive_text()

            json_dat = json.loads(data)

            match json_dat:
                case {"Cmd": "App.Locks.Get", "MT": "Rsp", "TID": 1336}:
                    await refresh_gantner_lock_states(sql_pool, json_dat["Data"])

                case {"Cmd": "Heartbeat", "Data": {}, "MT": "Req"}:
                    try:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "Cmd": "Heartbeat",
                                    "MT": "Req",
                                    "TID": json_dat["TID"],
                                }
                            )
                        )
                    except Exception:
                        print(
                            "[!] Failed to send heartbeat response due to connection error"
                        )

                case {"Cmd": "App.LockStateChanged", "MT": "Evt"}:
                    await refresh_gantner_lock(sql_pool, json_dat["Data"]["Lock"])

                case _:
                    print("[!] Unknown message received")
                    print("[!] Message: ", json_dat)

            print(f"Data received: {data}")

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    finally:
        connection_manager.disconnect(websocket)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    detail = "A database error occurred."
    logging.error(msg=detail, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    detail = "An internal server error occurred."
    logging.error(msg=detail, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


@app.exception_handler(NoResultFound)
async def no_result_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "The requested resource was not found, or the request was invalid."
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_error_exception_handler(request, exc):
    error_message = format_error(exc)

    return JSONResponse(
        status_code=409,
        content={"detail": f"{error_message}"},
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Failed to process request: {str(exc)}"},
    )


@app.exception_handler(TwilioRestException)
async def twilio_rest_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status,
        content={"detail": f"Failed to send SMS: {exc.msg.split(':')[1]}"},
    )


@app.exception_handler(stripe.error.InvalidRequestError)
async def stripe_invalid_request_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.http_status if exc.http_status else 400,
        content={"detail": f"{exc.user_message}"},
    )


@app.exception_handler(ClientError)
async def client_error_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.response["ResponseMetadata"]["HTTPStatusCode"],
        content={"detail": f"{exc.response['Error']['Message']}"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    try:
        errs = exc.errors()

        messages = []

        for err in errs:
            messages.append(f"{err['loc'][2]}: {err['msg']}")

        return JSONResponse(
            status_code=422,
            content={"detail": f"Failed to validate request: {messages}"},
        )
    except Exception:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Failed to validate request: {str(exc)}"},
        )


# Run the app
if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host=get_settings().host,
        port=get_settings().port,
    )

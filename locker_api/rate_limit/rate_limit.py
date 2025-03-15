from datetime import datetime

import pytz
from fastapi import FastAPI, HTTPException, Request
from fastapi_async_sqlalchemy import db
from sqlalchemy import insert, select, update
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from .model import RateLimit


class RateLimitMiddleware:
    def __init__(self, app: FastAPI, limit: int, interval: int) -> None:
        self.app = app
        self.limit = limit
        self.interval = interval

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        try:
            async with db():
                if scope["type"] == "http":
                    request = Request(scope, receive)
                    ip: str = request.client.host
                    await db.session.begin()
                    query = (
                        select(RateLimit).where(RateLimit.ip == ip).with_for_update()
                    )
                    result = await db.session.execute(query)
                    current_rate = result.scalars().first()

                    if current_rate:
                        elapsed_time = datetime.now(pytz.utc) - current_rate.timestamp
                        if elapsed_time.total_seconds() < self.interval:
                            if current_rate.requests >= self.limit:
                                current_rate.exceed_count += 1
                                backoff_time = 2**current_rate.exceed_count
                                query = (
                                    update(RateLimit)
                                    .where(RateLimit.ip == ip)
                                    .values(exceed_count=current_rate.exceed_count)
                                )
                                await db.session.execute(query)
                                await db.session.commit()  # Commit immediately
                                raise HTTPException(
                                    status_code=429,
                                    detail=f"Rate limit exceeded. Retry after {backoff_time} seconds.",
                                )
                            else:
                                query = (
                                    update(RateLimit)
                                    .where(RateLimit.ip == ip)
                                    .values(requests=current_rate.requests + 1)
                                )
                                await db.session.execute(query)
                                await db.session.commit()  # Commit immediately
                        else:
                            query = (
                                update(RateLimit)
                                .where(RateLimit.ip == ip)
                                .values(
                                    requests=1,
                                    timestamp=datetime.now(pytz.utc),
                                    exceed_count=0,
                                    # <-- Resetting exceed_count
                                )
                            )
                            await db.session.execute(query)
                            await (
                                db.session.commit()
                            )  # Reset rate counter and timestamp
                    else:
                        new_rate = RateLimit(
                            ip=ip, requests=1, timestamp=datetime.now(pytz.utc)
                        )
                        query = insert(RateLimit).values(**new_rate.dict())
                        await db.session.execute(query)
                        await db.session.commit()  # Commit the new record

        except HTTPException as e:
            response = JSONResponse({"detail": e.detail}, status_code=e.status_code)
            await response(scope, receive, send)
            return
        except Exception as e:
            response = JSONResponse(
                {"detail": f"Internal Server Error, {e}"}, status_code=500
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

import io
from uuid import UUID

import qrcode
from config import get_settings
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import select


from ..event.model import Event, EventStatus

router = APIRouter(tags=["verify"])


@router.get("/qr")
async def get_qr(code: conint(gt=999, lt=1000000)):
    # Logging at the start
    # Logging input objects

    # Generation of the QR code
    img = qrcode.make(code)
    img_io = io.BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)

    # Logging at the end
    return StreamingResponse(img_io, media_type="image/png")


@router.get("/page")
async def get_page(id_event: UUID):
    query = select(Event).where(Event.id == id_event)

    response = await db.session.execute(query)
    event: Event.Read = response.unique().scalar_one()

    if (
        event.event_status != EventStatus.awaiting_user_pickup
        and event.event_status != EventStatus.awaiting_service_dropoff
    ):
        raise HTTPException(
            status_code=400,
            detail="Event is not awaiting user pickup or service dropoff",
        )

    # build web app URL
    settings = get_settings()
    base_map = {
        "local": "web-dev",
        "dev": "web-dev",
        "qa": "web-qa",
        "staging": "web-staging",
        "production": "web",
    }

    pickup_url = (
        f"http://{base_map[settings.environment]}.koloni.io/pickup/?id={event.id}"
    )

    return RedirectResponse(url=pickup_url)

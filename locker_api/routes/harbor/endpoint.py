import random

from config import get_settings
from fastapi import APIRouter, HTTPException
from fastapi_async_sqlalchemy import db
from pydantic import constr
from sqlalchemy import insert, select, update
from twilio.rest import Client as TwilioClient


from .controller import (
    generate_access_tokens,
    generate_locker_token,
    get_available_lockers,
)
from .model import HarborEvents

router = APIRouter(tags=["harbor"])


@router.get("/harbor/{tower_id}/lockers")
async def get_harbor_devices(
    tower_id: str,
    harbor_api_access_token: str,
):
    """Get all available lockers in a Harbor tower"""

    # Logging at the start

    result = await get_available_lockers(
        tower_id=tower_id,
        svc_token=harbor_api_access_token,
    )
    # Logging result
    # Logging at the end

    return result


@router.post("/harbor/login")
async def harbor_login():
    """Log into Harbor OpenID and retrieve Tower Access and Service Provider tokens"""

    # Logging at the start

    result = await generate_access_tokens()

    # Logging result
    # Logging at the end

    return result


@router.post("/harbor/dropoff")
async def harbor_dropoff(
    tower_id: str,
    locker_id: str,
    harbor_api_access_token: str,
):
    """Generate a Harbor dropoff session token"""

    # Logging at the start
    # Logging input objects

    locker_token = await generate_locker_token(
        svc_token=harbor_api_access_token,
        tower_id=tower_id,
        locker_id=locker_id,
        step="dropoff",
    )

    # Create event
    new_event = HarborEvents(
        tower_id=tower_id,
        locker_id=locker_id,
        pin_code=random.randint(1000, 9999),
        status="awaiting_user_pickup",
    )

    query = insert(HarborEvents).values(new_event.dict()).returning(HarborEvents)
    response = await db.session.execute(query)
    event_dict = response.all().pop()

    await db.session.commit()

    result = {**event_dict, **locker_token}
    # Logging result
    # Logging at the end

    return result


@router.post("/harbor/event/confirm")
async def harbor_event_confirm(
    tower_id: str,
    locker_id: str,
    phone_number: str,
):
    """Confirm a Harbor event and send notification to the user"""

    # Logging at the start
    # Logging input objects

    query = select(HarborEvents).where(
        HarborEvents.tower_id == tower_id,
        HarborEvents.locker_id == locker_id,
    )

    data = await db.session.execute(query)
    events = data.scalars().all()

    if not events:
        # Logging warning
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    harbor_event = events.pop()

    client = TwilioClient(get_settings().twilio_sid, get_settings().twilio_secret)

    client.messages.create(
        to=phone_number,
        from_=get_settings().twilio_messaging_service_sid,
        body=f"You have a delivery ready to pick up at locker {harbor_event.locker_id}. "
        f"Use the following pin code to unlock your locker: {harbor_event.pin_code}",
    )

    # Logging notification info
    # Logging at the end

    return harbor_event


@router.get("/harbor/access/verify")
async def harbor_access_verify(
    pin_code: str,
):
    """Verify access using a pin code and retrieve the associated event"""

    # Logging at the start
    # Logging input

    query = select(HarborEvents).where(
        HarborEvents.pin_code == pin_code,
    )

    data = await db.session.execute(query)
    events = data.scalars().all()

    if not events:
        # Logging warning
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    event = events.pop()
    # Logging the found event
    # Logging at the end

    return event


@router.post("/harbor/pickup")
async def harbor_pickup(
    tower_id: str,
    locker_id: str,
    pin_code: constr(regex=r"\d{4}"),
    harbor_api_access_token: str,
):
    """Generate a Harbor pickup session token"""

    # Logging at the start
    # Logging input objects

    query = (
        update(HarborEvents)
        .where(
            HarborEvents.tower_id == tower_id,
            HarborEvents.locker_id == locker_id,
            HarborEvents.pin_code == pin_code,
        )
        .values(status="finished")
        .returning(HarborEvents)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError if applicable

    event_dict = response.all()
    if not event_dict:
        # Logging warning
        raise HTTPException(status_code=404, detail="Event not found")

    locker_token = await generate_locker_token(
        svc_token=harbor_api_access_token,
        tower_id=tower_id,
        locker_id=locker_id,
        step="pickup",
    )

    result = {**event_dict.pop(), **locker_token}
    # Logging result
    # Logging at the end

    return result

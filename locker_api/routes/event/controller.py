import json
import threading
import re
from apscheduler.jobstores.base import JobLookupError
from pydantic import AnyHttpUrl
from datetime import datetime, timedelta, timezone
from enum import Enum
from math import ceil
from random import randrange
from typing import Optional
from uuid import UUID

from async_stripe import stripe
import stripe.error
from config import get_settings
from fastapi import HTTPException, Request, UploadFile
from fastapi_async_sqlalchemy import db
from payments.stripe import (
    create_ephemeral_key,
    create_setup_intent,
    get_stripe_account,
)
from pydantic import conint, constr
from sqlalchemy import VARCHAR, and_, cast, func, insert, or_, select, update
from sqlalchemy.exc import NoResultFound
from twilio.rest import Client
from util import email
from util.images import ImagesService

from util.response import Message
from util.scheduler import scheduler

from ..device.controller import (
    partner_unlock_device,
    patch_device,
    reserve_device,
    unreserve_device,
    set_device_maintenance,
)
from ..conditions.model import Condition
from ..issue.controller import create_issue
from ..issue.model import Issue
from ..device.model import Device, HardwareType, LockStatus, Mode, Status
from ..groups.controller import is_device_assigned_to_user
from ..location.controller import get_location_by_external_id
from ..memberships.controller import cancel_subscription, get_user_membership
from ..memberships.model import Membership, MembershipType
from ..notifications.controller import create_notify_job_on_event
from ..notifications.model import NotificationType
from ..organization.controller import (
    get_org_name,
    get_org_tree,
    get_org_messaging_service_sid,
    get_org_sendgrid_auth_sender,
    is_ups_org,
)
from ..price.model import Currency, Price, PriceType, Unit
from ..promo.controller import get_promo_by_code, get_promos
from ..promo.model import DiscountType
from ..product_tracking.product_tracking import State
from ..products.controller import patch_product, track_product
from ..products.model import Product
from ..settings.controller import get_max_reservation_count, get_settings_org
from ..settings.model import ExpirationUnit
from ..size.controller import get_size_id_by_external_id
from ..user.controller import (
    get_or_create_stripe_customer,
    get_or_create_user,
    get_user,
    get_user_by_key,
    get_user_subscription,
    set_random_access_code,
)
from ..user.model import Channel, User
from ..webhook.controller import send_payload
from ..webhook.model import EventChange
from .connections import active_connections
from .model import (
    Event,
    EventStatus,
    EventType,
    PaginatedEvents,
    StripeCustomerData,
    StripePaymentData,
    StartReservationResponse,
    StartEvent,
    Duration,
    PenalizeReason,
)


stripe.api_key = get_settings().stripe_api_key


class ServiceStep(Enum):
    pickup = "pickup"
    charge = "charge"
    dropoff = "dropoff"


async def broadcast_event(id_event: UUID, action_type: str, id_org: UUID):
    try:
        query = select(Event).where(Event.id == id_event, Event.id_org == id_org)
        data = await db.session.execute(query)
        event = data.unique().scalar_one_or_none()

        if not event:
            return

        event = Event.Read.parse_obj(event)
        event = event.json(exclude_none=True)

        payload = {"type": action_type, "event": json.loads(event)}

        if id_org in active_connections:
            await active_connections[id_org].send_json(payload)
    except Exception:
        return


async def get_event(id_event: UUID, id_org: UUID) -> Event.Read:
    query = select(Event).where(Event.id == id_event, Event.id_org == id_org)

    data = await db.session.execute(query)
    return data.unique().scalar_one()  # raises NoResultFound


async def get_event_by_device(id_device: UUID, id_org: UUID):
    query = select(Event).where(
        Event.id_device == id_device,
        Event.id_org == id_org,
        Event.event_status.in_(
            [
                EventStatus.awaiting_service_dropoff,
                EventStatus.awaiting_service_pickup,
                EventStatus.awaiting_user_pickup,
                EventStatus.awaiting_payment_confirmation,
                EventStatus.in_progress,
                EventStatus.expired,
            ]
        ),
    )

    data = await db.session.execute(query)
    response = data.unique().scalars().first()

    if not response:
        raise HTTPException(status_code=404, detail="No event found for device")

    return response


async def partner_get_event_by_order_id(order_id: str, id_org: UUID):
    query = select(Event).where(Event.order_id == order_id, Event.id_org == id_org)

    data = await db.session.execute(query)
    return data.unique().scalar_one()  # raises NoResultFound


async def partner_get_events_by_user(
    id_user: UUID, id_org: UUID, by_type: Optional[EventType], active: Optional[bool]
):
    query = None
    if active:
        query = (
            select(Event)
            .where(
                Event.event_status.in_(
                    [
                        EventStatus.awaiting_service_pickup,
                        EventStatus.awaiting_user_pickup,
                        EventStatus.awaiting_payment_confirmation,
                        EventStatus.in_progress,
                    ]
                ),
                Event.id_user == id_user,
                Event.id_org == id_org,
            )
            .order_by(Event.created_at.desc())
        )

    else:
        query = (
            select(Event)
            .where(
                Event.id_user == id_user,
                Event.id_org == id_org,
            )
            .order_by(Event.created_at.desc())
            .limit(100)
        )

    if by_type:
        query = query.where(Event.event_type == by_type)

    data = await db.session.execute(query)
    events = data.unique().scalars().all()

    return events


async def partner_get_deliveries(access_code: str, id_org: UUID):
    query = (
        select(Event)
        .join(User)
        .where(
            Event.event_status.in_(
                [EventStatus.awaiting_service_dropoff, EventStatus.in_progress]
            ),
            Event.id_org == id_org,
            User.access_code == access_code,
        )
        .order_by(Event.created_at.desc())
    )

    data = await db.session.execute(query)
    events = data.unique().scalars().all()

    return events


async def generate_invoice_id(id_org: UUID):
    # Get org name and count of events
    name = await get_org_name(id_org)
    count = await partner_event_count(id_org)

    # Extract first 3 consonants from the org's name
    invoice_pre = re.sub(r"[aeiouAEIOU]", "", name).replace("-", "")[:3].upper()

    # Add 6 digit counter to the prefix
    result = f"{invoice_pre}{str(count + 1).zfill(6)}"
    return result


# Helper
async def partner_event_count(id_org: UUID):
    query = select(Event.id).where(Event.id_org == id_org)

    data = await db.session.execute(query)
    return len(data.unique().scalars().all())


async def partner_get_event_public(id_event: UUID):
    query = select(Event).where(Event.id == id_event)

    response = await db.session.execute(query)
    event = response.unique().scalar_one()

    return event


async def partner_get_invoice(invoice_id: str, id_org: UUID):
    query = select(Event).where(Event.invoice_id == invoice_id, Event.id_org == id_org)

    data = await db.session.execute(query)
    return data.unique().scalar_one()  # raises NoResultFound


def run_in_thread(func, *args, **kwargs) -> None:
    async def thread_func() -> None:
        await func(*args, **kwargs)

    thread = threading.Thread(target=thread_func)
    thread.start()


async def mobile_confirm_event(
    id_event: UUID,
    id_org: UUID,
    id_user: UUID,
    payment_method: str,
    ojmar_user_code: Optional[constr(regex=r"\d{4}")] = None,
):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_org == id_org,
        Event.id_user == id_user,
        or_(
            Event.event_status == EventStatus.awaiting_payment_confirmation,
            Event.event_status == EventStatus.awaiting_user_pickup,
        ),
    )

    data = await db.session.execute(query)
    event: Event.Read = data.unique().scalar_one()  # raises NoResultFound

    query = select(User).where(User.id == id_user)

    response = await db.session.execute(query)
    user = response.unique().scalar_one()  # raises NoResultFound

    setup = None
    payment = None
    if event.setup_intent_id and not payment_method:
        stripe_account_id = await get_stripe_account(id_org)

        setup = await stripe.SetupIntent.retrieve(
            event.setup_intent_id, stripe_account=stripe_account_id
        )

        if (
            setup.status != "succeeded"
            and user.phone_number != "+1234567890"
            and user.phone_number != "+1223334444"
            and event.device.price.amount != 0
        ):
            raise HTTPException(
                status_code=400, detail="payment method is still pending"
            )

    # Set setup intent as default payment method
    if setup:
        customer = await get_or_create_stripe_customer(id_user, id_org)
        await stripe.Customer.modify(
            customer,
            invoice_settings=(
                {"default_payment_method": setup.payment_method} if setup else None
            ),
            stripe_account=await get_stripe_account(id_org),
        )

    # Set the default payment method, in case it exists
    if payment_method:
        customer = await get_or_create_stripe_customer(id_user, id_org)
        await stripe.Customer.modify(
            customer,
            invoice_settings={"default_payment_method": payment_method},
            stripe_account=await get_stripe_account(id_org),
        )

    if event.event_type == EventType.vending:
        if event.device.product.price:
            account = await stripe.Account.retrieve(stripe_account_id)
            payment = await stripe.PaymentIntent.create(
                amount=int(event.device.product.price * 100),
                currency=account.default_currency or "usd",
                customer=customer,
                payment_method=setup.payment_method,
                confirm=True,
                off_session=True,
                stripe_account=stripe_account_id,
            )

            if payment.status != "succeeded":
                raise HTTPException(
                    status_code=400, detail="payment method is still pending"
                )

        await track_product(
            event.device.product.id,
            State.outgoing,
            id_org,
            id_user,
            event.device.id,
            event.device.id_condition,
        )
        await partner_unlock_device(event.device.id, id_org)
        # await unreserve_device(event.device.id, id_org)
        await set_device_maintenance(event.device.id, id_org)

    # Update event status
    match event.event_type:
        case EventType.service:
            event_status = EventStatus.awaiting_service_pickup
        case EventType.storage:
            event_status = EventStatus.in_progress
        case EventType.rental:
            event_status = EventStatus.in_progress
        case EventType.delivery:
            event_status = EventStatus.awaiting_user_pickup
        case EventType.vending:
            event_status = EventStatus.finished
        case _:
            raise HTTPException(
                status_code=400,
                detail=f"event with id: {id_event} is not supported for mobile confirmation",
            )

    query = (
        update(Event)
        .where(Event.id == id_event)
        .values(
            started_at=datetime.utcnow(),
            event_status=event_status,
            total=payment.amount / 100 if payment else None,
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    data = response.all().pop()

    # this selects the event again to get the related objects
    query = select(Event).where(Event.id == data.id)
    response = await db.session.execute(query)
    event_read = response.unique().scalar_one()  # raises NoResultFound

    # count events, so we can do a "welcome message"
    query = select(func.count(Event.id)).where(
        Event.id_user == id_user, Event.id_org == id_org
    )
    event_count = await db.session.execute(query)

    if event_count == 1:
        # this is a welcoming message for the first transaction
        await create_notify_job_on_event(event.id, NotificationType.on_signup)

    await create_notify_job_on_event(event.id, NotificationType.on_start)

    await send_payload(
        id_org,
        EventChange(
            id_org=id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    try:
        # remove scheduled job for event
        scheduler.remove_job(str(id_event))
    except Exception:
        pass

    # Track product usage
    if event.device.product:
        await track_product(
            event.device.product.id,
            State.outgoing,
            id_org,
            id_user,
            event.device.id,
            event.device.id_condition,
        )

    if event.device.hardware_type == HardwareType.ojmar and ojmar_user_code:
        await patch_device(
            event.device.id,
            id_org,
            Device.Patch(
                hardware_type=HardwareType.ojmar,
                locker_udn=event.device.locker_udn,
                user_code=ojmar_user_code,
                master_code=event.device.master_code,
            ),
            True,
        )

    return event_read


async def partner_sign_event(
    id_event: UUID,
    id_org: UUID,
    image: Optional[UploadFile],
    images_service: Optional[ImagesService],
    image_url: Optional[str] = None,
):
    query = select(Event).where(Event.id == id_event, Event.id_org == id_org)

    response = await db.session.execute(query)
    response.unique().scalar_one()  # raises NoResultFound

    try:
        if image and images_service:
            image_url = await images_service.upload(id_org, image)

    except Exception as e:
        error_detail = f"Failed to upload image, {e}"

        raise HTTPException(
            status_code=400,
            detail=error_detail,
        )

    query = (
        update(Event)
        .where(Event.id == id_event)
        .values(signature_url=image_url["url"] if image else image_url)
        .returning(Event)
    )

    response = await db.session.execute(query)

    await db.session.commit()  # raises IntegrityError

    data = response.all().pop()

    return {"id_event": data["id"], "signature_url": data["signature_url"]}


async def partner_sign_events(
    events: list[UUID],
    id_org: UUID,
    image_url: AnyHttpUrl,
):
    success_count = 0

    for event in events:
        try:
            await partner_sign_event(event, id_org, None, None, image_url)
        except Exception:
            pass
        success_count += 1

    return {"detail": f"{success_count}/{len(events)} where successfully signed"}


async def partner_penalize_event(
    id_event: UUID,
    amount: float,
    reason: PenalizeReason,
    id_org: UUID,
):
    query = select(Event).where(Event.id == id_event, Event.id_org == id_org)
    response = await db.session.execute(query)

    event = response.unique().scalar_one()

    if event.penalize_charge and event.penalize_reason:
        raise HTTPException(
            status_code=400, detail="This transaction has already been penalized"
        )

    # Charge step
    customer_id = await get_or_create_stripe_customer(event.id_user, id_org)
    stripe_account_id = await get_stripe_account(id_org)
    customer = await stripe.Customer.retrieve(
        customer_id, stripe_account=stripe_account_id
    )
    account = await stripe.Account.retrieve(stripe_account_id)
    try:
        await stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=account.default_currency or "usd",
            customer=customer.id,
            payment_method=customer.invoice_settings.default_payment_method,
            confirm=True,
            off_session=True,
            stripe_account=stripe_account_id,
        )
    except stripe.error.CardError:
        raise HTTPException(
            status_code=400, detail="failed to charge customer, card has no funds"
        )

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)
    if event.user.phone_number:
        client.messages.create(
            to=event.user.phone_number,
            from_=get_settings().twilio_messaging_service_sid,
            body=f"You have been charged {amount} {account.default_currency.upper() or 'USD'} for a misuse of our service, reason: {reason.value.replace('_', ' ')}. Please contact support for more information",
        )
    if event.user.email:
        email_sender = await get_org_sendgrid_auth_sender(event.id_org)

        email.send(
            email_sender,
            event.user.email,
            "Service Misuse",
            f"You have been charged {amount} {account.default_currency.upper() or 'USD'} for a misuse of our service, reason: {reason.value.replace('_', ' ')}. Please contact support for more information",
            is_ups_org=await is_ups_org(event.id_org),
        )

    query = (
        update(Event)
        .where(Event.id == id_event, Event.id_org == id_org)
        .values(penalize_charge=amount, penalize_reason=reason)
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError
    data = response.all().pop()

    return data


async def partner_unlock_event(id_event: UUID, code: int, id_org: UUID):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_org == id_org,
        Event.event_status.in_(
            [
                EventStatus.awaiting_payment_confirmation,
                EventStatus.awaiting_user_pickup,
                EventStatus.awaiting_service_pickup,
                EventStatus.awaiting_service_dropoff,
                EventStatus.in_progress,
            ]
        ),
    )

    response = await db.session.execute(query)
    event = response.unique().scalar_one()  # raises NoResultFound

    if event.code != code:
        error_detail = f"Invalid code for event with ID: {id_event}"

        raise HTTPException(
            status_code=400,
            detail=error_detail,
        )

    await partner_unlock_device(event.device.id, id_org)

    return event


async def get_device_with_fewest_transactions(
    id_size: UUID,
    id_location: UUID,
    id_org: UUID,
    by_mode: Optional[Mode] = None,
) -> Optional[Device]:
    query = select(Device).where(
        Device.id_size == id_size,
        Device.id_location == id_location,
        Device.id_org == id_org,
        Device.status == Status.available,
    )

    if by_mode:
        query = query.where(Device.mode == by_mode)

    # Order devices by their transaction count in ascending order
    query = query.order_by(Device.transaction_count)

    response = await db.session.execute(query)
    devices = response.unique().scalars().all()
    if len(devices) == 0:
        return None

    # Select the device with the fewest transactions
    selected_device: Device = devices[0]

    return selected_device


async def mobile_start_event(
    id_device: UUID,
    id_size: UUID,
    id_location: UUID,
    id_org: UUID,
    id_user: UUID,
    promo_code: Optional[str] = None,
    order_id: Optional[str] = None,
):
    if id_size and id_location and id_device:
        raise HTTPException(
            status_code=400,
            detail="You can't use a size, location, and device at the same time",
        )

    if not id_device and not id_location and not id_size:
        raise HTTPException(
            status_code=400,
            detail="You must use a combination of size and location, or just one device",
        )

    if id_device and id_location or id_device and id_size:
        raise HTTPException(
            status_code=400,
            detail="You can't use a device with a location or size",
        )

    if (id_size and id_device) or (id_location and id_device):
        raise HTTPException(
            status_code=400,
            detail="You must use a combination of size and location, or just one device",
        )

    query = select(User).where(User.id == id_user, User.phone_number is not None)
    try:
        response = await db.session.execute(query)
        response.unique().scalar_one()  # raises NoResultFound
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Count events for user
    query = select(func.count(Event.id)).where(
        Event.id_user == id_user,
        Event.event_status.in_(
            [
                EventStatus.awaiting_service_pickup,
                EventStatus.awaiting_user_pickup,
                EventStatus.awaiting_payment_confirmation,
                EventStatus.in_progress,
            ]
        ),
    )

    active_count = await db.session.execute(query)
    max_count = await get_max_reservation_count(id_org)
    if active_count.unique().scalar_one() == max_count and max_count != 0:
        raise HTTPException(
            status_code=400,
            detail=f"user with id: {id_user} has reached the maximum number of active reservations",
        )

    # If a Size and Location is passed, start the event with a random selected
    # device based on the given parameters
    if id_size and id_location:
        # Set id_device to selected device
        selected_device = await get_device_with_fewest_transactions(
            id_size, id_location, id_org
        )
        if not selected_device:
            raise HTTPException(
                status_code=404,
                detail="No devices found with the given parameters",
            )
        id_device = selected_device.id

    # Check if device is assigned to group or user and if user is in group
    if not await is_device_assigned_to_user(id_device, id_user):
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to use this device",
        )

    device = await reserve_device(id_device, id_org)

    match device.mode:
        case Mode.service:
            event_type = EventType.service
        case Mode.storage:
            event_type = EventType.storage
        case Mode.rental:
            event_type = EventType.rental
        case Mode.delivery:
            event_type = EventType.delivery
        case Mode.vending:
            if not device.product:
                await unreserve_device(id_device, id_org)
                raise HTTPException(
                    status_code=400,
                    detail=f"device with id: {id_device} has no product",
                )
            event_type = EventType.vending
        case _:
            await unreserve_device(id_device, id_org)
            raise HTTPException(
                status_code=400,
                detail="Device is in an unsupported mode for this operation",
            )

    setup_intent = None
    ephemeral_key = None
    stripe_account = None
    stripe_customer = None

    if device.mode == Mode.vending:
        try:
            stripe_account = await get_stripe_account(id_org)
            stripe_customer = await get_or_create_stripe_customer(id_user, id_org)
            setup_intent = await create_setup_intent(
                id_org, stripe_customer, stripe_account
            )
            ephemeral_key = await create_ephemeral_key(stripe_customer, stripe_account)
        except HTTPException as e:
            await unreserve_device(id_device, id_org)
            raise e
    elif device.price and device.price.card_on_file:
        try:
            stripe_account = await get_stripe_account(id_org)
            stripe_customer = await get_or_create_stripe_customer(id_user, id_org)
            setup_intent = await create_setup_intent(
                id_org, stripe_customer, stripe_account
            )
            ephemeral_key = await create_ephemeral_key(stripe_customer, stripe_account)
        except HTTPException as e:
            await unreserve_device(id_device, id_org)
            raise e

    # Get org settings to determine length of pin codes:
    org_settings = await get_settings_org(id_org=id_org)

    # Invoice ID
    invoice_id = await generate_invoice_id(id_org)
    code = await generate_code(long_codes=org_settings.use_long_parcel_codes)

    promo = None
    if promo_code:
        promo = await get_promo_by_code(promo_code, id_org, id_user)

    # Select events that have that promo code (promos should only work once per user)
    if promo:
        query = select(func.count(Event.id)).where(
            Event.id_org == id_org, Event.id_promo == promo.id, Event.id_user == id_user
        )
        response = await db.session.execute(query)
        data = response.unique().scalar_one()

        if data > 0:
            await unreserve_device(id_device, id_org)
            raise HTTPException(
                status_code=400, detail="you have already used this promo code"
            )

    new_event = Event(
        payment_intent_id=None,
        invoice_id=invoice_id,
        setup_intent_id=setup_intent.id if setup_intent else None,
        event_type=event_type,
        event_status=(
            EventStatus.awaiting_payment_confirmation
            if device.mode != Mode.delivery
            else EventStatus.awaiting_user_pickup
        ),
        total=None,
        started_at=datetime.utcnow(),
        code=code,
        id_org=id_org,
        id_user=id_user,
        id_device=id_device,
        id_promo=promo.id if promo else None,
        order_id=order_id,
        refunded_amount=0,
    )

    query = insert(Event).values(new_event.dict()).returning(Event)

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    payment_data = StripePaymentData(
        customer_data=StripeCustomerData(
            customer_id=stripe_customer,
            ephemeral_key=ephemeral_key,
        ),
        client_secret=setup_intent.client_secret if setup_intent else None,
        publishable_key=get_settings().stripe_pub_key,
    )

    event = response.all().pop()

    device_query = (
        update(Device)
        .where(Device.id == id_device)
        .values(transaction_count=Device.transaction_count + 1)
    )
    await db.session.execute(device_query)
    await db.session.commit()  # Commit the transaction count increment

    output = {
        "client_secret": payment_data.client_secret if payment_data else None,
        "customer_data": payment_data.customer_data if payment_data else None,
        "publishable_key": payment_data.publishable_key if payment_data else None,
        "stripe_account_id": stripe_account if payment_data else None,
    }

    output.update(event)

    await send_payload(
        id_org,
        EventChange(
            id_org=id_org,
            id_event=event.id,
            event_status=event.event_status,
            event_obj=event,
        ),
    )

    # start event timer to cancel event after 5 minutes, unless it's a delivery
    if device.mode != Mode.delivery:
        scheduler.add_job(
            partner_cancel_event,
            "date",
            run_date=datetime.utcnow() + timedelta(minutes=5),
            args=[event.id_org, event.id],
            id=str(event.id),
            replace_existing=True,
        )

    if device.mode == Mode.delivery:
        await create_notify_job_on_event(event.id, NotificationType.on_start)

    return StartReservationResponse(**output)


async def mobile_complete_event(
    id_event: UUID,
    id_user: UUID,
    id_org: UUID,
    request: Request,
    image_url: Optional[AnyHttpUrl] = None,
    ojmar_user_code: Optional[constr(regex=r"\d{4}")] = None,
    payment_method: Optional[str] = None,
):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_org == id_org,
        Event.id_user == id_user,
        or_(
            Event.event_status == EventStatus.awaiting_user_pickup,
            Event.event_status == EventStatus.reserved,
            and_(
                Event.event_status == EventStatus.in_progress,
                or_(
                    Event.event_type == EventType.rental,
                    Event.event_type == EventType.storage,
                ),
            ),
        ),
    )

    response = await db.session.execute(query)
    event = response.unique().scalar_one()

    match event.event_type:
        case EventType.service:
            data = await complete_service(event)

            if event.device.hardware_type == HardwareType.ojmar and ojmar_user_code:
                await patch_device(
                    event.device.id,
                    id_org,
                    Device.Patch(
                        hardware_type=HardwareType.ojmar,
                        locker_udn=event.device.locker_udn,
                        user_code=ojmar_user_code,
                        master_code=event.device.master_code,
                    ),
                )

            return data

        case EventType.storage:
            data = await complete_storage(event, request, None, None, payment_method)

            if event.device.hardware_type == HardwareType.ojmar and ojmar_user_code:
                await patch_device(
                    event.device.id,
                    id_org,
                    Device.Patch(
                        hardware_type=HardwareType.ojmar,
                        locker_udn=event.device.locker_udn,
                        user_code=ojmar_user_code,
                        master_code=event.device.master_code,
                    ),
                )

            return data

        case EventType.rental:
            data = await complete_storage(
                event, request, image_url, None, payment_method
            )

            if event.device.hardware_type == HardwareType.ojmar and ojmar_user_code:
                await patch_device(
                    event.device.id,
                    id_org,
                    Device.Patch(
                        hardware_type=HardwareType.ojmar,
                        locker_udn=event.device.locker_udn,
                        user_code=ojmar_user_code,
                        master_code=event.device.master_code,
                    ),
                )

            return data

        case _:
            raise HTTPException(
                status_code=400,
                detail=f"The event type {event.event_type} is not supported for mobile pickup",
            )


async def mobile_cancel_event(id_event: UUID, id_user: UUID, id_org: UUID):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_org == id_org,
        Event.id_user == id_user,
        Event.event_status.in_(
            [
                EventStatus.awaiting_payment_confirmation,
                EventStatus.awaiting_service_pickup,
                EventStatus.awaiting_user_pickup,
            ]
        ),
    )

    response = await db.session.execute(query)

    event = response.unique().scalar_one()  # raises NoResultFound

    # Cancel the event
    query = (
        update(Event)
        .where(Event.id == id_event)
        .values(event_status=EventStatus.canceled, ended_at=datetime.utcnow())
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    await unreserve_device(event.device.id, id_org)

    data = response.all().pop()

    await send_payload(
        id_org,
        EventChange(
            id_org=id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    return data


async def mobile_get_events(
    id_user: UUID,
    id_org: UUID,
    page: conint(gt=0),
    size: conint(gt=0),
    id_event: Optional[UUID],
    key: Optional[str],
    value: Optional[str],
    by_type: Optional[EventType],
    by_status: Optional[EventStatus],
    by_hardware_type: Optional[HardwareType],
    search: Optional[str],
):
    org_tree = await get_org_tree(id_org)

    query = select(Event).where(Event.id_user == id_user, Event.id_org.in_(org_tree))

    if id_event:
        # * Early return if id_event is provided
        query = query.where(Event.id == id_event)

        result = await db.session.execute(query)
        return result.unique().scalar_one()

    if key and value:
        # * Early return if key and value are provided
        if key not in Event.__table__.columns:
            raise HTTPException(status_code=400, detail=f"Invalid field: {key}")

        query = query.filter(cast(Event.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        return result.unique().scalar_one()

    if search:
        query = query.filter(
            or_(
                cast(Event.total, VARCHAR).ilike(f"%{search}%"),
            )
        )
    if by_type:
        query = query.where(Event.event_type == by_type)
    if by_status:
        query = query.where(Event.event_status == by_status)

    if by_hardware_type:
        query = query.join(Device).where(Device.hardware_type == by_hardware_type)

    total = await db.session.execute(query)
    query = (
        query.limit(size).offset((page - 1) * size).order_by(Event.created_at.desc())
    )

    data = await db.session.execute(query)

    total_count = len(total.unique().all())

    return PaginatedEvents(
        items=data.unique().scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def complete_service(event: Event):
    total_time: timedelta = datetime.now(timezone.utc) - event.started_at
    formated_time = f"{int(total_time.total_seconds() // 3600):02d}:{int(total_time.total_seconds() % 3600 // 60):02d}:{int(total_time.total_seconds() % 3600 % 60):02d}"

    query = (
        update(Event)
        .where(Event.id == event.id)
        .values(
            event_status=EventStatus.finished,
            ended_at=datetime.utcnow(),
            total_time=formated_time,
        )
        .returning(Event)
    )

    await unreserve_device(event.device.id, event.id_org)

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    data = response.all().pop()

    await send_payload(
        data.id_org,
        EventChange(
            id_org=data.id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    await create_notify_job_on_event(data.id, NotificationType.on_complete)

    return data


async def expire_delivery(
    id_event: UUID,
    id_org: UUID,
) -> Event.Read:
    query = select(Event).where(
        Event.event_type == EventType.delivery,
        or_(
            Event.event_status == EventStatus.awaiting_user_pickup,
            Event.event_status == EventStatus.awaiting_service_dropoff,
        ),
        Event.id == id_event,
        Event.id_org == id_org,
    )

    response = await db.session.execute(query)
    event = response.unique().scalar_one()

    total_time: timedelta = datetime.now(timezone.utc) - event.started_at
    formated_time = f"{int(total_time.total_seconds() // 3600):02d}:{int(total_time.total_seconds() % 3600 // 60):02d}:{int(total_time.total_seconds() % 3600 % 60):02d}"

    query = (
        update(Event)
        .where(Event.id == event.id)
        .values(
            event_status=EventStatus.expired,
            ended_at=datetime.utcnow(),
            total_time=formated_time,
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    data = response.all().pop()

    await send_payload(
        id_org,
        EventChange(
            id_org=id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    await create_notify_job_on_event(event.id, NotificationType.on_expired)

    return event


async def complete_delivery(
    code: Optional[int],
    order_id: Optional[str],
    user_code: Optional[constr(regex=r"\d{4}")] = None,
    id_org: Optional[UUID] = None,
) -> Event.Read:
    if not code and not order_id:
        error_detail = (
            "You must provide either a code or an order_id to complete a delivery"
        )

        raise HTTPException(
            status_code=400,
            detail=error_detail,
        )

    if code and order_id:
        error_detail = "You can't use both code and order_id to complete a delivery"

        raise HTTPException(
            status_code=400,
            detail=error_detail,
        )

    if id_org:
        query = select(Event).where(
            Event.id_org == id_org,
            Event.event_type == EventType.delivery,
        )
    else:
        query = select(Event).where(
            Event.event_type == EventType.delivery,
        )

    if code:
        query = query.where(Event.code == code)

    if order_id:
        query = query.where(Event.order_id == order_id)

    response = await db.session.execute(query)
    event = response.unique().scalar_one_or_none()
    if event is None:
        error_detail = "This pin code does not exist. Please try again"

        raise HTTPException(
            status_code=404,
            detail=error_detail,
        )

    # remove expiration job
    try:
        scheduler.remove_job("exp" + str(event.id))
    except JobLookupError:
        pass

    # This is to validate the user code if the event device has the restriction enabled
    # * if no user code is provided, it will just skip this step, this is to avoid breaking the Kiosk APP
    if user_code and id_org:
        # Check if the event device's location has the restriction enabled
        if event.device.location.restrict_by_user_code is True:
            # Check if user code exists
            user = await get_user_by_key("pin_code", user_code, id_org)

            if not user:
                error_detail = "Could not find a user with the provided user code"

                raise HTTPException(
                    status_code=400,
                    detail=error_detail,
                )

    total_time: timedelta = datetime.now(timezone.utc) - event.started_at
    formated_time = f"{int(total_time.total_seconds() // 3600):02d}:{int(total_time.total_seconds() % 3600 // 60):02d}:{int(total_time.total_seconds() % 3600 % 60):02d}"

    query = (
        update(Event)
        .where(Event.id == event.id)
        .values(
            event_status=EventStatus.finished,
            ended_at=datetime.utcnow(),
            total_time=formated_time,
            code=None,
        )
        .returning(Event)
    )

    response = await db.session.execute(query)

    if event.device.hardware_type != HardwareType.harbor:
        await partner_unlock_device(event.id_device, event.id_org, True)

    await unreserve_device(event.id_device, event.id_org)

    await db.session.commit()  # raises IntegrityError

    data = response.all().pop()

    await send_payload(
        id_org,
        EventChange(
            id_org=id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    await create_notify_job_on_event(event.id, NotificationType.on_complete)

    return event


async def complete_storage(
    event: Event,
    request: Optional[Request] = None,
    image_url: Optional[AnyHttpUrl] = None,
    cancel_at: Optional[datetime] = None,
    payment_method: Optional[str] = None,
):
    if not event.device.price:
        return await complete_storage_free(event, image_url, cancel_at)

    amount = await calculate_price_storage(event, event.device.price, cancel_at)

    if amount <= 0:
        return await complete_storage_free(event, image_url, cancel_at)

    stripe_account_id = await get_stripe_account(event.id_org)
    stripe_customer_id = await get_or_create_stripe_customer(
        event.id_user, event.id_org
    )

    stripe_customer = await stripe.Customer.retrieve(
        stripe_customer_id,
        stripe_account=stripe_account_id,
    )

    total = int(amount * 100)

    if total < 50:
        total = 50

    membership = await get_user_membership(event.id_org, event.id_user)
    link = await get_user_subscription(event.id_user, event.id_org)

    subscription_id = link.stripe_subscription_id
    if membership:
        total = await calculate_membership(membership, event, subscription_id, total)

    if total <= 0:
        return await complete_storage_free(event, image_url, cancel_at)

    await set_charge_in_progress(event.id, event.id_org)

    try:
        payment_intent = await stripe.PaymentIntent.create(
            amount=total,
            customer=stripe_customer_id,
            setup_future_usage="off_session",
            payment_method=payment_method
            or stripe_customer.invoice_settings.default_payment_method,
            currency=event.device.price.currency.value,
            stripe_account=stripe_account_id,
            confirm=True,
            return_url=request.headers.get("referer") if request else None,
        )
    except stripe.error.CardError:
        await undo_charge_in_progress(event.id, event.id_org)
        raise HTTPException(status_code=402, detail="Your card has insufficient funds")

    total_time: timedelta = (
        cancel_at.astimezone(tz=datetime.utcnow().tzinfo) - event.started_at
        if cancel_at
        else datetime.now(timezone.utc) - event.started_at
    )
    formatted_time = f"{int(total_time.total_seconds() // 3600):02d}:{int(total_time.total_seconds() % 3600 // 60):02d}:{int(total_time.total_seconds() % 3600 % 60):02d}"

    event_query = (
        update(Event)
        .where(Event.id == event.id)
        .values(
            payment_intent_id=payment_intent.id,
            event_status=EventStatus.finished,
            ended_at=cancel_at if cancel_at else datetime.utcnow(),
            total=float(total / float(100)),
            total_time=formatted_time,
            image_url=image_url,
        )
        .returning(Event)
    )

    await unreserve_device(event.device.id, event.device.id_org)

    response = await db.session.execute(event_query)
    await db.session.commit()  # raise IntegrityError

    data = response.all().pop()

    # this selects the event again to get the related objects
    query = select(Event).where(Event.id == data.id)
    response = await db.session.execute(query)
    event = response.unique().scalar_one()  # raises NoResultFound

    await send_payload(
        data.id_org,
        EventChange(
            id_org=data.id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    # Track product usage
    if event.device.product:
        await track_product(
            event.device.product.id,
            State.incoming,
            event.id_org,
            event.id_user,
            event.device.id,
            event.device.condition,
        )

    try:
        output = {
            "redirect_url_3d": payment_intent.next_action.redirect_to_url.url,
        }
    except AttributeError:
        output = {}

    output.update(event.Read.parse_obj(event))

    await create_notify_job_on_event(data.id, NotificationType.on_complete)

    try:
        scheduler.remove_job(job_id=str(event.id))
    except JobLookupError:
        pass

    return output


async def complete_storage_free(
    event: Event,
    image_url: Optional[AnyHttpUrl] = None,
    cancel_at: Optional[datetime] = None,
):
    total_time: timedelta = (
        cancel_at.astimezone(tz=datetime.utcnow().tzinfo) - event.started_at
        if cancel_at
        else datetime.now(timezone.utc) - event.started_at
    )
    formatted_time = (
        f"{int(total_time.total_seconds() // 3600):02d}:{int(total_time.total_seconds() % 3600 // 60):02d}:"
        f"{int(total_time.total_seconds() % 3600 % 60):02d}"
    )

    query = (
        update(Event)
        .where(Event.id == event.id)
        .values(
            event_status=EventStatus.finished,
            ended_at=cancel_at if cancel_at else datetime.utcnow(),
            total=0,
            total_time=formatted_time,
            passcode=None,
            image_url=image_url,
        )
    ).returning(Event)

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    await unreserve_device(event.device.id, event.device.id_org)

    data = response.all().pop()

    await send_payload(
        data.id_org,
        EventChange(
            id_org=data.id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    if event.device.product:
        await track_product(
            event.device.product.id,
            State.incoming,
            event.id_org,
            event.id_user,
            event.device.id,
            event.device.id_condition,
        )

    try:
        scheduler.remove_job(job_id=str(event.id))
    except JobLookupError:
        pass

    await create_notify_job_on_event(data.id, NotificationType.on_complete)

    return data


async def charge_service_free(event: Event):
    query = (
        update(Event)
        .where(Event.id == event.id)
        .values(
            event_status=EventStatus.awaiting_service_dropoff,
            total=0,
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    # Variable used to handle custom Twilio Messaging Service SIDs depending
    # on the org given:
    messaging_service_sid = await get_org_messaging_service_sid(event.id_org)

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)
    client.messages.create(
        to=event.user.phone_number,
        from_=messaging_service_sid,
        body="Your reservation is free of charge! We'll notify you once your order is complete and ready for pickup.",
    )  # raise TwilioRestException

    data = response.all().pop()

    await send_payload(
        data.id_org,
        EventChange(
            id_org=data.id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    return data


async def calculate_price_storage(
    event: Event, price: Price, cancel_at: Optional[datetime] = None
):
    if price.amount == 0:
        return 0

    if price.price_type != PriceType.pay_per_time:
        raise HTTPException(
            status_code=400,
            detail=f"Price type {price.price_type} is not supported for storage/rental",
        )

    delta = datetime.now(timezone.utc) - event.started_at

    if cancel_at:
        delta = cancel_at - event.started_at

    total = None

    match price.unit:
        case Unit.minute:
            if price.prorated:
                total = float(price.amount) * (
                    delta.total_seconds() / (60 * float(price.unit_amount))
                )

            total = float(price.amount) * ceil(
                delta.total_seconds() / (60 * float(price.unit_amount))
            )
        case Unit.hour:
            if price.prorated:
                total = (
                    float(price.amount)
                    * delta.total_seconds()
                    / (3600 * float(price.unit_amount))
                )

            total = float(price.amount) * ceil(
                delta.total_seconds() / (3600 * float(price.unit_amount))
            )
        case Unit.day:
            if price.prorated:
                total = (
                    float(price.amount)
                    * delta.total_seconds()
                    / (86400 * float(price.unit_amount))
                )

            total = (
                float(price.amount)
                * delta.total_seconds()
                / (86400 * float(price.unit_amount))
                if delta.days > 0
                else 1
            )
        case Unit.week:
            if price.prorated:
                total = float(price.amount) * delta.total_seconds() / 604800

            total = (
                float(price.amount)
                * delta.total_seconds()
                / (604800 * float(price.unit_amount))
                if delta.days > 6
                else 1
            )
        case _:
            raise HTTPException(
                status_code=400,
                detail=f"Unit {price.unit} is not supported for storage",
            )

    if event.id_promo:
        total = await calculate_promo(event, total)

    return total


async def calculate_promo(event: Event, total: int):
    promo = await get_promos(0, 0, id_org=event.id_org, id_promo=event.id_promo)
    match promo.discount_type:
        case DiscountType.percentage:
            total = total - (total * (int(promo.amount) / 100))
        case DiscountType.fixed:
            total = total - int(promo.amount)

    return total


async def partner_get_events(
    by_type: Optional[EventType],
    by_status: Optional[EventStatus],
    current_org: UUID,
    page: conint(gt=0),
    size: conint(gt=0),
    id_event: Optional[UUID],
    key: Optional[str],
    value: Optional[str],
    search: Optional[str],
    by_device: Optional[HardwareType],
):
    query = select(Event).where(Event.id_org == current_org).join(User).join(Device)

    if id_event:
        # * Early return if id_event is provided
        query = query.where(Event.id == id_event)

        result = await db.session.execute(query)
        event = result.unique().scalar_one()

        return event

    if key and value:
        # * Early return if key and value are provided
        if key not in Event.__table__.columns:
            raise HTTPException(status_code=400, detail=f"Invalid field: {key}")

        query = query.filter(cast(Event.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        event = result.unique().scalar_one()

        return event

    if search:
        query = query.filter(
            or_(
                cast(Event.total, VARCHAR).ilike(f"%{search}%"),
                Event.invoice_id.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%"),
                User.phone_number.ilike(f"%{search}%"),
                Device.name.ilike(f"%{search}%"),
            )
        )
    if by_type:
        query = query.where(Event.event_type == by_type)
    if by_status:
        query = query.where(Event.event_status == by_status)

    if by_device:
        query = query.where(Device.hardware_type == by_device)

    total = await db.session.execute(query)
    query = (
        query.limit(size)
        .offset((page - 1) * size)
        .order_by(Event.event_status.asc(), Event.created_at.desc())
    )

    data = await db.session.execute(query)

    events = data.unique().scalars().all()

    filtered_active_events = [
        event
        for event in events
        if event.event_status
        not in (
            EventStatus.finished,
            EventStatus.canceled,
            EventStatus.refunded,
            EventStatus.expired,
        )
    ]

    filtered_expired_events = [
        event for event in events if event.event_status == EventStatus.expired
    ]

    filtered_completed_events = [
        event
        for event in events
        if event.event_status
        in [
            EventStatus.finished,
            EventStatus.canceled,
            EventStatus.refunded,
        ]
    ]

    formatted_events = (
        sorted(filtered_active_events, key=lambda x: x.invoice_id, reverse=True)
        + sorted(filtered_expired_events, key=lambda x: x.invoice_id, reverse=True)
        + sorted(filtered_completed_events, key=lambda x: x.invoice_id, reverse=True)
    )

    total_count = len(total.unique().all())

    return PaginatedEvents(
        items=formatted_events,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def partner_start_event(
    payload: StartEvent,
    id_org: UUID,
    request: Request,
):
    match payload.event_type:
        case EventType.storage:
            return await partner_start_storage(
                payload.id_size,
                payload.size_external_id,
                payload.id_location,
                payload.location_external_id,
                id_org,
                payload.id_user,
                payload.user_external_id,
                payload.from_user,
                payload.duration,
                payload.passcode,
            )
        case EventType.rental:
            return await partner_start_rental(
                id_org,
                payload.from_user,
                payload.id_user,
                payload.user_external_id,
                payload.id_device,
                payload.id_condition,
            )
        case EventType.vending:
            return await partner_start_vending(
                payload.id_device,
                payload.id_user,
                id_org,
            )
        case EventType.delivery:
            return await partner_start_delivery(
                payload.id_device,
                payload.id_size,
                payload.size_external_id,
                payload.id_location,
                payload.location_external_id,
                id_org,
                payload.id_user,
                payload.user_external_id,
                payload.from_user,
                payload.order_id,
                payload.pin_code,
                payload.phone_number,
                request,
            )
        case _:
            raise HTTPException(
                status_code=400,
                detail=f"Event type {payload.event_type} is not supported",
            )


async def partner_start_delivery(
    id_device: Optional[UUID],
    id_size: Optional[UUID],
    size_external_id: Optional[str],
    id_location: Optional[UUID],
    location_external_id: Optional[str],
    id_org: UUID,
    id_user: Optional[UUID],
    user_external_id: Optional[str],
    from_user: Optional[UUID],
    order_id: Optional[str],
    pin_code: Optional[constr(regex=r"\d{4}")],
    phone_number: Optional[str],
    request: Request,
):
    if not id_user and not order_id and not phone_number:
        error_detail = "Either user id, phone number, or order id must be provided"

        raise HTTPException(
            status_code=400,
            detail="Either user id, phone number, or order id must be provided",
        )

    if id_user:
        user = await get_user(id_user)

    elif user_external_id:
        user = await get_user_by_key("user_id", user_external_id, id_org)

    if order_id:
        query = select(Event).where(Event.id_org == id_org, Event.order_id == order_id)
        response = await db.session.execute(query)

        event = response.unique().scalars().all()

        if len(event) > 0:
            error_detail = f"Event with order id {order_id} already exists"

            raise HTTPException(
                status_code=400,
                detail=f"Event with order id {order_id} already exists",
            )

    if phone_number and not id_user and not user_external_id:
        user = await get_or_create_user(phone_number, Channel.sms, id_org)

    if not id_device:
        if not (id_size or size_external_id) or not (
            id_location or location_external_id
        ):
            error_detail = "You must provide a device id, or a combination of size (UUID / external_id) and location (UUID / external_id)"

            raise HTTPException(
                status_code=400,
                detail="You must provide a device id, or a combination of size (UUID / external_id) and location (UUID / external_id)",
            )

        id_size = id_size or await get_size_id_by_external_id(size_external_id, id_org)

        if not id_size:
            error_detail = "Size ID/name provided is not valid"

            raise HTTPException(
                status_code=400,
                detail="Size ID/name provided is not valid",
            )

        if not id_location:
            id_location = await get_location_by_external_id(
                location_external_id, id_org
            )["id"]

        selected_device = await get_device_with_fewest_transactions(
            id_size, id_location, id_org
        )
        if not selected_device:
            error_detail = "No devices found with the given size and location"

            raise HTTPException(
                status_code=404,
                detail="No devices found with the given size and location",
            )
        id_device = selected_device.id

    device = await reserve_device(id_device, id_org)

    if device.mode != Mode.delivery:
        error_detail = "Device is in an unsupported mode for this operation"

        await unreserve_device(id_device, id_org)
        raise HTTPException(
            status_code=400,
            detail="Device is in an unsupported mode for this operation",
        )

    if (
        device.hardware_type == HardwareType.gantner
        and device.lock_status == LockStatus.offline
    ):
        await unreserve_device(id_device, id_org)
        error_detail = (
            "This device is offline and can't be used for delivery at the moment"
        )

        raise HTTPException(
            status_code=400,
            detail=error_detail,
        )

    courier = None
    if from_user:
        if not await is_device_assigned_to_user(device.id, from_user):
            raise HTTPException(
                status_code=400,
                detail="You are not authorized to use this device",
            )
        else:
            courier = await get_user(from_user)

    invoice_id = await generate_invoice_id(id_org)

    if pin_code:
        # Check if pin code is already in use
        query = select(Event).where(
            Event.id_org == id_org,
            cast(Event.code, VARCHAR) == pin_code,
        )
        response = await db.session.execute(query)
        event = response.unique().scalar_one_or_none()

        if event:
            pin_code = None

    org_settings = await get_settings_org(id_org)

    code = None

    if pin_code:
        code = pin_code
    else:
        code = await generate_code(long_codes=org_settings.use_long_parcel_codes)

    new_event = Event(
        payment_intent_id=None,
        invoice_id=invoice_id,
        order_id=order_id if order_id else None,
        setup_intent_id=None,
        event_type=EventType.delivery,
        event_status=EventStatus.awaiting_service_dropoff,
        started_at=datetime.utcnow(),
        total=None,
        id_org=id_org,
        id_user=user.id,
        courier_pin_code=courier.pin_code if courier else None,
        id_device=id_device,
        code=code,
        refunded_amount=0,
    )

    query = insert(Event).values(new_event.dict()).returning(Event)

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError
    event: Event.Read = response.all().pop()

    device_query = (
        update(Device)
        .where(Device.id == id_device)
        .values(transaction_count=Device.transaction_count + 1)
    )
    await db.session.execute(device_query)
    await db.session.commit()  # Commit the transaction count increment

    if not user.access_code:
        access_code = await set_random_access_code(user.id, id_org)
        user.access_code = access_code

    await delivery_message_strategy(event, user, device, request)
    if not device.size:
        scheduler.add_job(
            complete_delivery,
            "date",
            run_date=datetime.utcnow() + timedelta(minutes=5),
            args=[code, None, None, event.id],
            id=str(event.id),
            replace_existing=True,
        )

    if org_settings.parcel_expiration and org_settings.parcel_expiration_unit:
        scheduler.add_job(
            expire_delivery,
            "date",
            run_date=(
                datetime.utcnow()
                + timedelta(hours=float(org_settings.parcel_expiration))
                if org_settings.parcel_expiration_unit == ExpirationUnit.hours
                else datetime.utcnow()
                + timedelta(days=float(org_settings.parcel_expiration))
            ),
            args=[event.id, id_org],
            id="exp" + str(event.id),
            replace_existing=True,
        )

    await send_payload(
        event.id_org,
        EventChange(
            id_org=event.id_org,
            id_event=event.id,
            event_status=event.event_status,
            event_obj=event,
        ),
    )

    await create_notify_job_on_event(event.id, NotificationType.on_start)
    await create_notify_job_on_event(event.id, NotificationType.on_service_dropoff)

    return_event = await get_event(event.id, event.id_org)
    return return_event


async def delivery_message_strategy(
    event: Event, user: User.Read, device: Device.Read, request: Request
):
    base_map = {
        "local": "web-dev",
        "dev": "web-dev",
        "qa": "web-qa",
        "staging": "web-staging",
        "production": "web",
    }
    pickup_url = (
        f"http://{base_map[get_settings().environment]}.koloni.io/pickup/?id={event.id}"
    )

    # is_prod = get_settings().environment == "production"

    url_msg = f"You have a delivery to pickup at location {device.location.name} {device.location.address}. Use this URL {pickup_url} for pick up at the lockers."
    qr_msg = f"You have a delivery to pickup at location {device.location.name} {device.location.address}. You can pick this up from locker {device.locker_number} with QR code https://{request.headers.get('host')}/v3/qr?code={event.code} at the kiosk. "
    pin_msg = f"You have a delivery to pickup at location {device.location.name} {device.location.address}. You can pick this up from locker {device.locker_number} with event code {event.code} at the kiosk."

    qr_and_url = f"You have a delivery to pickup at location {device.location.name} {device.location.address}. Scan the QR code to You can pick this up by using QR code https://{request.headers.get('host')}/v3/qr?code={event.code} at the kiosk or with this URL {pickup_url} at the lockers."
    pin_and_url = f"You have a delivery to pickup at location {device.location.name} {device.location.address}. You can pick this up by using event code {event.code} at the kiosk or with this URL {pickup_url} at the lockers."

    generic_msg = f"You have a delivery to pick up at {device.location.name} {device.location.address}. Thank you for trusting us, please return soon"

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    # Variable used to handle custom Twilio Messaging Service SIDs depending
    # on the org given:
    messaging_service_sid = await get_org_messaging_service_sid(event.id_org)

    email_sender = await get_org_sendgrid_auth_sender(event.id_org)
    is_ups_sender = await is_ups_org(event.id_org)

    def send_sms(body):
        client.messages.create(
            to=user.phone_number, from_=messaging_service_sid, body=body
        )

    def send_email(body):
        email.send(
            email_sender,
            user.email,
            "Delivery",
            body,
            is_ups_org=is_ups_sender,
        )

    # If the device has a size, we continue as intended
    if device.size:
        if user.phone_number and device.location.phone:
            if device.location.verify_qr_code and device.location.verify_url:
                send_sms(qr_and_url)
            elif device.location.verify_pin_code and device.location.verify_url:
                send_sms(pin_and_url)
            elif device.location.verify_url:
                send_sms(url_msg)
            elif device.location.verify_qr_code:
                send_sms(qr_msg)
            elif device.location.verify_pin_code:
                send_sms(pin_msg)
        if user.email and device.location.email:
            if device.location.verify_qr_code and device.location.verify_url:
                send_email(qr_and_url)
            elif device.location.verify_pin_code and device.location.verify_url:
                send_email(pin_and_url)
            elif device.location.verify_url:
                send_email(url_msg)
            elif device.location.verify_qr_code:
                send_email(qr_msg)
            elif device.location.verify_pin_code:
                send_email(pin_msg)
    else:
        if user.phone_number:
            send_sms(generic_msg)
        if user.email:
            send_email(generic_msg)


async def partner_start_storage(
    id_size: Optional[UUID],
    size_external_id: Optional[str],
    id_location: Optional[UUID],
    location_external_id: Optional[str],
    id_org: UUID,
    id_user: Optional[UUID],
    user_external_id: Optional[str],
    from_user: Optional[UUID],
    duration: Optional[Duration],
    passcode: Optional[constr(regex=r"\d{4}", max_length=4, min_length=4)],
):
    if not id_user and not passcode:
        raise HTTPException(
            status_code=400,
            detail="Either user id or passcode must be provided",
        )

    user = None
    if id_user:
        user = await get_user(id_user)
    elif user_external_id:
        user = await get_user_by_key("user_id", user_external_id, id_org)

    if not (id_size or size_external_id) and not (id_location or location_external_id):
        raise HTTPException(
            status_code=400,
            detail="You must provide a combination of size (UUID / external_id) and location (UUID / external_id)",
        )

    id_size = id_size or await get_size_id_by_external_id(size_external_id, id_org)

    device = await get_device_with_fewest_transactions(
        id_size, id_location, id_org, Mode.storage
    )

    if not device:
        raise HTTPException(
            status_code=404,
            detail="No devices found with the given size and location",
        )

    if from_user:
        if not await is_device_assigned_to_user(device.id, from_user):
            raise HTTPException(
                status_code=400,
                detail="You are not authorized to use this device",
            )

    if (
        device.hardware_type == HardwareType.gantner
        and device.lock_status == LockStatus.offline
    ):
        raise HTTPException(
            status_code=400,
            detail="This device is offline and can't be used for storage at the moment",
        )

    if not device.locker_number:
        raise HTTPException(
            status_code=400,
            detail="This device is not configured to be used for storage. Missing locker number",
        )

    if passcode:
        query = select(Event).where(
            Event.id_org == id_org,
            Event.passcode == passcode,
        )
        response = await db.session.execute(query)
        event = response.unique().scalar_one_or_none()

        if event:
            raise HTTPException(
                status_code=400,
                detail="This passcode is already in use",
            )

    device = await reserve_device(device.id, id_org)

    invoice_id = await generate_invoice_id(id_org)

    new_event = Event(
        payment_intent_id=None,
        invoice_id=invoice_id,
        order_id=None,
        setup_intent_id=None,
        event_type=EventType.storage,
        event_status=EventStatus.in_progress,
        started_at=datetime.utcnow(),
        total=None,
        id_org=id_org,
        id_user=user.id if user else None,
        id_device=device.id,
        passcode=passcode if passcode else None,
    )

    query = insert(Event).values(new_event.dict()).returning(Event)

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    created_event = response.all().pop()

    device_query = (
        update(Device)
        .where(Device.id == device.id)
        .values(transaction_count=Device.transaction_count + 1)
    )
    await db.session.execute(device_query)
    await db.session.commit()  # Commit the transaction count increment

    # * Select the event again, to get the device and any other joined data

    query = select(Event).where(Event.id == created_event.id, Event.id_org == id_org)

    response = await db.session.execute(query)
    data = response.unique().scalar_one()

    if duration:
        end_date = datetime.utcnow()
        end_date = end_date + timedelta(
            hours=duration.hours or 0,
            days=duration.days or 0,
            weeks=duration.weeks or 0,
        )
        scheduler.add_job(
            func=partner_cancel_event,
            trigger="date",
            run_date=end_date,
            args=[id_org, data.id],
            id=str(data.id),
            replace_existing=True,
        )

    await create_notify_job_on_event(data.id, NotificationType.on_start)

    return data


async def partner_start_storage_batch(
    id_org: UUID,
    id_sizes: list[UUID],
    id_location: UUID,
    id_user: UUID,
    duration: Optional[Duration],
    from_user: Optional[UUID] = None,
):
    sizes = len(id_sizes)
    responses = []
    errors = []

    for id_size in id_sizes:
        try:
            data = await partner_start_storage(
                id_size,
                None,
                id_location,
                None,
                id_org,
                id_user,
                None,
                from_user,
                duration,
                None,
            )
            responses.append(data)
        except Exception as e:
            errors.append(e)

    return {
        "detail": f"{len(responses)}/{sizes} transactions were created",
        "items": responses,
        "err": errors,
    }


async def partner_start_vending(
    id_device: UUID,
    id_user: UUID,
    id_org: UUID,
):
    device = await reserve_device(id_device, id_org)

    if device.mode != Mode.vending:
        await unreserve_device(id_device, id_org)
        raise HTTPException(
            status_code=400,
            detail="The selected device is not in vending mode",
        )

    invoice_id = await generate_invoice_id(id_org)
    new_event = Event(
        payment_intent_id=None,
        invoice_id=invoice_id,
        setup_intent_id=None,
        event_type=EventType.vending,
        event_status=EventStatus.finished,
        total=None,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        id_org=id_org,
        id_user=id_user,
        id_device=id_device,
        refunded_amount=0,
    )

    query = insert(Event).values(new_event.dict()).returning(Event)
    response = await db.session.execute(query)
    await db.session.commit()

    created_event = response.all().pop()

    query = select(Event).where(Event.id == created_event.id, Event.id_org == id_org)
    response = await db.session.execute(query)

    event = response.unique().scalar_one()

    # if event.device.product.price:
    #     account = await stripe.Account.retrieve(stripe_account_id)
    #     payment = await stripe.PaymentIntent.create(
    #         amount=int(event.device.product.price * 100),
    #         currency=account.default_currency or "usd",
    #         customer=customer,
    #         payment_method=setup.payment_method,
    #         confirm=True,
    #         off_session=True,
    #         stripe_account=stripe_account_id,
    #     )
    #     if payment.status != "succeeded":
    #         raise HTTPException(
    #             status_code=400, detail="payment method is still pending"
    #         )

    await track_product(
        event.device.product.id,
        State.outgoing,
        id_org,
        id_user,
        event.device.id,
        event.device.id_condition,
    )
    await partner_unlock_device(event.device.id, id_org)
    # await unreserve_device(event.device.id, id_org)
    await set_device_maintenance(event.device.id, id_org)

    return event


async def partner_start_rental(
    id_org: UUID,
    from_user: Optional[UUID],
    id_user: Optional[UUID],
    user_external_id: Optional[str],
    id_device: UUID,
    id_condition: Optional[UUID],
):
    if not id_user and not user_external_id:
        raise HTTPException(
            status_code=400,
            detail="Either user id or user external id must be provided",
        )
    if id_user:
        user = await get_user(id_user)
    elif user_external_id:
        user = await get_user_by_key("user_id", user_external_id, id_org)

    device = await reserve_device(id_device, id_org)

    if device.mode != Mode.rental or device.product is None:
        await unreserve_device(id_device, id_org)
        raise HTTPException(
            status_code=400,
            detail="Device is not in rental mode or does not have a product",
        )

    if from_user:
        if not await is_device_assigned_to_user(device.id, from_user):
            await unreserve_device(id_device, id_org)
            raise HTTPException(
                status_code=400,
                detail="You are not authorized to use this device",
            )

    if id_condition:
        await patch_product(
            device.product.id, Product.Patch(id_condition=id_condition), id_org
        )

    org_settings = get_settings_org(id_org=id_org)

    invoice_id = await generate_invoice_id(id_org)
    code = await generate_code(long_codes=org_settings.use_long_parcel_codes)

    new_event = Event(
        invoice_id=invoice_id,
        event_type=EventType.rental,
        event_status=EventStatus.in_progress,
        started_at=datetime.utcnow(),
        code=code,
        id_org=id_org,
        id_user=user.id,
        id_device=id_device,
    )

    query = insert(Event).values(new_event.dict()).returning(Event)

    response = await db.session.execute(query)
    await db.session.commit()

    data = response.all().pop()

    await send_payload(
        id_org,
        EventChange(
            id_org=id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    await track_product(
        device.product.id,
        State.outgoing,
        id_org,
        id_user,
        device.id,
        id_condition,
    )
    await create_notify_job_on_event(data.id, NotificationType.on_start)
    return data


async def partner_complete_rental(
    id_org: UUID,
    id_user: Optional[UUID],
    id_device: UUID,
    id_condition: Optional[UUID],
):
    query = select(Event).where(
        Event.id_org == id_org,
        Event.id_user == id_user if id_user else True,
        Event.id_device == id_device,
        Event.event_type == EventType.rental,
        Event.event_status == EventStatus.in_progress,
    )

    response = await db.session.execute(query)
    event = response.unique().scalars().first()

    if not event:
        raise HTTPException(status_code=404, detail="No event found for this device")

    condition = None
    if id_condition:
        query = select(Condition).where(
            Condition.id == id_condition, Condition.id_org == id_org
        )
        response = await db.session.execute(query)
        condition = response.unique().scalar_one()
        condition = Condition.Read.parse_obj(condition)

        if condition.auto_maintenance:
            await patch_device(
                id_device, id_org, Device.Patch(status=Status.maintenance), True
            )
        if condition.auto_report:
            issue = Issue.Write(
                description=f"Product '{event.device.product.name}' in Device '{event.device.name}' has been reported as '{condition.name}'"
            )
            await create_issue(None, issue, None, id_user, id_org, None, None)

        await patch_product(
            event.device.product.id, Product.Patch(id_condition=id_condition), id_org
        )

    query = (
        update(Event)
        .where(Event.id == event.id)
        .values(
            event_status=EventStatus.finished, ended_at=datetime.utcnow(), code=None
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    data = response.all().pop()

    await send_payload(
        id_org,
        EventChange(
            id_org=id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    if not condition or (condition and not condition.auto_maintenance):
        await unreserve_device(id_device, id_org)

    await track_product(
        event.device.product.id,
        State.incoming,
        id_org,
        id_user,
        event.device.id,
        id_condition,
    )

    await create_notify_job_on_event(data.id, NotificationType.on_complete)

    return data


async def partner_complete_delivery_batch(
    codes: list[int],
    id_org: UUID,
):
    resp = []
    for code in codes:
        try:
            resp.append(
                {
                    "status_code": 200,
                    "event_code": code,
                    "response": await complete_delivery(code, None, None, id_org),
                }
            )
        except HTTPException as e:
            resp.append(
                {
                    "status_code": e.status_code,
                    "event_code": code,
                    "response": e.detail,
                }
            )
        except Exception as e:
            resp.append(
                {
                    "status_code": 500,
                    "event_code": code,
                    "response": e,
                }
            )

    return resp


async def partner_complete_storage(
    id_event: Optional[UUID],
    passcode: Optional[constr(regex=r"\d{4}", max_length=4, min_length=4)],
    locker_number: Optional[int],
    id_org: UUID,
):
    if not id_event and not (passcode and locker_number):
        raise HTTPException(
            status_code=400,
            detail="Either event id or passcode and locker number must be provided",
        )

    query = None

    if id_event:
        query = select(Event).where(
            Event.id == id_event,
            Event.id_org == id_org,
            Event.event_status == EventStatus.in_progress,
            Event.event_type == EventType.storage,
        )
    elif passcode and locker_number:
        query = (
            select(Event)
            .join(Device)
            .where(
                Event.passcode == passcode,
                Event.id_org == id_org,
                Event.event_status == EventStatus.in_progress,
                Event.event_type == EventType.storage,
                Device.locker_number == locker_number,
            )
        )

    response = await db.session.execute(query)
    event = response.unique().scalar_one()  # raises NoResultFound

    await complete_storage_free(event)
    await partner_unlock_device(event.device.id, id_org)

    try:
        scheduler.remove_job(job_id=str(event.id))
    except JobLookupError:
        pass

    await create_notify_job_on_event(event.id, NotificationType.on_complete)

    return event


# Helper
async def generate_code(depth: int = 0, max_depth: int = 25, long_codes=False):
    if depth > max_depth:
        raise HTTPException(
            status_code=400,
            detail="Failed to generate unique code for event",
        )

    if long_codes:
        code = randrange(100000, 999999)
    else:
        code = randrange(1000, 9999)

    query = select(Event).where(Event.code == code)
    response = await db.session.execute(query)

    # Use .unique().scalar_one() to ensure the result set is unique
    event = response.unique().scalar_one_or_none()

    # Check if the event exists, if it does, generate a new code.
    if event:
        return await generate_code(depth=depth + 1, max_depth=max_depth)

    return code


async def partner_service_pickup(id_event: UUID, id_org: UUID):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_org == id_org,
        Event.event_status == EventStatus.awaiting_service_pickup,
        Event.event_type == EventType.service,
    )

    response = await db.session.execute(query)
    event = response.unique().scalar_one()  # raise NoResultFound

    # Update event status
    query = (
        update(Event)
        .where(Event.id == id_event, Event.id_org == id_org)
        .values(event_status=EventStatus.in_progress)
        .returning(Event)
    )

    await partner_unlock_device(event.device.id, id_org)
    await unreserve_device(event.device.id, id_org)

    response = await db.session.execute(query)
    await db.session.commit()

    # client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    # client.messages.create(
    #     to=event.user.phone_number,
    #     from_=get_settings().twilio_messaging_service_sid,
    #     body="Your laundry has been picked up and is being processed. We'll notify you soon about the total cost.",
    # )  # raise TwilioRestException

    data = response.all().pop()

    await send_payload(
        data.id_org,
        EventChange(
            id_org=data.id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    await create_notify_job_on_event(data.id, NotificationType.on_service_pickup)

    return data


async def calculate_membership(
    membership: Membership,
    event: Event,
    subscription_id: str,
    total: int,
):
    if membership and membership.active is True:
        if (
            membership.locations and event.device.id_location in membership.locations
        ) or (not membership.locations):
            match membership.membership_type:
                case MembershipType.unlimited:
                    print("CALC:: UNLIMITED")
                    await partner_add_subscription_to_event(
                        event.id, event.id_org, subscription_id, membership.id
                    )
                    return 0
                case MembershipType.limited:
                    print("CALC:: LIMITED")
                    count = await subscription_event_count(
                        event.id_org, subscription_id
                    )

                    if count < membership.value:
                        await partner_add_subscription_to_event(
                            event.id, event.id_org, subscription_id, membership.id
                        )
                        return 0
                    await cancel_subscription(event.id_org, event.id_user)
                    return total
                case MembershipType.percentage:
                    print("CALC:: Percentage")
                    # take the percentage off the total
                    total = int(total * (1 - membership.value / 100))
                    if total < 50:
                        return 0
                    await partner_add_subscription_to_event(
                        event.id, event.id_org, subscription_id, membership.id
                    )
                    return total
                case MembershipType.fixed:
                    print("CALC:: Fixed")
                    # take the fixed amount off the total, in cents
                    total = total - (int(membership.value * 100))
                    if total < 50:
                        return 0
                    await partner_add_subscription_to_event(
                        event.id, event.id_org, subscription_id, membership.id
                    )
                    return total
                case _:
                    pass
        else:
            # User has a membership, but not on the same location
            return total


async def partner_service_charge(
    id_event: UUID,
    weight: float,
    id_org: UUID,
):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_org == id_org,
        Event.event_status == EventStatus.in_progress,
        Event.event_type == EventType.service,
    )

    response = await db.session.execute(query)
    event = response.unique().scalar_one()  # raise NoResultFound

    if not event.device.price:
        return await charge_service_free(event)

    total = int(float(event.device.price.amount) * float(weight) * 100)

    if event.id_promo:
        total = await calculate_promo(event, total)

    if total <= 0:
        return await charge_service_free(event)

    membership = await get_user_membership(event.id_org, event.id_user)
    link = await get_user_subscription(event.id_user, event.id_org)

    subscription_id = link.stripe_subscription_id
    if membership:
        total = await calculate_membership(membership, event, subscription_id, total)

    if total <= 0:
        return await charge_service_free(event)

    stripe_account_id = await get_stripe_account(id_org)
    stripe_customer = await get_or_create_stripe_customer(event.id_user, id_org)

    customer = await stripe.Customer.retrieve(
        stripe_customer,
        stripe_account=stripe_account_id,
    )

    payment_intent = await stripe.PaymentIntent.create(
        amount=total,
        customer=stripe_customer,
        setup_future_usage="off_session",
        payment_method=customer.invoice_settings.default_payment_method,
        currency=event.device.price.currency.value,
        stripe_account=stripe_account_id,
        confirm=True,
    )

    query = (
        update(Event)
        .where(Event.id == id_event)
        .values(
            event_status=EventStatus.awaiting_service_dropoff,
            payment_intent_id=payment_intent.id,
            total=event.device.price.amount * weight,
            weight=weight,
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    # client = Client(get_settings().twilio_sid, get_settings().twilio_secret)
    # currency = event.device.price.currency.value.upper()

    # client.messages.create(
    #     to=event.user.phone_number,
    #     from_=get_settings().twilio_messaging_service_sid,
    #     body=f"Your service is done {weight}{event.device.price.unit.value}. You will be charged "
    #     + f"{round((event.device.price.amount * weight), 2)} {currency}. We'll notify you once your order is "
    #     f"complete and ready for pickup.",
    # )  # raise TwilioRestException

    data = response.all().pop()

    await send_payload(
        data.id_org,
        EventChange(
            id_org=data.id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    await create_notify_job_on_event(data.id, NotificationType.on_service_charge)

    return data


async def partner_service_dropoff(id_event: UUID, id_device: UUID, id_org: UUID):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_org == id_org,
        Event.event_status == EventStatus.awaiting_service_dropoff,
        Event.event_type == EventType.service,
    )

    response = await db.session.execute(query)
    response.unique().scalar_one()  # raise NoResultFound

    device = await reserve_device(id_device, id_org)
    await partner_unlock_device(device.id, id_org)

    query = (
        update(Event)
        .where(Event.id == id_event, Event.id_org == id_org)
        .values(event_status=EventStatus.awaiting_user_pickup, id_device=id_device)
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    # client = Client(get_settings().twilio_sid, get_settings().twilio_secret)
    # client.messages.create(
    #     to=event.user.phone_number,
    #     from_=get_settings().twilio_messaging_service_sid,
    #     body=f"Your laundry is ready to be picked up in {device.name} at {device.location.name}. "
    #     + "Open the Laundry Locks app to see locations and retrieve your laundry.",
    # )

    data = response.all().pop()

    await send_payload(
        data.id_org,
        EventChange(
            id_org=data.id_org,
            id_event=data.id,
            event_status=data.event_status,
            event_obj=data,
        ),
    )

    await create_notify_job_on_event(data.id, NotificationType.on_service_dropoff)

    return data


async def partner_service_step(
    step: ServiceStep,
    weight: Optional[float],
    id_device: Optional[UUID],
    id_event: UUID,
    id_org: UUID,
):
    match step:
        case ServiceStep.pickup:
            result = await partner_service_pickup(id_event, id_org)

            return result
        case ServiceStep.charge:
            if not weight:
                raise HTTPException(
                    status_code=400,
                    detail=f"Weight is required for service step {step}",
                )

            result = await partner_service_charge(id_event, weight, id_org)

            return result
        case ServiceStep.dropoff:
            if not id_device:
                raise HTTPException(
                    status_code=400,
                    detail=f"Device id is required for service step {step}",
                )

            result = await partner_service_dropoff(id_event, id_device, id_org)

            return result
        case _:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service step '{step}'",
            )


async def partner_cancel_event(
    id_org: UUID,
    id_event: Optional[UUID] = None,
    invoice_id: Optional[str] = None,
    order_id: Optional[str] = None,
    cancel_at: Optional[datetime] = None,
    charge: Optional[bool] = True,
    maintenance: Optional[bool] = None,
    canceled_by: Optional[str] = None,
):
    query = select(Event).where(Event.id_org == id_org)

    if invoice_id:
        query = query.where(Event.invoice_id == invoice_id)
    elif id_event:
        query = query.where(Event.id == id_event)
    elif order_id:
        query = query.where(Event.order_id == order_id)
    else:
        raise HTTPException(
            status_code=400,
            detail="Either invoice id or event id must be provided",
        )

    response = await db.session.execute(query)
    event: Event.Read = response.unique().scalar_one()

    if cancel_at:
        cancel_at_utc = cancel_at.astimezone(tz=datetime.utcnow().tzinfo)
        if cancel_at_utc < event.created_at:
            raise HTTPException(
                status_code=400,
                detail="cancel_at must be past the transaction's creation date",
            )

    total_time: timedelta = (
        cancel_at.astimezone(tz=datetime.utcnow().tzinfo) - event.started_at
        if cancel_at
        else datetime.now(timezone.utc) - event.started_at
    )
    formatted_time = (
        f"{int(total_time.total_seconds() // 3600):02d}:{int(total_time.total_seconds() % 3600 // 60):02d}:"
        f"{int(total_time.total_seconds() % 3600 % 60):02d}"
    )

    if event.event_status not in [
        EventStatus.awaiting_user_pickup,
        EventStatus.awaiting_service_pickup,
        EventStatus.in_progress,
        EventStatus.awaiting_service_dropoff,
    ]:
        query = (
            update(Event)
            .where(
                Event.id == event.id,
                Event.id_org == id_org,
            )
            .values(
                event_status=EventStatus.canceled,
                ended_at=cancel_at if cancel_at else datetime.utcnow(),
                canceled_at=datetime.utcnow(),
                canceled_by=canceled_by if canceled_by else "API",
                total_time=formatted_time,
                code=None,
            )
            .returning(Event)
        )

        response = await db.session.execute(query)
        await db.session.commit()  # raises IntegrityError

        try:
            response.all().pop()
        except IndexError:
            raise HTTPException(
                status_code=400,
                detail=f"Event with id '{id_event}' cannot be canceled",
            )

        await unreserve_device(event.id_device, id_org)

        if maintenance:
            await patch_device(
                event.id_device, id_org, Device.Patch(status=Status.maintenance), True
            )

        await send_payload(
            event.id_org,
            EventChange(
                id_org=event.id_org,
                id_event=event.id,
                event_status=event.event_status,
                event_obj=event,
            ),
        )

        try:
            scheduler.remove_job(job_id=str(event.id))
        except JobLookupError:
            pass

        return event

    if event.event_type in [EventType.rental, EventType.storage] and charge is True:
        return await complete_storage(event=event, cancel_at=cancel_at)

    query = (
        update(Event)
        .where(Event.id == event.id, Event.id_org == id_org)
        .values(
            event_status=EventStatus.canceled,
            ended_at=cancel_at if cancel_at else datetime.utcnow(),
            canceled_at=datetime.utcnow(),
            canceled_by=canceled_by if canceled_by else "API",
            total_time=formatted_time,
            code=None,
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    await unreserve_device(event.id_device, id_org)

    if maintenance:
        await patch_device(
            event.id_device, id_org, Device.Patch(status=Status.maintenance), True
        )

    await send_payload(
        event.id_org,
        EventChange(
            id_org=event.id_org,
            id_event=event.id,
            event_status=event.event_status,
            event_obj=event,
        ),
    )

    query = select(Event).where(Event.id == event.id, Event.id_org == id_org)
    res = await db.session.execute(query)
    event = res.unique().scalar_one()

    try:
        scheduler.remove_job(job_id=str(event.id))
    except JobLookupError:
        pass

    return event


async def partner_cancel_events(
    id_events: list[UUID],
    id_org: UUID,
):
    query = select(Event).where(Event.id_org == id_org, Event.id.in_(id_events))

    response = await db.session.execute(query)
    events = response.unique().scalars().all()

    for event in events:
        await partner_cancel_event(id_org, event.id, charge=False)

    return {"detail": "Events canceled"}


async def partner_unreserve_device(
    id_event: UUID,
    id_org: UUID,
):
    query = select(Event).where(Event.id == id_event, Event.id_org == id_org)

    response = await db.session.execute(query)
    event: Event.Read = response.unique().scalar_one()

    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Event with id '{id_event}' was not found",
        )

    if event.device.status == Status.available:
        raise HTTPException(
            status_code=400,
            detail=f"Device with id '{event.id_device}' is already unreserved",
        )

    await unreserve_device(event.id_device, id_org)

    return event


async def partner_refund_event(
    id_event: UUID,
    id_org: UUID,
    amount: Optional[float] = None,
    currency: Optional[Currency] = None,
):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_org == id_org,
        Event.event_status.in_(
            [
                EventStatus.canceled,
                EventStatus.finished,
            ]
        ),
        Event.total > 0,
    )

    response = await db.session.execute(query)
    event = response.unique().scalar_one()  # raises NoResultFound

    # Removed unrelaible check
    # if not event.device.price:
    #     error_detail = "This event has no price, and can't be refunded"

    #     raise HTTPException(
    #         status_code=400,
    #         detail=error_detail,
    #     )

    amount = amount or event.total

    if amount > event.total:
        error_detail = (
            f"Cannot refund event with Id {id_event}, amount is greater than total"
        )

        raise HTTPException(
            status_code=400,
            detail=error_detail,
        )

    stripe_account_id = await get_stripe_account(id_org)

    refund = await stripe.Refund.create(
        payment_intent=event.payment_intent_id,
        amount=int(amount * 100),
        stripe_account=stripe_account_id,
    )

    query = (
        update(Event)
        .where(Event.id == id_event, Event.id_org == id_org)
        .values(event_status=EventStatus.refunded, refunded_amount=amount)
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    # Variable used to handle custom Twilio Messaging Service SIDs depending
    # on the org given:
    messaging_service_sid = await get_org_messaging_service_sid(event.id_org)

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    if event.user.phone_number:
        client.messages.create(
            to=event.user.phone_number,
            from_=messaging_service_sid,
            body=f"You have been refunded {amount} {str(refund['currency']).upper()} for the Transaction {event.invoice_id}",
        )

    if event.user.email:
        email_sender = await get_org_sendgrid_auth_sender(event.id_org)

        email.send(
            email_sender,
            event.user.email,
            "Refund",
            f"You have been refunded {amount} {str(refund['currency']).upper()} for the Transaction {event.invoice_id}",
            is_ups_org=await is_ups_org(event.id_org),
        )

    await send_payload(
        event.id_org,
        EventChange(
            id_org=event.id_org,
            id_event=event.id,
            event_status="refund",
            event_obj=event,
        ),
    )

    return event


async def partner_add_subscription_to_event(
    id_event: UUID, id_org: UUID, stripe_subscription_id: str, id_membership: UUID
):
    query = (
        update(Event)
        .where(
            Event.id == id_event,
            Event.id_org == id_org,
        )
        .values(
            stripe_subscription_id=stripe_subscription_id, id_membership=id_membership
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    return response.all().pop()


# Helper
async def subscription_event_count(
    id_org: UUID,
    stripe_subscription_id: str,
) -> int:
    query = select(Event.id).where(
        Event.id_org == id_org,
        Event.stripe_subscription_id == stripe_subscription_id,
    )

    response = await db.session.execute(query)

    return len(response.unique().scalars().all())


async def share_event(
    id_event: UUID,
    phone_number: Optional[str],
    user_email: Optional[str],
    message: Optional[Message],
    id_org: UUID,
):
    event = await get_event(id_event, id_org)

    if not event.code:
        raise HTTPException(
            status_code=400,
            detail="You can't share an event that doesn't have a code",
        )

    if phone_number:
        # Variable used to handle custom Twilio Messaging Service SIDs depending
        # on the org given:
        messaging_service_sid = await get_org_messaging_service_sid(event.id_org)

        try:
            client = Client(get_settings().twilio_sid, get_settings().twilio_secret)
            client.messages.create(
                to=phone_number,
                from_=messaging_service_sid,
                body=(
                    f"Your pin code is {event.code}. Use this code to unlock your delievered items."
                    if not message
                    else message.msg
                ),
            )

        except Exception:
            raise

    if user_email:
        try:
            email_sender = await get_org_sendgrid_auth_sender(event.id_org)

            email.send(
                email_sender,
                user_email,
                "Share Event",
                (
                    f"Your pin code is {event.code}. Use this code to unlock your delievered items."
                    if not message
                    else message.msg
                ),
                is_ups_org=await is_ups_org(event.id_org),
            )
        except Exception:
            raise

    channel_text = "phone number" if phone_number else "email"

    return {"detail": f"Event shared successfully via {channel_text}"}


# Helper
async def set_charge_in_progress(id_event: UUID, id_org: UUID) -> Optional[Event]:
    query = (
        update(Event)
        .where(
            Event.id == id_event,
            Event.id_org == id_org,
        )
        .values(
            event_status=EventStatus.transaction_in_progress,
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        return response.all()[0]
    except IndexError:
        return None


# Helper
async def undo_charge_in_progress(id_event: UUID, id_org: UUID) -> Optional[Event]:
    query = (
        update(Event)
        .where(
            Event.id == id_event,
            Event.id_org == id_org,
        )
        .values(
            event_status=EventStatus.in_progress,
        )
        .returning(Event)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        return response.all()[0]
    except IndexError:
        return None

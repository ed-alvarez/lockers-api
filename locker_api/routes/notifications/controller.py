from datetime import datetime, timedelta
from math import ceil
from pathlib import Path
from typing import Optional
from uuid import UUID
from uuid import uuid4

from config import get_settings
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, insert, or_, select, update
from twilio.rest import Client
from util import email

from util.scheduler import scheduler

from ..event.model import Event
from ..organization.model import Org
from ..organization.controller import (
    get_org_messaging_service_sid,
    get_org_sendgrid_auth_sender,
    is_ups_org,
)
from ..settings.controller import get_settings_org
from ..white_label.controller import partner_get_white_label
from ..member.controller import get_user as get_cognito_member
from .default_notifications import DEFAULT_NOTIFICATIONS
from .model import (
    LinkNotificationLocation,
    Notification,
    NotificationType,
    PaginatedNotifications,
    TimeUnit,
    RecipientType,
)


async def partner_get_notification(id_notification: UUID, id_org: UUID):
    query = select(Notification).where(
        Notification.id == id_notification, Notification.id_org == id_org
    )
    response = await db.session.execute(query)

    return response.unique().scalar_one()


async def partner_get_notifications(
    page: conint(gt=0),
    size: conint(gt=0),
    user_pool: str,
    id_org: UUID,
    id_notification: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    by_type: Optional[NotificationType] = None,
):
    query = select(Notification).where(Notification.id_org == id_org)

    if id_notification:
        # * Early return if id_notification is provided

        query = query.where(Notification.id == id_notification)
        result = await db.session.execute(query)
        notification = result.unique().scalar_one()

        if notification.id_member:
            notification = Notification.Read.parse_obj(notification)
            try:
                member = await get_cognito_member(
                    user_pool, str(notification.id_member)
                )
                notification.member = member
            except Exception:
                pass

        return notification

    if key and value:
        # * Early return if key and value are provided

        if key not in Notification.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )

        query = query.filter(
            cast(Notification.__table__.columns[key], VARCHAR) == value
        )

        result = await db.session.execute(query)
        notification = result.unique().scalar_one()

        if notification.id_member:
            notification = Notification.Read.parse_obj(notification)
            try:
                member = await get_cognito_member(
                    user_pool, str(notification.id_member)
                )
                notification.member = member
            except Exception:
                pass
        return notification

    notifcations = await db.session.execute(query)

    if len(notifcations.unique().scalars().all()) == 0:
        for notification in DEFAULT_NOTIFICATIONS:
            await partner_create_notification(notification, id_org)

    if search:
        query = query.where(
            or_(
                Notification.name.ilike(f"%{search}%"),
                Notification.message.ilike(f"%{search}%"),
            )
        )

    if by_type:
        query = query.where(Notification.notification_type == by_type)

    count = query

    query = (
        query.limit(size)
        .offset((page - 1) * size)
        .order_by(Notification.created_at.desc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    notifcations = data.unique().scalars().all()

    result = []
    # add a cache to avoid multiple requests to cognito
    members = {}
    for notification in notifcations:
        notification = Notification.Read.parse_obj(notification)
        if notification.id_member:
            if notification.id_member not in members:
                try:
                    member = await get_cognito_member(
                        user_pool, str(notification.id_member)
                    )
                    notification.member = member
                    result.append(notification)
                    members[notification.id_member] = member
                except Exception:
                    pass
        else:
            result.append(notification)

    return PaginatedNotifications(
        items=result,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def partner_delete_twilio_link(id_org: UUID):
    query = select(Org).where(Org.id == id_org)

    response = await db.session.execute(query)
    org: Org.Read = response.unique().scalar_one_or_none()

    # Checking if organization exists
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    query = update(Org).where(Org.id == id_org).values(twilio_sid=None).returning(Org)

    await db.session.execute(query)
    await db.session.commit()

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)
    client.authorized_connect_apps(org.twilio_sid).delete()

    return {"detail": "Twilio unlinked"}


async def partner_get_twilio_link(id_org: UUID):
    query = select(Org).where(Org.id == id_org)
    response = await db.session.execute(query)

    org = response.unique().scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not org.twilio_sid:
        raise HTTPException(status_code=404, detail="Twilio not authorized")

    return {"detail": "Twilio authorized"}


async def partner_auth_twilio(id_org: UUID, AccountSid: str):
    query = (
        update(Org).where(Org.id == id_org).values(twilio_sid=AccountSid).returning(Org)
    )

    await db.session.execute(query)
    await db.session.commit()

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    return client.authorized_connect_apps(AccountSid).fetch()


async def partner_deauth_twilio(id_org: UUID, AccountSid: str):
    query = update(Org).where(Org.id == id_org).values(twilio_sid=None).returning(Org)

    await db.session.execute(query)
    await db.session.commit()

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    return client.authorized_connect_apps(AccountSid).delete()


async def partner_create_notification(
    notification: Notification.Write,
    id_org: UUID,
) -> Notification.Read:
    new_notification = Notification(
        name=notification.name,
        message=notification.message,
        mode=notification.mode,
        notification_type=notification.notification_type,
        time_amount=notification.time_amount,
        time_unit=notification.time_unit,
        before=notification.before,
        after=notification.after,
        email=notification.email,
        sms=notification.sms,
        push=notification.push,
        email_2nd=notification.email_2nd,
        sms_2nd=notification.sms_2nd,
        push_2nd=notification.push_2nd,
        is_template=notification.is_template,
        id_member=notification.id_member,
        recipient_type=notification.recipient_type,
    )

    query = (
        insert(Notification)
        .values(**new_notification.dict(), id_org=id_org)
        .returning(Notification)
    )

    response = await db.session.execute(query)

    inserted_notification = response.unique().all().pop()

    if notification.locations:
        query = insert(LinkNotificationLocation).values(
            [
                {"id_location": location, "id_notification": inserted_notification.id}
                for location in notification.locations
            ]
        )

        await db.session.execute(query)
        await db.session.commit()

    else:
        await db.session.commit()

    return inserted_notification


async def partner_update_notification(
    id_notification: UUID, notification: Notification.Write, id_org: UUID
) -> Notification.Read:
    query = (
        update(Notification)
        .where(Notification.id == id_notification, Notification.id_org == id_org)
        .values(
            {
                "name": notification.name,
                "message": notification.message,
                "mode": notification.mode,
                "notification_type": notification.notification_type,
                "time_amount": notification.time_amount,
                "time_unit": notification.time_unit,
                "before": notification.before,
                "after": notification.after,
                "email": notification.email,
                "sms": notification.sms,
                "push": notification.push,
                "email_2nd": notification.email_2nd,
                "sms_2nd": notification.sms_2nd,
                "push_2nd": notification.push_2nd,
                "is_template": notification.is_template,
                "id_member": notification.id_member,
                "recipient_type": notification.recipient_type,
            }
        )
        .returning(Notification)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    if notification.locations:
        query = delete(LinkNotificationLocation).where(
            LinkNotificationLocation.id_notification == id_notification
        )

        await db.session.execute(query)
        await db.session.commit()

        query = insert(LinkNotificationLocation).values(
            [
                {"id_notification": id_notification, "id_location": location}
                for location in notification.locations
            ]
        )

        await db.session.execute(query)
        await db.session.commit()

    if len(notification.locations) == 0:
        query = delete(LinkNotificationLocation).where(
            LinkNotificationLocation.id_notification == id_notification
        )

        await db.session.execute(query)
        await db.session.commit()

    updated_notification = response.all().pop()

    return updated_notification


async def partner_patch_notification(
    id_notification: UUID, notification: Notification.Patch, id_org: UUID
) -> Notification.Read:
    query = (
        update(Notification)
        .where(Notification.id == id_notification, Notification.id_org == id_org)
        .values(
            {
                "name": notification.name if notification.name else None,
                "message": notification.message if notification.message else None,
                "mode": notification.mode if notification.mode else None,
                "notification_type": (
                    notification.notification_type
                    if notification.notification_type
                    else None
                ),
                "time_amount": (
                    notification.time_amount if notification.time_amount else None
                ),
                "time_unit": notification.time_unit if notification.time_unit else None,
                "email": notification.email if notification.email else None,
                "sms": notification.sms if notification.sms else None,
                "push": notification.push if notification.push else None,
                "email_2nd": notification.email_2nd if notification.email_2nd else None,
                "sms_2nd": notification.sms_2nd if notification.sms_2nd else None,
                "push_2nd": notification.push_2nd if notification.push_2nd else None,
                "is_template": (
                    notification.is_template if notification.is_template else None
                ),
                "id_member": notification.id_member if notification.id_member else None,
                "recipient_type": (
                    notification.recipient_type if notification.recipient_type else None
                ),
            }
        )
        .returning(Notification)
    )
    response = await db.session.execute(query)
    await db.session.commit()

    if notification.locations:
        query = delete(LinkNotificationLocation).where(
            LinkNotificationLocation.id_notification == id_notification
        )

        await db.session.execute(query)
        await db.session.commit()

        query = insert(LinkNotificationLocation).values(
            [
                {"id_notification": id_notification, "id_location": location}
                for location in notification.locations
            ]
        )

        await db.session.execute(query)
        await db.session.commit()

    if len(notification.locations) == 0:
        query = delete(LinkNotificationLocation).where(
            LinkNotificationLocation.id_notification == id_notification
        )

        await db.session.execute(query)
        await db.session.commit()

    updated_notification = response.all().pop()

    return updated_notification


async def partner_patch_notifications(
    id_notifications: list[UUID], notification: Notification.Patch, id_org: UUID
):
    for id_notification in id_notifications:
        await partner_patch_notification(id_notification, notification, id_org)

    return {"detail": "Notifications updated"}


async def partner_delete_notification(id_notification: UUID, id_org: UUID):
    query = (
        delete(Notification)
        .where(
            Notification.id == id_notification,
            Notification.id_org == id_org,
            Notification.is_template == False,  # noqa: E712
        )
        .returning(Notification)
    )
    response = await db.session.execute(query)

    await db.session.commit()

    query = delete(LinkNotificationLocation).where(
        LinkNotificationLocation.id_notification == id_notification
    )

    await db.session.execute(query)
    await db.session.commit()

    try:
        deleted_notification = response.all().pop()

        return deleted_notification
    except IndexError:
        raise HTTPException(status_code=404, detail="Notification not found")


async def partner_delete_notifications(id_notifications: list[UUID], id_org: UUID):
    query = (
        delete(Notification)
        .where(
            Notification.id.in_(id_notifications),
            Notification.id_org == id_org,
            Notification.is_template == False,  # noqa: E712
        )
        .returning(Notification)
    )
    await db.session.execute(query)
    await db.session.commit()

    query = delete(LinkNotificationLocation).where(
        LinkNotificationLocation.id_notification.in_(id_notifications)
    )

    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Notifications deleted"}


async def replace_tags(event: Event.Read, notification: Notification.Read) -> str:
    wl = await partner_get_white_label(event.id_org)
    message = notification.message

    org_settings = await get_settings_org(event.id_org)

    # build web app URL
    settings = get_settings()
    base_map = {
        "local": "web",
        "dev": "web-dev",
        "qa": "web-qa",
        "staging": "web-staging",
        "production": "web",
    }

    pickup_url = (
        f"http://{base_map[settings.environment]}.koloni.io/ready-pickup/?id={event.id}"
    )
    status_url = (
        f"http://{base_map[settings.environment]}.koloni.io/active-transactions"
    )

    message = (
        message.replace("((order_id))", event.invoice_id if event.invoice_id else "")
        .replace(
            "((unit))",
            (
                event.device.price.unit.value
                if event.device and event.device.price
                else ""
            ),
        )
        .replace("((pickup_url))", pickup_url)
        .replace("((status_url))", status_url)
        .replace("((URL))", status_url)
        .replace(
            "((currency))",
            (
                event.device.price.currency.value.upper()
                if event.device and event.device.price
                else "USD"
            ),
        )
        .replace(
            "((weight))",
            str(event.weight) if event.weight else "0",
        )
        .replace("((user_name))", event.user.name if event.user else "")
        .replace(
            "((location_name))",
            (
                event.device.location.name
                if event.device and event.device.location
                else ""
            ),
        )
        .replace(
            "((location_address))",
            (
                event.device.location.address
                if event.device and event.device.location
                else ""
            ),
        )
        .replace(
            "((locker_number))", str(event.device.locker_number if event.device else "")
        )
        .replace("((charged_amount))", str(event.total))
        .replace("((amount))", str(event.total))
        .replace("((org_name))", wl.app_name if wl else "")
        .replace(
            "((selected_duration))",
            f"{org_settings.parcel_expiration} {org_settings.parcel_expiration_unit}",
        )
    )

    return message


async def format_email(event: Event.Read, notification: Notification.Read) -> str:
    wl = await partner_get_white_label(event.id_org)

    ROOT_DIR = Path(__file__).parent
    psub_file = ROOT_DIR / "notification_template.html"
    with open(psub_file) as f:
        contents = f.read()
        return (
            contents.replace("{{org_name}}", wl.app_name if wl else "")
            .replace(
                "{{org_logo}}",
                (
                    event.device.location.image
                    if event.device.location.image
                    else wl.app_logo
                ),
            )
            .replace("{{order_id}}", event.invoice_id)
            .replace("{{location_address}}", event.device.location.address)
            .replace("{{message}}", await replace_tags(event, notification))
        )


async def send_notification(event: Event, notification: Notification.Read):
    """Send a notification to the user."""
    print("SENDING NOTIFICATION")
    try:
        match notification.recipient_type:
            case RecipientType.user:
                if notification.sms and event.user.phone_number:
                    # Variable used to handle custom Twilio Messaging Service SIDs depending
                    # on the org given:
                    messaging_service_sid = await get_org_messaging_service_sid(
                        event.id_org
                    )

                    client = Client(
                        get_settings().twilio_sid, get_settings().twilio_secret
                    )
                    client.messages.create(
                        to=event.user.phone_number,
                        from_=messaging_service_sid,
                        body=await replace_tags(event, notification),
                    )  # raise TwilioRestException

                if notification.email and event.user.email:
                    email_sender = await get_org_sendgrid_auth_sender(event.id_org)

                    email.send(
                        email_sender,
                        event.user.email,
                        "notification",
                        await format_email(event, notification),
                        is_ups_org=await is_ups_org(event.id_org),
                    )
            case RecipientType.admin:
                settings = await get_settings_org(event.id_org)
                if notification.sms:
                    # Variable used to handle custom Twilio Messaging Service SIDs depending
                    # on the org given:
                    messaging_service_sid = await get_org_messaging_service_sid(
                        event.id_org
                    )

                    client = Client(
                        get_settings().twilio_sid, get_settings().twilio_secret
                    )
                    client.messages.create(
                        to=event.device.location.contact_phone
                        or settings.default_support_phone,
                        from_=messaging_service_sid,
                        body=await replace_tags(event, notification),
                    )  # raise TwilioRestException

                if notification.email:
                    email_sender = await get_org_sendgrid_auth_sender(event.id_org)

                    email.send(
                        email_sender,
                        event.device.location.contact_email
                        or settings.default_support_email,
                        "notification",
                        await format_email(event, notification),
                        is_ups_org=await is_ups_org(event.id_org),
                    )
    except Exception as e:
        print("EXCEPTION::", e)
        pass


async def create_notify_job_on_event(
    id_event: UUID,
    notify_type: NotificationType,
):
    """Find possible notifications for an event and schedule them."""
    query = select(Event).where(Event.id == id_event)
    response = await db.session.execute(query)

    event = response.unique().scalar_one_or_none()

    # early exit if there is no event
    if not event:
        print("No event")
        return

    query = select(Notification).where(
        Notification.notification_type == notify_type,
        Notification.mode == event.event_type,
        Notification.id_org == event.id_org,
    )
    data = await db.session.execute(query)

    notifications = data.unique().scalars().all()

    for notification in notifications:
        trigger_date = None

        id_locations = [location.id for location in notification.locations]
        if id_locations and event.device.id_location not in id_locations:
            continue

        match notification.time_unit:
            case TimeUnit.minute:
                trigger_date = datetime.utcnow() + timedelta(
                    minutes=float(notification.time_amount)
                )
            case TimeUnit.hour:
                trigger_date = datetime.utcnow() + timedelta(
                    hours=float(notification.time_amount)
                )
            case TimeUnit.day:
                trigger_date = datetime.utcnow() + timedelta(
                    days=float(notification.time_amount)
                )
            case TimeUnit.week:
                trigger_date = datetime.utcnow() + timedelta(
                    weeks=float(notification.time_amount)
                )
            case TimeUnit.immediately:
                await send_notification(event, notification)
                continue

        scheduler.add_job(
            func=send_notification,
            trigger="date",
            run_date=trigger_date,
            id=str(uuid4()),
            args=[event, notification],
            replace_existing=True,
        )

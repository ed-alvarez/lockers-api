from uuid import UUID

from fastapi_async_sqlalchemy import db
from sqlalchemy import insert, select
from .model import Log, LogType
from ..event.model import Event, EventStatus
from ..device.model import Device


async def add_to_logger(
    id_org: UUID,
    id_device: UUID,
    log_type: LogType,
    log_owner: str,
):
    query = select(Event).where(
        Event.id_device == id_device,
        Event.event_status.in_(
            [
                EventStatus.awaiting_payment_confirmation,
                EventStatus.awaiting_service_pickup,
                EventStatus.awaiting_service_dropoff,
                EventStatus.awaiting_user_pickup,
                EventStatus.in_progress,
            ]
        ),
    )

    response = await db.session.execute(query)
    event = response.unique().scalars().first()

    query = (
        insert(Log)
        .values(
            id_org=id_org,
            id_device=id_device,
            log_type=log_type,
            log_owner=log_owner,
            id_event=event.id if event else None,
        )
        .returning(Log)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def add_to_logger_dclock(
    dclock_terminal_no: str,
    dclock_box_no: str,
    log_type: LogType,
):
    async with db():
        query = select(Device).where(
            Device.dclock_terminal_no == dclock_terminal_no,
            Device.dclock_box_no == dclock_box_no,
        )

        response = await db.session.execute(query)

        device = response.unique().scalar_one_or_none()

        if not device:
            return

        await add_to_logger(device.id_org, device.id, log_type, "API")


async def add_to_logger_gantner(
    gantner_id: str,
    log_type: LogType,
):
    async with db():
        query = select(Device).where(
            Device.gantner_id == gantner_id,
        )

        response = await db.session.execute(query)

        devices = response.unique().scalars().all()

        if not devices:
            return

        for device in devices:
            await add_to_logger(device.id_org, device.id, log_type, "API")


async def get_device_logs(
    id_device: UUID,
    id_org: UUID,
):
    query = select(Log).where(Log.id_device == id_device, Log.id_org == id_org)

    response = await db.session.execute(query)

    data = response.unique().scalars().all()
    print(data)

    return data


async def get_event_logs(
    id_event: UUID,
    id_org: UUID,
):
    query = select(Log).where(Log.id_event == id_event, Log.id_org == id_org)

    response = await db.session.execute(query)

    return response.unique().scalars().all()

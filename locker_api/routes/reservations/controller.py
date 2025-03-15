from datetime import datetime
from math import ceil
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, insert, or_, select, update
from ..notifications.controller import create_notify_job_on_event
from ..notifications.model import NotificationType
from util.scheduler import scheduler

from ..device.controller import (
    reserve_device,
    unreserve_device,
    get_device_by_loc_and_size,
)
from ..device.model import Mode
from ..event.controller import (
    generate_invoice_id,
    mobile_complete_event,
)
from ..event.model import Event, EventStatus
from ..user.controller import get_user_by_key, create_or_update_user
from ..user.model import User
from ..location.model import Location
from ..size.controller import get_sizes
from .model import PaginatedReservation, Reservation, ReservationSettings
from ..settings.model import ResTimeUnit


def get_days_from_reservation(
    reservation: Reservation,
) -> list[int]:
    # * Get days from reservation
    days = []
    if reservation.monday:
        days.append(0)
    if reservation.tuesday:
        days.append(1)
    if reservation.wednesday:
        days.append(2)
    if reservation.thursday:
        days.append(3)
    if reservation.friday:
        days.append(4)
    if reservation.saturday:
        days.append(5)
    if reservation.sunday:
        days.append(6)

    return days


async def get_reservations(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    id_reservation: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
) -> PaginatedReservation | Reservation.Read:
    query = select(Reservation).where(Reservation.id_org == id_org)

    if id_reservation:
        # * Early return if id_reservation is provided
        query = query.where(Reservation.id == id_reservation)

        result = await db.session.execute(query)
        return result.unique().scalar_one()

    if key and value:
        # * Early return if key and value are provided
        if key not in Reservation.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )

        query = query.filter(cast(Reservation.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        return result.unique().scalar_one()

    if search:
        query = query.filter(
            or_(
                cast(Reservation.user.name, VARCHAR()).ilike(f"%{search}%"),
                cast(Reservation.user.phone_number, VARCHAR()).ilike(f"%{search}%"),
                cast(Reservation.user.email, VARCHAR()).ilike(f"%{search}%"),
                cast(Reservation.device.name, VARCHAR()).ilike(f"%{search}%"),
                cast(Reservation.device.locker_number, VARCHAR()).ilike(f"%{search}%"),
            )
        )

    query = (
        query.limit(size)
        .offset((page - 1) * size)
        .order_by(Reservation.created_at.desc())
    )
    count = select(Reservation).where(Reservation.id_org == id_org)

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    return PaginatedReservation(
        items=data.unique().scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def get_reservation_by_tracking_number(
    tracking_number: str, id_org: UUID
) -> Optional[Reservation.Read]:
    query = select(Reservation).where(
        Reservation.tracking_number == tracking_number,
        Reservation.id_org == id_org,
        Reservation.mode == Mode.delivery,
    )
    response = await db.session.execute(query)

    return response.unique().scalar_one_or_none()


async def get_reservation(id_reservation: UUID, id_org: UUID) -> Reservation.Read:
    query = select(Reservation).where(
        Reservation.id == id_reservation, Reservation.id_org == id_org
    )

    response = await db.session.execute(query)

    return response.unique().scalar_one()


async def create_reservation(
    reservation: Reservation.Write,
    id_org: UUID,
) -> Reservation.Read:
    # * At least one day must be selected
    if (
        not any(
            [
                reservation.monday,
                reservation.tuesday,
                reservation.wednesday,
                reservation.thursday,
                reservation.friday,
                reservation.saturday,
                reservation.sunday,
            ]
        )
        and reservation.mode != Mode.delivery
    ):
        # * Set all days to True, if none are selected
        # * This is to allow "custom ranges" to be created
        reservation.monday = True
        reservation.tuesday = True
        reservation.wednesday = True
        reservation.thursday = True
        reservation.friday = True
        reservation.saturday = True
        reservation.sunday = True

    if (
        not reservation.phone_number
        and not reservation.email
        and not reservation.id_user
    ):
        raise HTTPException(
            status_code=400,
            detail="either a phone number, email or id must be provided",
        )

    if reservation.tracking_number:
        await check_tracking_number_unique(reservation.tracking_number, id_org)

    device = None
    if not reservation.id_device:
        if reservation.id_location and reservation.id_size:
            device = await get_device_by_loc_and_size(
                reservation.id_location, reservation.id_size, reservation.mode, id_org
            )
            if not device:
                raise HTTPException(
                    status_code=400,
                    detail="failed to assign a locker to this reservation given the location and size",
                )

    user = None
    if not reservation.id_user:
        if reservation.phone_number:
            try:
                user = await get_user_by_key(
                    "phone_number", reservation.phone_number, id_org
                )
            except HTTPException:
                pass

        if not user and reservation.email:
            try:
                user = await get_user_by_key("email", reservation.email, id_org)
            except HTTPException:
                pass

        if not user:
            user, err = await create_or_update_user(
                User.Write(
                    name=reservation.user_name,
                    phone_number=reservation.phone_number,
                    email=reservation.email,
                ),
                id_org,
            )

    reservation.id_user = reservation.id_user or user.id
    reservation.id_device = reservation.id_device or device.id

    await reserve_device(reservation.id_device, id_org)

    query = (
        insert(Reservation)
        .values(
            **reservation.dict(exclude={"phone_number", "email", "user_name"}),
            id_org=id_org,
        )
        .returning(Reservation)
    )

    result = await db.session.execute(query)
    await db.session.commit()
    data = result.all().pop()

    # * Schedule start
    if reservation.mode != Mode.delivery:
        await schedule_start(reservation, False)

    return data


async def create_reservations_batch(reservation: Reservation.Batch, id_org: UUID):
    if not reservation.id_sizes:
        raise HTTPException(status_code=400, detail="At least 1 size is required")

    for size in reservation.id_sizes:
        res = Reservation.Write(
            recurring=reservation.recurring,
            monday=reservation.monday,
            tuesday=reservation.tuesday,
            wednesday=reservation.wednesday,
            thursday=reservation.thursday,
            friday=reservation.friday,
            saturday=reservation.saturday,
            sunday=reservation.sunday,
            from_time=reservation.from_time,
            to_time=reservation.to_time,
            id_location=reservation.id_location,
            id_user=reservation.id_user,
            end_date=reservation.end_date,
            id_size=size,
        )

        await create_reservation(res, id_org)

    return {"detail": "Reservations created"}


async def update_reservation(
    id_reservation: UUID,
    reservation: Reservation.Write,
    id_org: UUID,
) -> Reservation.Read:
    prev_reservation = await get_reservation(id_reservation, id_org)

    if (
        not any(
            [
                reservation.monday,
                reservation.tuesday,
                reservation.wednesday,
                reservation.thursday,
                reservation.friday,
                reservation.saturday,
                reservation.sunday,
            ]
        )
        and reservation.mode != Mode.delivery
    ):
        # * Set all days to True, if none are selected
        # * This is to allow "custom ranges" to be created
        reservation.monday = True
        reservation.tuesday = True
        reservation.wednesday = True
        reservation.thursday = True
        reservation.friday = True
        reservation.saturday = True
        reservation.sunday = True

    if reservation.tracking_number:
        await check_tracking_number_unique(
            reservation.tracking_number, id_org, id_reservation
        )

    if prev_reservation.id_device:
        await unreserve_device(prev_reservation.id_device, id_org)

    device = None
    if not reservation.id_device:
        if reservation.id_location and reservation.id_size:
            device = await get_device_by_loc_and_size(
                reservation.id_location, reservation.id_size, reservation.mode, id_org
            )
            if not device:
                raise HTTPException(
                    status_code=400,
                    detail="failed to assign a locker to this reservation given the location and size",
                )

    user = None
    if not reservation.id_user:
        if reservation.phone_number:
            try:
                user = await get_user_by_key(
                    "phone_number", reservation.phone_number, id_org
                )
            except HTTPException:
                pass

        if not user and reservation.email:
            try:
                user = await get_user_by_key("email", reservation.email, id_org)
            except HTTPException:
                pass

        if not user and reservation.phone_number and reservation.email:
            user = await create_or_update_user(
                User.Write(
                    name=reservation.user_name,
                    phone_number=reservation.phone_number,
                    email=reservation.email,
                ),
                id_org,
            )

    reservation.id_user = reservation.id_user or user.id if user else None
    reservation.id_device = reservation.id_device or device.id if device else None

    await reserve_device(reservation.id_device, id_org)

    query = (
        update(Reservation)
        .where(
            Reservation.id == id_reservation,
            Reservation.id_org == id_org,
        )
        .values(
            **reservation.dict(exclude={"phone_number", "email", "user_name"}),
        )
        .returning(Reservation)
    )

    result = await db.session.execute(query)
    await db.session.commit()

    try:
        reservation = result.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found",
        )

    # * Cancel previous schedule, schedule new one
    if reservation.mode != Mode.delivery:
        await cancel_schedule(id_reservation)
        await schedule_start(reservation, False)

    query = select(Reservation).where(Reservation.id == reservation.id)
    result = await db.session.execute(query)
    reservation = result.unique().scalar_one()

    return reservation


async def create_reservations_csv(id_org: UUID, reservation: Reservation.WriteCSV):
    try:
        if reservation.location:
            query = select(Location).where(
                Location.id_org == id_org, Location.name == reservation.location
            )
            res = await db.session.execute(query)
            location = res.scalar_one()

        if reservation.size:
            size = await get_sizes(
                id_org, None, None, key="name", value=reservation.size
            )

        user = None
        if reservation.phone_number:
            try:
                user = await get_user_by_key(
                    "phone_number", reservation.phone_number, id_org
                )
            except HTTPException:
                pass

        if not user and reservation.email:
            try:
                user = await get_user_by_key("email", reservation.email, id_org)
            except HTTPException:
                pass

        if not user and reservation.phone_number and reservation.email:
            user = await create_or_update_user(
                User.Write(
                    name="",
                    phone_number=reservation.phone_number,
                    email=reservation.email,
                ),
                id_org,
            )

        new_reservation: Reservation.Write = Reservation.Write.parse_obj(reservation)

        new_reservation.id_size = size.id if reservation.size else None
        new_reservation.id_location = location.id if reservation.location else None
        new_reservation.id_user = user.id

        await create_reservation(new_reservation, id_org)

        return True
    except HTTPException as e:
        return e.detail
    except Exception as e:
        raise e


async def update_reservations_csv(
    id_org: UUID, reservation: Reservation.Write, id_reservation: UUID
):
    try:
        await update_reservation(id_reservation, reservation, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def delete_reservation(
    id_reservation: UUID,
    id_org: UUID,
) -> Reservation.Read:
    query = (
        delete(Reservation)
        .where(
            Reservation.id == id_reservation,
            Reservation.id_org == id_org,
        )
        .returning(Reservation)
    )

    result = await db.session.execute(query)
    await db.session.commit()
    try:
        reservation = result.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found",
        )

    await cancel_schedule(reservation)
    return reservation


async def delete_reservations(
    id_reservations: List[UUID],
    id_org: UUID,
):
    query = (
        delete(Reservation)
        .where(
            Reservation.id.in_(id_reservations),
            Reservation.id_org == id_org,
        )
        .returning(Reservation)
    )

    result = await db.session.execute(query)
    await db.session.commit()

    reservations = result.all()

    for reservation in reservations:
        await cancel_schedule(reservation)

    return {"detail": "Reservations deleted"}


async def insert_reservation_transaction(reservation: Reservation):
    device = await reserve_device(reservation.id_device, reservation.id_org)

    invoice_id = await generate_invoice_id(reservation.id_org)
    query = (
        insert(Event)
        .values(
            invoice_id=invoice_id,
            id_org=reservation.id_org,
            id_user=reservation.id_user,
            id_device=device.id,
            event_type=device.mode.value,
            event_status=EventStatus.reserved,
            started_at=datetime.utcnow(),
            order_id=None,
            total=None,
            payment_intent_id=None,
        )
        .returning(Event)
    )

    result = await db.session.execute(query)
    await db.session.commit()

    event = result.all().pop()

    # * Schedule finalization
    await schedule_end(reservation, reservation.id_org, event.id)
    await create_notify_job_on_event(
        event.id, NotificationType.on_reservation, event.event_type
    )

    return event


async def schedule_start(reservation: Reservation, renew: bool = False):
    days = get_days_from_reservation(reservation)

    if not days:
        raise HTTPException(
            status_code=400,
            detail="At least one day must be selected",
        )

    for day in days:
        scheduler.add_job(
            insert_reservation_transaction,
            "cron",
            day_of_week=day,
            hour=reservation.from_time.split(":")[0],
            minute=reservation.from_time.split(":")[1],
            second=0,
            end_date=reservation.end_date,
            args=[reservation],
            id=str(reservation.id) + "_" + str(day),
            replace_existing=True,
        )

    return reservation


async def schedule_end(reservation: Reservation, id_org: UUID, id_event: UUID):
    end_time = reservation.to_time
    end_date = datetime.utcnow().replace(
        hour=int(end_time.split(":")[0]),
        minute=int(end_time.split(":")[1]),
    )

    # * Schedule End
    scheduler.add_job(
        mobile_complete_event,
        "date",
        run_date=end_date,
        args=[id_event, reservation.id_user, id_org, None, None],
        id=str(id_event),
        replace_existing=True,
    )

    # * Schedule Renewal
    await schedule_start(reservation, True)

    return reservation


async def cancel_schedule(reservation: Reservation):
    days = get_days_from_reservation(reservation)

    for day in days:
        try:
            scheduler.remove_job(str(reservation.id) + "_" + str(day))
        except Exception:
            pass


async def get_reservation_settings(id_org: UUID):
    query = select(ReservationSettings).where(ReservationSettings.id_org == id_org)

    response = await db.session.execute(query)
    data = response.scalar_one_or_none()

    if not data:
        res = await create_reservation_settings(
            id_org,
            ReservationSettings.Write(
                max_rental_time=30,
                max_rental_time_period=ResTimeUnit.hour,
                max_reservation_time=30,
                max_reservation_time_period=ResTimeUnit.day,
                transaction_buffer_time=30,
                locker_buffer_time=15,
            ),
        )

        return res

    return data


async def create_reservation_settings(
    id_org: UUID, reservation_settings: ReservationSettings.Write
):
    query = select(ReservationSettings).where(ReservationSettings.id_org == id_org)

    response = await db.session.execute(query)
    data = response.scalar_one_or_none()

    if data:
        raise HTTPException(
            status_code=400,
            detail=f"Reservation Settings for id_org '{id_org}' already exists",
        )

    query = (
        insert(ReservationSettings)
        .values(
            **reservation_settings.dict(),
            id_org=id_org,
        )
        .returning(ReservationSettings)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def update_reservation_settings(
    id_org: UUID, reservation_settings: ReservationSettings.Write
):
    query = (
        update(ReservationSettings)
        .where(ReservationSettings.id_org == id_org)
        .values(
            **reservation_settings.dict(),
            id_org=id_org,
        )
        .returning(ReservationSettings)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        return response.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Settings were not found for id_org '{id_org}'",
        )


async def check_tracking_number_unique(
    tracking_number: str, id_org: UUID, id_reservation: Optional[UUID] = None
):
    query = select(Reservation).where(
        Reservation.tracking_number == tracking_number, Reservation.id_org == id_org
    )

    if id_reservation:
        query = query.where(Reservation.id != id_reservation)

    res = await db.session.execute(query)

    data = res.unique().scalars().all()

    if data:
        raise HTTPException(
            status_code=409,
            detail="a reservation with this tracking number already exists",
        )

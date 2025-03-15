import re
from math import ceil
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import VARCHAR, cast, delete, insert, or_, select, update


from ..device.model import Device
from .model import Locker, LockerWall, PaginatedLockerWalls


async def get_locker_walls(
    page: int, size: int, search: str, id_org: UUID, id_location: Optional[UUID] = None
):
    query = select(LockerWall).where(LockerWall.id_org == id_org)

    if id_location:
        query = query.where(LockerWall.id_location == id_location)

    if search:
        query = query.where(
            or_(
                cast(LockerWall.name, VARCHAR).ilike(f"%{search}%"),
            )
        )

    count = query
    query = (
        query.limit(size)
        .offset((page - 1) * size)
        .order_by(LockerWall.created_at.desc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    return PaginatedLockerWalls(
        items=data.unique().scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_locker_wall(locker_wall: LockerWall.Write, id_org: UUID):
    locker_wall = LockerWall(
        **locker_wall.dict(),
        id_org=id_org,
    )

    await validate_custom_id(locker_wall.custom_id, id_org, None)

    devices = await validate_lockers(locker_wall.lockers, locker_wall.is_kiosk, id_org)

    query = insert(LockerWall).values(locker_wall.dict()).returning(LockerWall)

    response = await db.session.execute(query)
    locker_wall_created = response.all().pop()

    await assign_devices_to_locker_wall(devices, locker_wall_created.id, id_org)

    return locker_wall_created


async def update_locker_wall(
    id_locker_wall: UUID, locker_wall: LockerWall.Write, id_org: UUID
):
    locker_wall = LockerWall(
        **locker_wall.dict(),
        id_org=id_org,
    )

    await validate_custom_id(locker_wall.custom_id, id_org, id_locker_wall)

    devices = await validate_lockers(
        locker_wall.lockers, locker_wall.is_kiosk, id_org, id_locker_wall
    )

    await remove_devices_from_locker_wall(id_locker_wall, id_org)

    await assign_devices_to_locker_wall(devices, id_locker_wall, id_org)

    query = (
        update(LockerWall)
        .where(LockerWall.id == id_locker_wall, LockerWall.id_org == id_org)
        .values(**locker_wall.dict(exclude_unset=True))
        .returning(LockerWall)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        response.all().pop()

    except IndexError:
        error_detail = f"Locker wall with id {id_locker_wall} was not found"

        raise HTTPException(status_code=404, detail=error_detail)

    query = select(LockerWall).where(
        LockerWall.id == id_locker_wall, LockerWall.id_org == id_org
    )
    locker_wall = await db.session.execute(query)
    locker_wall = locker_wall.unique().scalar_one_or_none()

    return locker_wall


async def delete_locker_wall(id_locker_wall: UUID, id_org: UUID):
    query = (
        delete(LockerWall)
        .where(LockerWall.id == id_locker_wall, LockerWall.id_org == id_org)
        .returning(LockerWall)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        locker_wall = response.all().pop()

    except IndexError:
        error_detail = f"Locker wall with id '{id_locker_wall}' was not found"

        raise HTTPException(status_code=404, detail=error_detail)

    await remove_devices_from_locker_wall(id_locker_wall, id_org)

    return locker_wall


async def validate_lockers(
    lockers: List[Locker],
    is_kiosk: bool,
    id_org: UUID,
    id_locker_wall: Optional[UUID] = None,
) -> List[UUID]:
    # Every id must be a valid UUID
    # There can only be one kiosk, if enabled
    # All lockers must have a unique id
    # No coordinates can be duplicated

    uuids = [locker.id for locker in lockers if locker.id is not None]
    uuid_set = set(uuids)

    # * Check for duplicates
    if len(uuids) != len(uuid_set):
        raise HTTPException(
            status_code=400,
            detail="one or more Lockers are duplicated",
        )

    # * Check ids
    for locker in lockers:
        uuid_pattern = r"^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$"
        if locker.id:
            if not re.match(uuid_pattern, locker.id):
                raise HTTPException(
                    status_code=400,
                    detail="one or more UUIDs are invalid",
                )

    # * Check coordinates
    coordinates = [(locker.x, locker.y) for locker in lockers]
    if len(coordinates) != len(set(coordinates)):
        raise HTTPException(
            status_code=400,
            detail="one or more coordinates are duplicated",
        )

    # * Check kiosk
    if is_kiosk:
        if len([locker for locker in lockers if locker.kiosk]) != 1:
            raise HTTPException(
                status_code=400,
                detail="there must be exactly one kiosk",
            )

    # * Check if all ids belong to this organization
    query = select(Device.id).where(
        Device.id_org == id_org,
        Device.id.in_(uuids),
        or_(Device.id_locker_wall == id_locker_wall, Device.id_locker_wall == None),  # noqa: E711
    )
    devices = await db.session.execute(query)

    devices = devices.unique().scalars().all()

    if len(devices) != len(uuids):
        raise HTTPException(
            status_code=400,
            detail="one or more Devices are invalid or are assigned to another locker wall",
        )

    return uuids


async def validate_custom_id(
    custom_id: Optional[str], id_org: UUID, id_locker_wall: Optional[UUID]
):
    if not custom_id:
        return

    query = select(LockerWall).where(
        LockerWall.id_org == id_org,
        LockerWall.custom_id == custom_id,
        LockerWall.id != id_locker_wall,
    )
    locker_wall = await db.session.execute(query)
    locker_wall = locker_wall.unique().scalar_one_or_none()

    if locker_wall:
        raise HTTPException(
            status_code=400,
            detail="Custom ID is already in use",
        )


async def assign_devices_to_locker_wall(
    devices: List[UUID], id_locker_wall: UUID, id_org: UUID
):
    query = select(LockerWall).where(
        LockerWall.id == id_locker_wall, LockerWall.id_org == id_org
    )
    locker_wall = await db.session.execute(query)
    locker_wall = locker_wall.unique().scalar_one_or_none()

    if not locker_wall:
        raise HTTPException(
            status_code=404,
            detail="Locker wall not found",
        )

    query = (
        update(Device)
        .where(Device.id.in_(devices), Device.id_org == id_org)
        .values(id_locker_wall=id_locker_wall)
    )

    await db.session.execute(query)
    await db.session.commit()

    return True


async def remove_devices_from_locker_wall(id_locker_wall: UUID, id_org: UUID):
    query = (
        update(Device)
        .where(Device.id_locker_wall == id_locker_wall, Device.id_org == id_org)
        .values(id_locker_wall=None)
    )

    await db.session.execute(query)
    await db.session.commit()

    return True

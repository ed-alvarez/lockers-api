from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, or_, select, update


from ..device.model import Device
from .model import Condition, PaginatedConditions


async def get_conditions(
    page: conint(gt=0),
    size: conint(gt=0),
    id_condition: Optional[UUID],
    key: Optional[str],
    value: Optional[str],
    search: Optional[str],
    id_org: UUID,
) -> PaginatedConditions | Condition.Read:
    query = select(Condition).where(Condition.id_org == id_org)

    if id_condition:
        # * Early return if id_condition is provided
        query = query.where(Condition.id == id_condition)

        result = await db.session.execute(query)
        return result.unique().scalar_one()

    if key and value:
        # * Early return if key and value are provided
        if key not in Condition.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )

        query = query.filter(cast(Condition.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        return result.unique().scalar_one()

    if search:
        query = query.filter(
            or_(
                Condition.name.ilike(f"%{search}%"),
            )
        )

    count = query
    query = (
        query.limit(size)
        .offset((page - 1) * size)
        .order_by(Condition.created_at.desc())
    )

    data = await db.session.execute(query)
    counter = await db.session.execute(count)

    total_count = len(counter.unique().all())

    return PaginatedConditions(
        items=data.unique().scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_condition(
    condition: Condition.Write,
    id_org: UUID,
) -> Condition.Read:
    condition_obj = Condition(
        name=condition.name,
        auto_report=condition.auto_report,
        auto_maintenance=condition.auto_maintenance,
        id_org=id_org,
    )

    db.session.add(condition_obj)
    await db.session.commit()
    await db.session.refresh(condition_obj)

    if condition.devices:
        if len(condition.devices) > 0:
            query = (
                update(Device)
                .where(Device.id.in_(condition.devices), Device.id_org == id_org)
                .values(
                    {
                        "id_condition": condition_obj.id,
                    }
                )
            )
            await db.session.execute(query)
            await db.session.commit()

    return condition_obj


async def create_condition_csv(
    id_org: UUID,
    condition: Condition.Write,
):
    try:
        await create_condition(condition, id_org)
    except HTTPException as e:
        return e.detail
    return None


async def update_condition_csv(
    id_org: UUID,
    condition: Condition.Write,
    id_condition: UUID,
):
    try:
        await update_condition(id_condition, condition, id_org)
    except HTTPException as e:
        return e.detail
    return None


async def patch_condition(
    id_condition: UUID,
    condition: Condition.Patch,
    id_org: UUID,
) -> Condition.Read:
    query = (
        update(Condition)
        .where(Condition.id == id_condition, Condition.id_org == id_org)
        .values(**condition.dict(exclude_unset=True))
        .returning(Condition)
    )

    result = await db.session.execute(query)
    await db.session.commit()

    try:
        data = result.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Condition with id {id_condition} was not found",
        )

    if condition.devices is not None:
        query = (
            update(Device)
            .where(Device.id_condition == id_condition, Device.id_org == id_org)
            .values(
                {
                    "id_condition": None,
                }
            )
        )
        await db.session.execute(query)
        await db.session.commit()

        if len(condition.devices) > 0:
            query = (
                update(Device)
                .where(Device.id.in_(condition.devices), Device.id_org == id_org)
                .values(
                    {
                        "id_condition": id_condition,
                    }
                )
            )
            await db.session.execute(query)
            await db.session.commit()

    return data


async def patch_conditions(
    id_conditions: list[UUID],
    condition: Condition.Patch,
    id_org: UUID,
) -> dict[str, str]:
    for id_condition in id_conditions:
        await patch_condition(id_condition, condition, id_org)

    return {"detail": "Conditions updated"}


async def update_condition(
    id_condition: UUID,
    condition: Condition.Patch,
    id_org: UUID,
) -> Condition.Read:
    query = select(Condition).where(
        Condition.id == id_condition, Condition.id_org == id_org
    )
    result = await db.session.execute(query)
    condition_to_update = result.unique().scalar_one_or_none()

    if condition_to_update is None:
        raise HTTPException(
            status_code=404,
            detail=f"Condition with id {id_condition} was not found",
        )

    if condition.devices is not None:
        query = (
            update(Device)
            .where(Device.id_condition == id_condition, Device.id_org == id_org)
            .values(
                {
                    "id_condition": None,
                }
            )
        )
        await db.session.execute(query)
        await db.session.commit()

        if len(condition.devices) > 0:
            query = (
                update(Device)
                .where(Device.id.in_(condition.devices), Device.id_org == id_org)
                .values(
                    {
                        "id_condition": id_condition,
                    }
                )
            )
            await db.session.execute(query)
            await db.session.commit()

    # Update the condition excluding 'devices' field
    condition_data = condition.dict(exclude_unset=True)
    condition_data.pop("devices", None)  # Exclude 'devices' from update data

    query = (
        update(Condition)
        .where(Condition.id == id_condition, Condition.id_org == id_org)
        .values(**condition_data)
        .returning(Condition)
    )

    result = await db.session.execute(query)
    await db.session.commit()

    # Fetch the updated condition data
    query = select(Condition).where(Condition.id == id_condition)
    result = await db.session.execute(query)
    updated_condition = result.unique().scalar_one()

    # If no updated condition is found (which should not happen normally)
    if not updated_condition:
        raise HTTPException(
            status_code=500, detail="Error retrieving updated condition data."
        )

    # Fetch associated devices
    query = select(Device).where(Device.id_condition == id_condition)
    result = await db.session.execute(query)
    devices = result.unique().scalars().all()

    # Convert to Condition.Read format
    condition_read = Condition.Read(
        id=updated_condition.id,
        created_at=updated_condition.created_at,
        name=updated_condition.name,
        auto_report=updated_condition.auto_report,
        auto_maintenance=updated_condition.auto_maintenance,
        devices=[
            Device.Read(**device.dict()) for device in devices
        ],  # Convert each device to Device.Read
    )

    return condition_read


async def delete_condition(
    id_condition: UUID,
    id_org: UUID,
) -> Condition.Read:
    query = select(Condition).where(Condition.id == id_condition)
    result = await db.session.execute(query)
    condition_to_delete = result.unique().scalar_one_or_none()

    if condition_to_delete is None:
        raise HTTPException(
            status_code=404,
            detail=f"Condition with id {id_condition} was not found",
        )

    # * Remove condition from devices
    query = (
        update(Device)
        .where(Device.id_condition == id_condition, Device.id_org == id_org)
        .values(
            {
                "id_condition": None,
            }
        )
    )
    await db.session.execute(query)
    await db.session.commit()

    # * Delete condition
    delete_query = (
        delete(Condition)
        .where(Condition.id == id_condition)
        .where(Condition.id_org == id_org)
    )

    await db.session.execute(delete_query)
    await db.session.commit()

    return condition_to_delete


async def delete_conditions(
    id_conditions: list[UUID],
    id_org: UUID,
) -> dict[str, str]:
    query = delete(Condition).where(
        Condition.id.in_(id_conditions), Condition.id_org == id_org
    )
    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Conditions deleted"}

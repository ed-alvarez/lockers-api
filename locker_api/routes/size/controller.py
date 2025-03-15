from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError
from util.exception import format_error


from .model import PaginatedSizes, Size


async def get_size_id_by_external_id(
    external_id: str,
    id_org: UUID,
) -> UUID | None:
    query = select(Size.id).where(
        Size.id_org == id_org, Size.external_id == external_id
    )

    result = await db.session.execute(query)

    size_id = result.scalar_one_or_none()

    return size_id


async def get_sizes(
    id_org: UUID,
    page: conint(gt=0),
    size: conint(gt=0),
    id_size: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
) -> PaginatedSizes | Size.Read:
    query = select(Size).where(Size.id_org == id_org)

    if id_size:
        # * Early return if id_size is provided

        query = query.where(Size.id == id_size)

        result = await db.session.execute(query)

        return result.scalar_one()

    if key and value:
        # * Early return if key and value are provided

        if key not in Size.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )

        query = query.filter(cast(Size.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)

        return result.scalar_one()

    if search:
        query = query.filter(
            or_(
                Size.name.ilike(f"%{search}%"),
            )
        )

    count = query
    query = query.limit(size).offset((page - 1) * size).order_by(Size.created_at.desc())

    data = await db.session.execute(query)
    counter = await db.session.execute(count)

    total_count = len(counter.all())

    return PaginatedSizes(
        items=data.scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_size(size: Size.Write, id_org: UUID) -> Size.Read:
    await check_size_unique(size, id_org)
    new_size = Size(**size.dict(), id_org=id_org)

    query = insert(Size).values(new_size.dict()).returning(Size)

    try:
        response = await db.session.execute(query)
        await db.session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Failed to create a size, {format_error(e)}",
        )

    result = response.fetchone()

    return Size.Read.from_orm(result)


async def update_size(id_size: UUID, size: Size.Write, id_org: UUID) -> Size.Read:
    await check_size_unique(size, id_org, id_size)

    # Fetch the object before updating
    fetch_query = select(Size).where(Size.id == id_size).where(Size.id_org == id_org)

    result = await db.session.execute(fetch_query)
    size_to_update = result.scalar_one_or_none()

    if size_to_update is None:
        raise HTTPException(
            status_code=404,
            detail=f"Size with id {id_size} was not found",
        )

    # Update the fields of the fetched object
    for key, value in size.dict(exclude_unset=True).items():
        setattr(size_to_update, key, value)

    try:
        await db.session.commit()
    except IntegrityError as e:
        await db.session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Failed to update size, {format_error(e)}",
        )

    return size_to_update


async def patch_size(id_size: UUID, size: Size.Patch, id_org: UUID) -> Size.Read:
    # Fetch the object before updating

    if size.name:
        await check_size_unique(size, id_org, id_size)

    query = (
        update(Size)
        .where(Size.id == id_size, Size.id_org == id_org)
        .values(size.dict(exclude_unset=True))
        .returning(Size)
    )

    result = await db.session.execute(query)
    await db.session.commit()

    try:
        return result.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Size with id {id_size} was not found",
        )


async def patch_sizes(id_sizes: list[UUID], size: Size.Patch, id_org: UUID):
    for id_size in id_sizes:
        await patch_size(id_size, size, id_org)

    return {"detail": "Sizes updated"}


async def create_size_csv(id_org: UUID, size: Size.Write):
    try:
        await create_size(size, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def update_size_csv(id_org: UUID, size: Size.Write, id_size: UUID):
    try:
        await patch_size(id_size, size, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def delete_size(id_size: UUID, id_org: UUID) -> Size.Read:
    # Fetch the object before deleting

    query = select(Size).where(Size.id == id_size)

    result = await db.session.execute(query)
    size_to_delete = result.scalar_one_or_none()

    if size_to_delete is None:
        raise HTTPException(
            status_code=404,
            detail=f"Size with id {id_size} was not found",
        )

    delete_query = delete(Size).where(Size.id == id_size).where(Size.id_org == id_org)

    await db.session.execute(delete_query)
    await db.session.commit()

    return size_to_delete


async def delete_sizes(id_sizes: list[UUID], id_org: UUID):
    query = delete(Size).where(Size.id.in_(id_sizes)).where(Size.id_org == id_org)

    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Sizes deleted"}


async def check_size_unique(
    size: Size.Write, id_org: UUID, id_size: Optional[UUID] = None
):
    query = select(Size).where(Size.id_org == id_org, Size.name == size.name)

    if size.external_id:
        query = select(Size).where(
            Size.id_org == id_org,
            or_(Size.name == size.name, Size.external_id == size.external_id),
        )

    if id_size:
        query = query.where(Size.id != id_size)

    response = await db.session.execute(query)

    data = response.scalars().all()

    if len(data) > 0:
        msg = f"Name '{size.name}' is already in use. Please use a different name"
        if size.external_id:
            msg = f"Name '{size.name}' or external ID '{size.external_id}' is already in use. Please use a different name or external ID"

        raise HTTPException(status_code=409, detail=msg)

from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError
from util.exception import format_error


from .model import DiscountType, PaginatedPromos, Promo


async def get_promo_by_code(
    promo_code: str, id_org: UUID, id_user: UUID
) -> Optional[Promo.Read]:
    query = select(Promo).where(Promo.id_org == id_org, Promo.code == promo_code)
    result = await db.session.execute(query)
    promo = result.scalar_one_or_none()

    return promo


async def get_promos(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    id_promo: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_type: Optional[DiscountType] = None,
    search: Optional[str] = None,
) -> PaginatedPromos | Promo.Read:
    query = select(Promo).where(Promo.id_org == id_org)

    if id_promo:
        # * Early return if id_promo is provided

        query = query.where(Promo.id == id_promo)

        result = await db.session.execute(query)
        return result.scalar_one()

    if key and value:
        # * Early return if key and value are provided
        if key not in Promo.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )

        query = query.filter(cast(Promo.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        return result.scalar_one()

    if search:
        query = query.filter(
            or_(
                cast(Promo.amount, VARCHAR()).ilike(f"%{search}%"),
                cast(Promo.code, VARCHAR()).ilike(f"%{search}%"),
                cast(Promo.name, VARCHAR()).ilike(f"%{search}%"),
                cast(Promo.discount_type, VARCHAR()).ilike(f"%{search}%"),
            )
        )

    if by_type:
        query = query.where(Promo.discount_type == by_type)

    query = (
        query.limit(size).offset((page - 1) * size).order_by(Promo.created_at.desc())
    )
    count = select(Promo.id).where(
        Promo.id_org == id_org
    )  # Count the total number of promos, without the limit and offset

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.all())

    return PaginatedPromos(
        items=data.scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_promo(promo: Promo.Write, id_org: UUID):
    await check_unique_promo(promo, id_org)

    new_promo = Promo(**promo.dict(), id_org=id_org)

    query = insert(Promo).values(new_promo.dict()).returning(Promo)

    try:
        response = await db.session.execute(query)
        await db.session.commit()

    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Failed to create promo, {format_error(e)}",
        )

    return response.all().pop()


async def update_promo(id_promo: UUID, promo: Promo.Write, id_org: UUID):
    await check_unique_promo(promo, id_org, id_promo)

    query = (
        update(Promo)
        .where(Promo.id == id_promo)
        .where(Promo.id_org == id_org)
        .values(**promo.dict())
        .returning(Promo)
    )

    try:
        response = await db.session.execute(query)
        await db.session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Failed to update promo, {format_error(e)}",
        )

    try:
        updated_promo = response.all().pop()

        return updated_promo
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Promo with id {id_promo} was not found",
        )


async def patch_promo(id_promo: UUID, promo: Promo.Patch, id_org: UUID):
    if promo.code or promo.name:
        await check_unique_promo(promo, id_org, id_promo)

    query = (
        update(Promo)
        .where(Promo.id == id_promo, Promo.id_org == id_org)
        .values(**promo.dict(exclude_unset=True))
        .returning(Promo)
    )

    result = await db.session.execute(query)
    await db.session.commit()

    try:
        patched_promo = result.all().pop()

        return patched_promo
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Promo with id {id_promo} was not found",
        )


async def patch_promos(id_promos: list[UUID], promo: Promo.Patch, id_org: UUID):
    for id_promo in id_promos:
        await patch_promo(id_promo, promo, id_org)

    return {"detail": "Promos updated"}


async def create_promo_csv(id_org: UUID, promo: Promo.Write):
    try:
        await create_promo(promo, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def update_promo_csv(id_org: UUID, promo: Promo.Write, id_promo: UUID):
    try:
        await patch_promo(id_promo, promo, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def delete_promo(id_promo: UUID, id_org: UUID):
    query = (
        delete(Promo)
        .where(Promo.id == id_promo)
        .where(Promo.id_org == id_org)
        .returning(Promo)
    )

    try:
        response = await db.session.execute(query)
        await db.session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Failed to delete promo, {format_error(e)}",
        )

    try:
        deleted_promo = response.all().pop()

        return deleted_promo
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Promo with id {id_promo} was not found",
        )


async def delete_promos(id_promos: list[UUID], id_org: UUID):
    query = (
        delete(Promo)
        .where(Promo.id.in_(id_promos))
        .where(Promo.id_org == id_org)
        .returning(Promo)
    )

    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Promos deleted"}


async def check_unique_promo(
    promo: Promo.Write,
    id_org: UUID,
    id_promo: Optional[UUID] = None,
):
    query = select(Promo).where(
        Promo.id_org == id_org,
        or_(
            Promo.code == promo.code if promo.code else False,
            Promo.name == promo.name if promo.name else False,
        ),
    )

    if id_promo:
        query = query.where(Promo.id != id_promo)

    response = await db.session.execute(query)

    data = response.scalar_one_or_none()

    if data:
        raise HTTPException(
            status_code=409,
            detail=f"Promo with '{promo.code}' or '{promo.name}' already exists",
        )

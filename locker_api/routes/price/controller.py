from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, insert, or_, select, update


from .model import Currency, PaginatedPrices, Price, PriceType, Unit


async def get_prices(
    id_org: UUID,
    page: conint(ge=0),
    size: conint(ge=0),
    id_price: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    by_unit: Optional[Unit] = None,
    by_price_type: Optional[PriceType] = None,
    by_currency: Optional[Currency] = None,
) -> PaginatedPrices | Price.Read:
    query = select(Price).where(Price.id_org == id_org)

    if id_price:
        # * Early return if id_price is provided

        query = query.where(Price.id == id_price)

        result = await db.session.execute(query)
        return result.scalar_one()

    if key and value:
        # * Early return if key and value are provided
        if key not in Price.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )

        query = query.filter(cast(Price.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        return result.scalar_one()

    if search:
        query = query.filter(
            or_(
                Price.name.ilike(f"%{search}%"),
                cast(Price.amount, VARCHAR).ilike(f"%{search}%"),
            )
        )

    if by_unit:
        query = query.where(Price.unit == by_unit)

    if by_price_type:
        query = query.where(Price.price_type == by_price_type)

    if by_currency:
        query = query.where(Price.currency == by_currency)

    count = query  # This is used to count the total number of items
    page = query.limit(size).offset((page - 1) * size).order_by(Price.created_at.desc())

    response = await db.session.execute(page)
    counter = await db.session.execute(count)

    total = counter.scalars().all()

    total_count = len(total)

    return PaginatedPrices(
        items=response.scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_price(price: Price.Write, id_org: UUID):
    await check_unique_price(price, id_org)
    await validate_price(price)

    if price.amount > 0 and price.card_on_file is False:
        raise HTTPException(
            status_code=400,
            detail="Cannot create a positive price without a card on file",
        )

    new_price = Price(**price.dict(), id_org=id_org)

    query = insert(Price).values(new_price.dict()).returning(Price)

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def update_price(id_price: UUID, price: Price.Write, id_org: UUID):
    await check_unique_price(price, id_org, id_price)
    await validate_price(price)

    if price.amount > 0 and price.card_on_file is False:
        raise HTTPException(
            status_code=400,
            detail="Cannot create a positive price without a card on file",
        )

    query = (
        update(Price)
        .where(Price.id == id_price)
        .where(Price.id_org == id_org)
        .values(**price.dict())
        .returning(Price)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        updated_price = response.all().pop()

        return updated_price
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Price with id {id_price} was not found",
        )


async def patch_price(id_price: UUID, price: Price.Patch, id_org: UUID):
    if price.name or price.default:
        await check_unique_price(price, id_org, id_price)

    query = (
        update(Price)
        .where(Price.id == id_price, Price.id_org == id_org)
        .values(price.dict(exclude_unset=True))
        .returning(Price)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        updated_price = response.all().pop()

        return updated_price
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Price with id {id_price} was not found",
        )


async def patch_prices(id_prices: list[UUID], price: Price.Patch, id_org: UUID):
    for id_price in id_prices:
        await patch_price(id_price, price, id_org)

    return {"detail": "Prices updated"}


async def delete_price(id_price: UUID, id_org: UUID):
    query = (
        delete(Price)
        .where(Price.id == id_price)
        .where(Price.id_org == id_org)
        .returning(Price)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        deleted_price = response.all().pop()

        return deleted_price
    except IndexError:
        raise HTTPException(
            status_code=404, detail=f"Price with id {id_price} was not found"
        )


async def create_price_csv(id_org: UUID, price: Price.Write):
    try:
        await create_price(price, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def update_price_csv(id_org: UUID, price: Price.Write, id_price: UUID):
    try:
        await patch_price(id_price, price, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def delete_prices(id_prices: list[UUID], id_org: UUID):
    query = (
        delete(Price)
        .where(Price.id.in_(id_prices))
        .where(Price.id_org == id_org)
        .returning(Price)
    )

    response = await db.session.execute(query)
    deleted_prices = response.all()

    await db.session.commit()

    if not deleted_prices:
        raise HTTPException(status_code=404, detail="Prices not found")

    return {"detail": "Prices deleted"}


async def validate_price(price: Price.Write):
    match price.dict():
        case {
            "unit": Unit.minute | Unit.hour | Unit.day | Unit.week,
            "price_type": PriceType.pay_per_time,
        }:
            pass
        case {
            "unit": Unit.lb | Unit.kg,
            "price_type": PriceType.pay_per_weight,
        }:
            pass
        case _:
            raise HTTPException(status_code=400, detail="Invalid price")


async def check_unique_price(
    price: Price.Write, id_org: UUID, id_price: Optional[UUID] = None
):
    query = select(Price).where(Price.id_org == id_org, Price.name == price.name)

    if id_price:
        query = query.where(Price.id != id_price)

    response = await db.session.execute(query)
    data = response.scalars().all()

    if len(data) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Price with name '{price.name}' already exists",
        )

    if price.default is True:
        query = select(Price).where(Price.id_org == id_org, Price.default == True)  # noqa: E712

    if id_price:
        query = query.where(Price.id != id_price)

    response = await db.session.execute(query)
    data = response.scalars().all()

    if len(data) > 0:
        raise HTTPException(
            status_code=409,
            detail="There is already a default price",
        )

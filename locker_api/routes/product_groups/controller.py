from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import delete, insert, select, update


from ..products.model import Product
from .model import PaginatedProductGroups, ProductGroup


async def get_product_group(id_product_group: UUID, id_org: UUID):
    query = select(ProductGroup).where(
        ProductGroup.id == id_product_group, ProductGroup.id_org == id_org
    )

    data = await db.session.execute(query)
    product_group = data.unique().scalar_one()

    return product_group


async def get_product_groups(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    search: Optional[str] = None,
):
    query = select(ProductGroup).where(ProductGroup.id_org == id_org)

    if search:
        query = query.filter(ProductGroup.name.ilike(f"%{search}%"))

    count = query

    query = (
        query.limit(size)
        .offset((page - 1) * size)
        .order_by(ProductGroup.created_at.desc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    return PaginatedProductGroups(
        items=data.unique().scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_product_group(
    product_group: ProductGroup.Write,
    id_org: UUID,
):
    new_product_group = ProductGroup(
        name=product_group.name,
        id_org=id_org,
        auto_repair=product_group.auto_repair,
        transaction_number=product_group.transaction_number,
        charging_time=product_group.charging_time,
        one_to_one=product_group.one_to_one,
        id_size=product_group.id_size,
        total_inventory=product_group.total_inventory,
    )

    query = (
        insert(ProductGroup).values(new_product_group.dict()).returning(ProductGroup)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    data = response.all().pop()

    if product_group.products:
        query = (
            update(Product)
            .where(Product.id_org == id_org, Product.id.in_(product_group.products))
            .values(id_product_group=data.id)
        )
        await db.session.execute(query)
        await db.session.commit()

    return data


async def update_product_group(
    id_product_group: UUID,
    product_group: ProductGroup.Write,
    id_org: UUID,
):
    query = (
        update(ProductGroup)
        .where(ProductGroup.id == id_product_group, ProductGroup.id_org == id_org)
        .values(
            name=product_group.name,
            auto_repair=product_group.auto_repair,
            transaction_number=product_group.transaction_number,
            charging_time=product_group.charging_time,
            one_to_one=product_group.one_to_one,
            id_size=product_group.id_size,
        )
        .returning(ProductGroup)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    if product_group.products is not None:
        query = (
            update(Product)
            .where(
                Product.id_product_group == id_product_group, Product.id_org == id_org
            )
            .values(id_product_group=None)
        )
        await db.session.execute(query)
        await db.session.commit()

        query = (
            update(Product)
            .where(Product.id_org == id_org, Product.id.in_(product_group.products))
            .values(id_product_group=id_product_group)
        )
        await db.session.execute(query)
        await db.session.commit()

    try:
        updated_product_group = response.all().pop()

        return updated_product_group
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Product Group with id {id_product_group} was not found",
        )


async def patch_product_group(
    id_product_group: UUID, product_group: ProductGroup.Patch, id_org: UUID
):
    query = (
        update(ProductGroup)
        .where(ProductGroup.id == id_product_group, ProductGroup.id_org == id_org)
        .values(**product_group.dict(exclude_unset=True))
        .returning(ProductGroup)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        patched_product_group = response.all().pop()

        return patched_product_group
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Product Group with id {id_product_group} was not found",
        )


async def patch_product_groups(
    id_product_groups: list[UUID], product_group: ProductGroup.Patch, id_org: UUID
):
    for id_product_group in id_product_groups:
        await patch_product_group(id_product_group, product_group, id_org)

    return {"detail": "Product Groups updated"}


async def delete_product_group(id_product_group: UUID, id_org: UUID):
    query = delete(ProductGroup).where(
        ProductGroup.id == id_product_group, ProductGroup.id_org == id_org
    )
    response = await db.session.execute(query)
    await db.session.commit()

    try:
        deleted_product_group = response.all().pop()

        return deleted_product_group
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Product Group with id {id_product_group} was not found",
        )


async def delete_product_groups(id_product_groups: list[UUID], id_org: UUID):
    query = delete(ProductGroup).where(
        ProductGroup.id_org == id_org, ProductGroup.id.in_(id_product_groups)
    )
    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Product Groups deleted"}

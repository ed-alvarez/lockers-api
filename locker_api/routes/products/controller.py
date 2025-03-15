from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, insert, or_, select, update
from sqlalchemy.orm import joinedload
from util.images import ImagesService


from ..device.model import Device, Mode, Status
from ..product_tracking.product_tracking import ProductTracking, State
from .model import PaginatedProducts, Product


async def get_product(id_product: UUID, id_org: UUID):
    query = select(Product).where(Product.id == id_product, Product.id_org == id_org)

    data = await db.session.execute(query)
    product = data.unique().scalar_one()

    return product


async def get_products(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    id_product: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_group: Optional[UUID] = None,
    by_device: Optional[UUID] = None,
    by_location: Optional[UUID] = None,
    search: Optional[str] = None,
    with_tracking: Optional[bool] = True,
):
    query = select(Product).where(Product.id_org == id_org)

    if id_product:
        # * Early return if id_size is provided
        query = query.where(Product.id == id_product)

        result = await db.session.execute(query)
        data = result.unique().scalar_one()

        res = Product.Read.parse_obj(data)
        if res.devices:
            res.devices.sort(
                key=lambda x: x.mode == Mode.rental and x.status == Status.reserved,
                reverse=True,
            )
        return res

    if key and value:
        # * Early return if key and value are provided
        if key not in Product.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )

        query = query.filter(cast(Product.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)

        return result.unique().scalar_one()

    if by_group:
        query = query.where(Product.id_group == by_group)

    if by_device:
        query = query.outerjoin_from(
            Product, Device, Device.id_product == Product.id
        ).where(Device.id == by_device)

    if by_location:
        query = query.outerjoin_from(
            Product, Device, Device.id_product == Product.id
        ).where(Device.id_location == by_location)

    if with_tracking:
        query = query.options(joinedload(Product.product_tracking))

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%"),
                cast(Product.price, VARCHAR).ilike(f"%{search}%"),
                cast(Product.sales_price, VARCHAR).ilike(f"%{search}%"),
                Product.msrp.ilike(f"%{search}%"),
                Product.serial_number.ilike(f"%{search}%"),
            )
        )

    count = query

    query = (
        query.limit(size).offset((page - 1) * size).order_by(Product.created_at.desc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    return PaginatedProducts(
        items=data.unique().scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def track_product(
    id_product: UUID,
    state: State,
    id_org: UUID,
    id_user: Optional[UUID] = None,
    id_device: Optional[UUID] = None,
    id_condition: Optional[UUID] = None,
):
    query = (
        insert(ProductTracking)
        .values(
            id_product=id_product,
            state=state,
            id_org=id_org,
            id_user=id_user,
            id_device=id_device,
            id_condition=id_condition,
        )
        .returning(ProductTracking)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def create_product(
    image: Optional[UploadFile],
    product: Product.Write,
    id_org: UUID,
    images_service: ImagesService,
):
    await check_unique_product(product=product, id_org=id_org)
    if image:
        try:
            image_url = (
                await images_service.upload(id_org, image)
                if image
                else print("No image")
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to upload image, {e}",
            )

    new_product = Product(
        **product.dict(), image=image_url["url"] if image else None, id_org=id_org
    )

    query = insert(Product).values(new_product.dict()).returning(Product)
    response = await db.session.execute(query)

    await db.session.commit()

    data = response.all().pop()

    await track_product(
        id_product=data.id,
        state=State.new,
        id_org=id_org,
        id_user=None,
        id_device=None,
        id_condition=None,
    )

    return data


async def duplicate_product(id_product: UUID, id_org: UUID):
    query = select(Product).where(Product.id == id_product, Product.id_org == id_org)

    data = await db.session.execute(query)
    product = data.unique().scalar_one()

    new_product = Product(
        id_org=id_org,
        image=product.image,
        name=product.name,
        description=product.description,
        price=None,
        sales_price=None,
        sku=None,
        msrp=None,
        serial_number=None,
    )

    query = insert(Product).values(new_product.dict()).returning(Product)
    response = await db.session.execute(query)

    await db.session.commit()

    data = response.all().pop()

    await track_product(
        id_product=data.id,
        state=State.new,
        id_org=id_org,
        id_user=None,
        id_device=None,
        id_condition=None,
    )

    return data


async def update_product(
    id_product: UUID,
    image: Optional[UploadFile],
    product: Product.Write,
    id_org: UUID,
    images_service: ImagesService,
):
    await check_unique_product(product=product, id_org=id_org, id_product=id_product)
    if image:
        try:
            image_url = (
                await images_service.upload(id_org, image)
                if image
                else print("No image")
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to upload image, {e}",
            )

    query = (
        update(Product)
        .where(Product.id == id_product)
        .values(
            **product.dict(exclude_unset=True),
            image=image_url["url"] if image else Product.image,
        )
        .returning(Product)
    )
    response = await db.session.execute(query)
    await db.session.commit()

    try:
        updated_product = response.all().pop()
        return updated_product
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id {id_product} was not found",
        )


async def patch_product(id_product: UUID, product: Product.Patch, id_org: UUID):
    await check_unique_product(product=product, id_org=id_org, id_product=id_product)
    query = (
        update(Product)
        .where(Product.id == id_product, Product.id_org == id_org)
        .values(**product.dict(exclude_unset=True))
        .returning(Product)
    )
    response = await db.session.execute(query)
    await db.session.commit()

    try:
        patched_product = response.all().pop()
        return patched_product
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id {id_product} was not found",
        )


async def patch_products(id_products: list[UUID], product: Product.Patch, id_org: UUID):
    for id_product in id_products:
        await patch_product(id_product, product, id_org)

    return {"detail": "Products updated"}


async def create_product_csv(id_org: UUID, product: Product.Write):
    try:
        await create_product(None, product, id_org, ImagesService)
        return True
    except HTTPException as e:
        return e.detail


async def update_product_csv(id_org: UUID, product: Product.Write, id_product: UUID):
    try:
        await update_product(id_product, None, product, id_org, ImagesService)
        return True
    except HTTPException as e:
        return e.detail


async def delete_product(id_product: UUID, id_org: UUID):
    query = (
        delete(Product)
        .where(Product.id == id_product, Product.id_org == id_org)
        .returning(Product)
    )
    response = await db.session.execute(query)
    await db.session.commit()

    try:
        deleted_product = response.all().pop()
        return deleted_product
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id {id_product} was not found",
        )


async def delete_products(id_products: list[UUID], id_org: UUID):
    query = delete(Product).where(Product.id_org == id_org, Product.id.in_(id_products))
    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Products deleted"}


async def check_unique_product(
    product: Product.Write, id_org: UUID, id_product: Optional[UUID] = None
):
    if not product.serial_number:
        return

    query = select(Product).where(
        Product.id_org == id_org, Product.serial_number == product.serial_number
    )

    if id_product:
        query = query.where(Product.id != id_product)

    response = await db.session.execute(query)

    data = response.unique().scalars().all()

    if len(data) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Product with serial number '{product.serial_number}' already exists",
        )

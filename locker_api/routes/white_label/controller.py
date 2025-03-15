from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from fastapi_async_sqlalchemy import db
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from util.images import ImagesService
from ..organization.controller import add_user

from .model import WhiteLabel


async def partner_get_white_label(id_org: UUID):
    query = select(WhiteLabel).where(WhiteLabel.id_org == id_org)
    data = await db.session.execute(query)
    white_label = data.scalar_one_or_none()
    return white_label


async def partner_update_white_label_logo(
    image: UploadFile, id_org: UUID, images_service: ImagesService
):
    query = select(WhiteLabel).where(WhiteLabel.id_org == id_org)

    data = await db.session.execute(query)
    data.scalar_one()  # raises NoResultFound if not found

    try:
        image_url = await images_service.upload(id_org, image)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to upload image, {e}",
        )

    query = (
        update(WhiteLabel)
        .where(WhiteLabel.id_org == id_org)
        .values(app_logo=image_url["url"])
        .returning(WhiteLabel)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def partner_patch_white_label(white_label: WhiteLabel.Patch, id_org: UUID):
    query = select(WhiteLabel).where(WhiteLabel.id_org == id_org)

    data = await db.session.execute(query)
    data.scalar_one()  # raises NoResultFound if not found

    query = (
        update(WhiteLabel)
        .where(WhiteLabel.id_org == id_org)
        .values(**white_label.dict(exclude_unset=True))
        .returning(WhiteLabel)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def partner_update_white_label(
    image: Optional[UploadFile],
    white_label: WhiteLabel.Write,
    id_org: UUID,
    user_pool: str,
    images_service: ImagesService,
):
    query = select(WhiteLabel).where(WhiteLabel.id_org == id_org)

    data = await db.session.execute(query)
    select_data = data.scalar_one()  # raises NoResultFound if not found
    prev_owner = (
        select_data.organization_owner
    )  # setting temp variable here due to weird behaviour

    try:
        image_url = (
            await images_service.upload(id_org, image) if image else print("No image")
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to upload image, {e}",
        )

    update_query = (
        update(WhiteLabel)
        .where(WhiteLabel.id_org == id_org)
        .values(
            **white_label.dict(),
            # Default if no image is provided
            app_logo=image_url["url"] if image else select_data.app_logo,
        )
        .returning(WhiteLabel)
    )

    response = await db.session.execute(update_query)
    await db.session.commit()

    data = response.all().pop()

    if white_label.organization_owner and white_label.organization_owner != prev_owner:
        # Owner updated, invite to user_pool (fire and forget)
        try:
            await add_user(user_pool, white_label.organization_owner)
        except Exception:
            ...

    return data


async def partner_create_white_label(
    image: Optional[UploadFile],
    white_label: WhiteLabel.Write,
    id_org: UUID,
    images_service: ImagesService,
):
    query = select(WhiteLabel).where(WhiteLabel.id_org == id_org)

    data = await db.session.execute(query)

    select_data = data.scalar_one_or_none()

    if select_data:
        raise HTTPException(
            status_code=409,
            detail=f"White Label for id_org {id_org} already exists",
        )

    try:
        image_url = (
            await images_service.upload(id_org, image) if image else print("No image")
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to upload image, {e}",
        )

    default_logo = "https://assets.website-files.com/61f7e37730d06c4a05d2c4f3/62c640ed55a520a3d21d9b61_koloni-logo-black%207-p-500.png"

    insert_query = (
        insert(WhiteLabel)
        .values(
            **white_label.dict(),
            app_logo=image_url["url"] if image else default_logo,
            id_org=id_org,
        )
        .returning(WhiteLabel)
    )

    try:
        response = await db.session.execute(insert_query)
        await db.session.commit()

    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail=f"Failed to create White Label: {e}"
        )

    return response.all().pop()


async def mobile_get_white_label(id_org: UUID):
    query = select(WhiteLabel).where(WhiteLabel.id_org == id_org)

    data = await db.session.execute(query)

    try:
        return data.scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"White Label for id_org {id_org} was not found",
        )

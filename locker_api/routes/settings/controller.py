from uuid import UUID, uuid4
import re
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import insert, select, update
from sqlalchemy.exc import NoResultFound
from util.validator import lookup_phone

from .helpers import parse_country
from .model import (
    OrgSettings,
    LiteAppSettings,
    SignInMethod,
    ReservationWidgetSettings,
    ResTimeUnit,
)


async def get_max_reservation_count(id_org: UUID) -> int:
    query = select(OrgSettings.default_max_reservations).where(
        OrgSettings.id_org == id_org
    )

    response = await db.session.execute(query)
    max_reservation_count = response.scalar_one_or_none() or 0

    return max_reservation_count


async def get_settings_org(id_org: UUID) -> OrgSettings.Read:
    query = select(OrgSettings).where(OrgSettings.id_org == id_org)

    response = await db.session.execute(query)
    try:
        return response.scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail="Settings are not set for this organization",
        )


async def update_settings(id_org: UUID, settings: OrgSettings.Write):
    phone_regex = re.compile(r"^\+?[1-9]\d{1,14}$")
    if settings.default_support_phone:
        if not phone_regex.match(settings.default_support_phone):
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number",
            )
        lookup_phone(settings.default_support_phone)

    query = (
        update(OrgSettings)
        .where(OrgSettings.id_org == id_org)
        .values(
            default_currency=settings.default_currency,
            default_country=settings.default_country,
            default_max_reservations=settings.default_max_reservations,
            maintenance_on_issue=settings.maintenance_on_issue,
            parcel_expiration=settings.parcel_expiration,
            parcel_expiration_unit=settings.parcel_expiration_unit,
            use_long_parcel_codes=settings.use_long_parcel_codes,
            default_time_zone=settings.default_time_zone,
            default_date_format=settings.default_date_format,
            delivery_sms_start=settings.delivery_sms_start,
            service_sms_start=settings.service_sms_start,
            service_sms_charge=settings.service_sms_charge,
            service_sms_end=settings.service_sms_end,
            event_sms_refund=settings.event_sms_refund,
            invoice_prefix=settings.invoice_prefix,
            default_device_hardware=settings.default_device_hardware,
            default_device_mode=settings.default_device_mode,
            default_id_price=settings.default_id_price,
            default_id_size=settings.default_id_size,
            default_support_email=settings.default_support_email,
            default_support_phone=settings.default_support_phone,
            language=settings.language.value,
        )
        .returning(OrgSettings)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    # Check country and update date file_format and currency accordingly
    if settings.default_country:
        query = (
            update(OrgSettings)
            .where(OrgSettings.id_org == id_org)
            .values(
                {
                    "default_date_format": parse_country.get_date_format(
                        settings.default_country
                    ),
                }
            )
            .returning(OrgSettings)
        )

        response = await db.session.execute(query)
        await db.session.commit()  # raise IntegrityError

    try:
        return response.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Settings were not found for id_org '{id_org}'",
        )


async def create_settings(id_org: UUID, settings: OrgSettings.Write):
    phone_regex = re.compile(r"^\+?[1-9]\d{1,14}$")
    if settings.default_support_phone:
        if not phone_regex.match(settings.default_support_phone):
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number",
            )
        lookup_phone(settings.default_support_phone)

    query = select(OrgSettings).where(OrgSettings.id_org == id_org)

    response = await db.session.execute(query)
    data = response.scalar_one_or_none()

    if data:
        raise HTTPException(
            status_code=400,
            detail=f"Settings for id_org {id_org} already exists",
        )

    query = (
        insert(OrgSettings)
        .values(
            id=uuid4(),
            id_org=id_org,
            default_country=settings.default_country,
            default_currency=settings.default_currency,
            default_max_reservations=settings.default_max_reservations,
            maintenance_on_issue=settings.maintenance_on_issue,
            parcel_expiration=settings.parcel_expiration,
            parcel_expiration_unit=settings.parcel_expiration_unit,
            use_long_parcel_codes=settings.use_long_parcel_codes,
            default_time_zone=settings.default_time_zone,
            default_date_format=settings.default_date_format,
            delivery_sms_start=settings.delivery_sms_start,
            service_sms_start=settings.service_sms_start,
            service_sms_charge=settings.service_sms_charge,
            service_sms_end=settings.service_sms_end,
            event_sms_refund=settings.event_sms_refund,
            invoice_prefix=settings.invoice_prefix,
            default_device_hardware=settings.default_device_hardware,
            default_device_mode=settings.default_device_mode,
            default_id_price=settings.default_id_price,
            default_id_size=settings.default_id_size,
            default_support_email=settings.default_support_email,
            default_support_phone=settings.default_support_phone,
            language=settings.language.value,
        )
        .returning(OrgSettings)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def get_lite_app_settings(id_org: UUID) -> LiteAppSettings.Read:
    query = select(LiteAppSettings).where(LiteAppSettings.id_org == id_org)

    response = await db.session.execute(query)
    data = response.scalars().first()

    if not data:
        data = await create_lite_app_settings(
            id_org,
            lite_app_settings=LiteAppSettings.Write(
                sign_in_method=SignInMethod.both,
                allow_multiple_rentals=True,
                allow_user_reservation=True,
                track_product_condition=True,
                allow_photo_end_rental=True,
                setup_in_app_payment=True,
                primary_color="#000000",
                secondary_color="#000000",
            ),
        )

    return LiteAppSettings.Read.parse_obj(data)


async def create_lite_app_settings(
    id_org: UUID, lite_app_settings: LiteAppSettings.Write
) -> LiteAppSettings.Read:
    query = select(LiteAppSettings).where(LiteAppSettings.id_org == id_org)

    response = await db.session.execute(query)
    data = response.scalar_one_or_none()

    if data:
        raise HTTPException(
            status_code=400,
            detail=f"Settings for id_org {id_org} already exists",
        )

    query = (
        insert(LiteAppSettings)
        .values(**lite_app_settings.dict(), id_org=id_org)
        .returning(LiteAppSettings)
    )

    response = await db.session.execute(query)
    await db.session.commit()
    data = response.all().pop()

    return LiteAppSettings.Read.parse_obj(data)


async def update_lite_app_settings(
    id_org: UUID, lite_app_settings: LiteAppSettings.Write
) -> LiteAppSettings.Read:
    query = (
        update(LiteAppSettings)
        .where(LiteAppSettings.id_org == id_org)
        .values(**lite_app_settings.dict())
        .returning(LiteAppSettings)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    try:
        return response.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Settings were not found for id_org '{id_org}'",
        )


async def get_res_widget_settings(id_org: UUID) -> ReservationWidgetSettings.Read:
    query = select(ReservationWidgetSettings).where(
        ReservationWidgetSettings.id_org == id_org
    )

    response = await db.session.execute(query)
    data = response.scalar_one_or_none()

    if not data:
        data = await create_res_widget_settings(
            id_org,
            settings=ReservationWidgetSettings.Write(
                primary_color="#000000",
                secondary_color="#000000",
                background_color="#000000",
                duration=0,
                duration_unit=ResTimeUnit.hour,
                in_app_payment=True,
            ),
        )

    return ReservationWidgetSettings.Read.parse_obj(data)


async def create_res_widget_settings(
    id_org: UUID, settings: ReservationWidgetSettings.Write
) -> ReservationWidgetSettings.Read:
    query = select(ReservationWidgetSettings).where(
        ReservationWidgetSettings.id_org == id_org
    )

    response = await db.session.execute(query)
    data = response.scalar_one_or_none()

    if data:
        raise HTTPException(
            status_code=400,
            detail=f"Settings for id_org {id_org} already exists",
        )

    query = (
        insert(ReservationWidgetSettings)
        .values(**settings.dict(), id_org=id_org)
        .returning(ReservationWidgetSettings)
    )

    response = await db.session.execute(query)
    await db.session.commit()
    data = response.all().pop()

    return ReservationWidgetSettings.Read.parse_obj(data)


async def update_res_widget_settings(
    id_org: UUID, settings: ReservationWidgetSettings.Write
) -> ReservationWidgetSettings.Read:
    query = (
        update(ReservationWidgetSettings)
        .where(ReservationWidgetSettings.id_org == id_org)
        .values(**settings.dict())
        .returning(ReservationWidgetSettings)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    try:
        return response.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Settings were not found for id_org '{id_org}'",
        )

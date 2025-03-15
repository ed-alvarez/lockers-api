from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, conint, constr
from sqlmodel import Field, SQLModel
from util.form import as_form

from ..device.model import HardwareType, Mode
from ..financial.model import StripeCountry
from ..price.model import Currency


class ResTimeUnit(Enum):
    minute = "minute"
    hour = "hour"
    day = "day"
    week = "week"


class ExpirationUnit(Enum):
    hours = "hours"
    days = "days"


class SignInMethod(Enum):
    email = "email"
    phone = "phone"
    both = "both"


class Language(Enum):
    en = "en"
    es = "es"
    it = "it"
    fr = "fr"
    pl = "pl"
    de = "de"


class OrgSettings(SQLModel, table=True):
    __tablename__ = "org_settings"

    id: UUID = Field(primary_key=True)
    id_org: UUID = Field(foreign_key="org.id")

    default_country: Optional[StripeCountry]
    default_currency: Currency
    default_max_reservations: Optional[int]
    maintenance_on_issue: Optional[bool]

    parcel_expiration: Optional[int]
    parcel_expiration_unit: Optional[ExpirationUnit]
    use_long_parcel_codes: Optional[bool]

    default_time_zone: Optional[str]
    default_date_format: Optional[str]
    delivery_sms_start: Optional[str]
    service_sms_start: Optional[str]
    service_sms_charge: Optional[str]
    service_sms_end: Optional[str]
    event_sms_refund: Optional[str]

    invoice_prefix: Optional[str]

    default_device_hardware: Optional[HardwareType]
    default_device_mode: Optional[Mode]

    default_id_size: Optional[UUID] = Field(foreign_key="size.id")

    default_id_price: Optional[UUID] = Field(foreign_key="price.id")
    default_support_email: Optional[str] = "support@koloni.me"
    default_support_phone: Optional[str] = "+18337081205"

    language: Optional[str]

    @as_form
    class Write(BaseModel):
        default_currency: Optional[Currency] = Currency.usd
        default_country: Optional[StripeCountry]
        default_max_reservations: Optional[int]
        maintenance_on_issue: Optional[bool] = True

        parcel_expiration: Optional[conint(gt=0)]
        parcel_expiration_unit: Optional[ExpirationUnit]
        use_long_parcel_codes: Optional[bool]

        default_time_zone: Optional[str]
        default_date_format: Optional[str]
        delivery_sms_start: Optional[str]
        service_sms_start: Optional[str]
        service_sms_charge: Optional[str]
        service_sms_end: Optional[str]
        event_sms_refund: Optional[str]

        invoice_prefix: Optional[
            constr(
                max_length=3,
                to_upper=True,
                strip_whitespace=True,
                regex=r"^[A-Z]+$",
            )
        ]

        default_device_hardware: Optional[HardwareType]
        default_device_mode: Optional[Mode]
        default_id_size: Optional[UUID]

        default_id_price: Optional[UUID]
        default_support_email: Optional[str] = "support@koloni.me"
        default_support_phone: Optional[str] = "+18337081205"

        language: Optional[Language] = Language.en

    class Read(BaseModel):
        id: UUID
        id_org: UUID
        default_country: Optional[StripeCountry]
        default_currency: Currency
        default_max_reservations: Optional[int]
        maintenance_on_issue: Optional[bool]

        parcel_expiration: Optional[int]
        parcel_expiration_unit: Optional[ExpirationUnit]
        use_long_parcel_codes: Optional[bool]

        default_time_zone: Optional[str]
        default_date_format: Optional[str]
        delivery_sms_start: Optional[str]
        service_sms_start: Optional[str]
        service_sms_charge: Optional[str]
        service_sms_end: Optional[str]
        event_sms_refund: Optional[str]

        invoice_prefix: Optional[str]

        default_device_hardware: Optional[HardwareType]
        default_device_mode: Optional[Mode]
        default_id_size: Optional[UUID]

        default_id_price: Optional[UUID]
        default_support_email: Optional[str]  # new
        default_support_phone: Optional[str]  # new

        language: Optional[str]


class LiteAppSettings(SQLModel, table=True):
    __tablename__ = "lite_app_settings"

    id: UUID = Field(primary_key=True)
    id_org: UUID = Field(foreign_key="org.id")

    sign_in_method: Optional[SignInMethod]

    allow_multiple_rentals: Optional[bool]
    allow_user_reservation: Optional[bool]
    track_product_condition: Optional[bool]
    allow_photo_end_rental: Optional[bool]
    setup_in_app_payment: Optional[bool]

    primary_color: Optional[str]
    secondary_color: Optional[str]

    class Write(BaseModel):
        sign_in_method: Optional[SignInMethod]

        allow_multiple_rentals: Optional[bool]
        allow_user_reservation: Optional[bool]
        track_product_condition: Optional[bool]
        allow_photo_end_rental: Optional[bool]
        setup_in_app_payment: Optional[bool]

        primary_color: Optional[str] = "#ffffff"
        secondary_color: Optional[str] = "#ffffff"

    class Read(BaseModel):
        sign_in_method: Optional[SignInMethod]

        allow_multiple_rentals: Optional[bool]
        allow_user_reservation: Optional[bool]
        track_product_condition: Optional[bool]
        allow_photo_end_rental: Optional[bool]
        setup_in_app_payment: Optional[bool]

        primary_color: Optional[str]
        secondary_color: Optional[str]


class ReservationWidgetSettings(SQLModel, table=True):
    __tablename__ = "reservation_widget_settings"

    id: UUID = Field(primary_key=True)
    id_org: UUID = Field(foreign_key="org.id")

    primary_color: Optional[str]
    secondary_color: Optional[str]
    background_color: Optional[str]

    duration: Optional[int]
    duration_unit: Optional[ResTimeUnit]

    in_app_payment: Optional[bool]

    class Write(BaseModel):
        primary_color: Optional[str] = "#000000"
        secondary_color: Optional[str] = "#000000"
        background_color: Optional[str] = "#000000"

        duration: Optional[int] = 0
        duration_unit: Optional[ResTimeUnit] = ResTimeUnit.hour

        in_app_payment: Optional[bool] = True

    class Read(BaseModel):
        primary_color: Optional[str]
        secondary_color: Optional[str]
        background_color: Optional[str]

        duration: Optional[int]
        duration_unit: Optional[ResTimeUnit]

        in_app_payment: Optional[bool]

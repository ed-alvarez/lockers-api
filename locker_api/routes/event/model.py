from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, condecimal, conint, constr, AnyHttpUrl
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID

from ..device.model import Device
from ..user.model import User
from ..promo.model import Promo
from ..memberships.model import Membership


class EventStatus(Enum):
    in_progress = "in_progress"
    awaiting_payment_confirmation = "awaiting_payment_confirmation"
    awaiting_service_pickup = "awaiting_service_pickup"
    awaiting_service_dropoff = "awaiting_service_dropoff"
    awaiting_user_pickup = "awaiting_user_pickup"
    transaction_in_progress = "transaction_in_progress"
    finished = "finished"
    canceled = "canceled"
    refunded = "refunded"
    reserved = "reserved"
    expired = "expired"


class PenalizeReason(Enum):
    missing_items = "missing_items"
    damaged_items = "damaged_items"
    misconduct = "misconduct"
    other = "other"


class EventType(Enum):
    service = "service"
    rental = "rental"
    storage = "storage"
    delivery = "delivery"
    vending = "vending"


class Duration(BaseModel):
    hours: Optional[conint(ge=0)] = 0
    days: Optional[conint(ge=0)] = 0
    weeks: Optional[conint(ge=0)] = 0


class PublicEvent(BaseModel):
    id: UUID
    app_logo: Optional[str]
    invoice_id: Optional[str]
    created_at: datetime

    event_status: EventStatus
    event_type: EventType

    device_name: str
    device_id: UUID
    device_number: Optional[int]
    location_name: str
    location_address: str
    user_phone: Optional[str]
    user_email: Optional[str]
    user_name: Optional[str]


class BatchResponse(BaseModel):
    status_code: int
    event_code: int
    response: dict | str


class Event(SQLModel, table=True):
    __tablename__ = "event"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID(),
            server_default=func.gen_random_uuid(),
            unique=True,
            primary_key=True,
        )
    )

    created_at: datetime = Field(
        sa_column=Column(
            "created_at",
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
            nullable=False,
        )
    )

    started_at: datetime = Field(
        sa_column=Column("started_at", DateTime(timezone=True))
    )

    ended_at: datetime = Field(sa_column=Column("ended_at", DateTime(timezone=True)))
    canceled_at: Optional[datetime] = Field(
        sa_column=Column("canceled_at", DateTime(timezone=True))
    )

    invoice_id: str = Field(nullable=True)
    order_id: Optional[str] = Field(nullable=True)

    # Stripe
    payment_intent_id: str = Field(nullable=True)
    setup_intent_id: str = Field(nullable=True)
    stripe_subscription_id: str = Field(nullable=True)

    # Harbor Specific
    harbor_session_seed: str = Field(nullable=True)
    harbor_session_token: str = Field(nullable=True)
    harbor_session_token_auth: str = Field(nullable=True)
    harbor_payload: str = Field(nullable=True)
    harbor_payload_auth: str = Field(nullable=True)
    harbor_reservation_id: str = Field(nullable=True)

    # Delivery Only
    code: Optional[int] = Field(nullable=True)

    # Passcode
    passcode: Optional[constr(regex=r"\d{4}", max_length=4, min_length=4)] = Field(
        nullable=True
    )

    event_status: EventStatus = Field(default=EventStatus.in_progress)
    event_type: EventType = Field(default=EventType.service)

    total: condecimal(max_digits=8, decimal_places=2) = Field(nullable=True)
    total_time: str = Field(nullable=True)
    weight: Optional[float]

    refunded_amount: condecimal(max_digits=8, decimal_places=2) = 0

    penalize_charge: Optional[float]
    penalize_reason: Optional[PenalizeReason]

    signature_url: Optional[str] = Field(nullable=True)

    courier_pin_code: Optional[str]
    canceled_by: Optional[str]  # Member's name
    image_url: Optional[AnyHttpUrl] = Field(nullable=True)

    id_org: UUID = Field(foreign_key="org.id")
    id_user: Optional[UUID] = Field(foreign_key="User.id")
    id_device: UUID = Field(foreign_key="device.id")
    id_promo: Optional[UUID] = Field(foreign_key="promo.id")
    id_membership: Optional[UUID] = Field(foreign_key="memberships.id")

    device: Optional["Device"] = Relationship(
        back_populates="events",
        sa_relationship_kwargs={"lazy": "joined", "uselist": False},
    )

    user: Optional["User"] = Relationship(
        back_populates="events",
        sa_relationship_kwargs={"lazy": "joined", "uselist": False},
    )

    promo: Optional["Promo"] = Relationship(
        back_populates="events",
        sa_relationship_kwargs={"lazy": "joined", "uselist": False},
    )

    membership: Optional["Membership"] = Relationship(
        back_populates="events",
        sa_relationship_kwargs={"lazy": "joined", "uselist": False},
    )

    issue: Optional["Issue"] = Relationship(  # noqa: F821
        back_populates="event",
        sa_relationship_kwargs={"lazy": "noload", "uselist": False},
    )

    log: Optional["Log"] = Relationship(  # noqa: F821
        back_populates="event",
        sa_relationship_kwargs={"lazy": "noload", "uselist": False},
    )

    class Read(BaseModel):
        id: UUID
        invoice_id: Optional[str]
        order_id: Optional[str]
        code: Optional[int]
        created_at: datetime
        started_at: Optional[datetime]
        ended_at: Optional[datetime]
        canceled_at: Optional[datetime]

        event_status: EventStatus
        event_type: EventType

        harbor_session_seed: Optional[str]
        harbor_session_token: Optional[str]
        harbor_session_token_auth: Optional[str]
        harbor_payload: Optional[str]
        harbor_payload_auth: Optional[str]
        harbor_reservation_id: Optional[str]

        image_url: Optional[AnyHttpUrl]

        total: Optional[float]
        total_time: Optional[str]
        weight: Optional[float]

        refunded_amount: Optional[float]

        penalize_charge: Optional[float]
        penalize_reason: Optional[PenalizeReason]

        courier_pin_code: Optional[str]
        canceled_by: Optional[str]  # Member's name

        signature_url: Optional[str]

        id_user: Optional[UUID]
        id_device: Optional[UUID]

        device: Optional[Device.Read]
        user: Optional[User.Read]
        promo: Optional[Promo.Read]
        membership: Optional[Membership.Read]


class EventBatch(BaseModel):
    detail: str
    items: list[Event.Read]
    err: Optional[list]


class PaginatedEvents(BaseModel):
    items: list[Event.Read]

    total: int
    pages: int


class StripeCustomerData(BaseModel):
    ephemeral_key: Optional[dict]
    customer_id: Optional[str]


class StripePaymentData(BaseModel):
    client_secret: Optional[str]
    customer_data: Optional[StripeCustomerData]
    publishable_key: Optional[str]


class StartReservationResponse(BaseModel):
    client_secret: Optional[str]
    customer_data: Optional[StripeCustomerData]
    publishable_key: Optional[str]
    stripe_account_id: Optional[str]

    # Event fields

    id: UUID
    invoice_id: Optional[str]
    order_id: Optional[str]
    code: Optional[str]
    created_at: datetime

    event_status: EventStatus
    event_type: EventType

    payment_intent_id: Optional[str]
    setup_intent_id: Optional[str]

    total: Optional[float]

    id_user: Optional[UUID]
    id_device: UUID


class CompleteReservationResponse(BaseModel):
    id: UUID
    redirect_url_3ds: Optional[str]
    invoice_id: Optional[str]
    order_id: Optional[str]
    code: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    event_status: EventStatus
    event_type: EventType

    harbor_session_seed: Optional[str]
    harbor_session_token: Optional[str]
    harbor_session_token_auth: Optional[str]
    harbor_payload: Optional[str]
    harbor_payload_auth: Optional[str]
    harbor_reservation_id: Optional[str]

    total: Optional[float]
    total_time: Optional[str]

    refunded_amount: Optional[float]

    id_user: Optional[UUID]
    id_device: UUID

    device: Optional[Device.Read]
    user: Optional[User.Read]


class StartEvent(BaseModel):
    event_type: EventType

    from_user: Optional[UUID]

    id_condition: Optional[UUID]
    id_device: Optional[UUID]

    id_size: Optional[UUID]
    size_external_id: Optional[str]
    id_location: Optional[UUID]
    location_external_id: Optional[str]

    order_id: Optional[str]

    id_user: Optional[UUID]
    user_external_id: Optional[str]
    phone_number: Optional[str]
    pin_code: Optional[constr(regex=r"\d{4}", max_length=4, min_length=4)]
    passcode: Optional[constr(regex=r"\d{4}", max_length=4, min_length=4)]
    duration: Optional[Duration]

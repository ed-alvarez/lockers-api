from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, condecimal
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID

from ..event.model import EventType
from ..location.model import Location
from ..member.model import Member
from .link_notification_location import LinkNotificationLocation


class RecipientType(Enum):
    user = "user"
    admin = "admin"


class ChannelType(Enum):
    email = "email"
    sms = "sms"
    push = "push"

    email_2nd = "email_2nd"
    sms_2nd = "sms_2nd"
    push_2nd = "push_2nd"


class TimeUnit(Enum):
    minute = "minute"
    hour = "hour"
    day = "day"
    week = "week"
    immediately = "immediately"


class NotificationType(Enum):
    on_signup = "on_signup"  # welcome

    on_start = "on_start"  # start
    in_progress = "in_progress"  # * new
    on_complete = "on_complete"  # complete

    on_service_pickup = "on_service_pickup"  # pickup
    on_service_charge = "on_service_charge"  # charge
    on_service_dropoff = "on_service_dropoff"  # user_pickup

    on_reservation = "on_reservation"  # * new
    non_locker_delivery = "non_locker_delivery"  # * new

    marketing = "marketing"  # * new
    instructions = "instructions"  # * new

    reminder = "reminder"  # reminder
    custom = "custom"  # custom

    on_expired = "on_expired"


class Notification(SQLModel, table=True):
    __tablename__ = "notification"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID,
            server_default=func.gen_random_uuid(),
            primary_key=True,
            unique=True,
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

    name: str = Field(nullable=False)
    message: str = Field(nullable=False)

    mode: EventType = Field(nullable=False)

    notification_type: NotificationType = Field(nullable=False)

    time_amount: condecimal(max_digits=8, decimal_places=2, ge=0) = Field(  # type: ignore
        nullable=False, default=0
    )
    time_unit: TimeUnit = Field(nullable=False, default=TimeUnit.minute)
    before: bool = Field(nullable=False, default=False)
    after: bool = Field(nullable=False, default=True)

    email: bool = Field(nullable=False, default=False)
    sms: bool = Field(nullable=False, default=True)
    push: bool = Field(nullable=False, default=False)

    #  2nd notification channel
    email_2nd: bool = Field(nullable=False, default=False)
    sms_2nd: bool = Field(nullable=False, default=False)
    push_2nd: bool = Field(nullable=False, default=False)

    is_template: bool = Field(nullable=False, default=False)

    id_member: Optional[UUID]

    recipient_type: Optional[RecipientType]

    id_org: UUID = Field(foreign_key="org.id")

    locations: List["Location"] = Relationship(
        back_populates="notifications",
        link_model=LinkNotificationLocation,
        sa_relationship_kwargs={"lazy": "joined", "join_depth": 1},
    )

    class Write(BaseModel):
        name: str
        message: str

        mode: EventType
        notification_type: NotificationType

        time_amount: Optional[condecimal(max_digits=8, decimal_places=2, ge=0)] = 0
        time_unit: TimeUnit
        before: Optional[bool] = False
        after: Optional[bool] = True

        email: Optional[bool] = False
        sms: Optional[bool] = True
        push: Optional[bool] = False

        email_2nd: Optional[bool] = False
        sms_2nd: Optional[bool] = False
        push_2nd: Optional[bool] = False

        is_template: bool = False

        id_member: Optional[UUID]
        recipient_type: Optional[RecipientType] = RecipientType.user

        locations: Optional[List[UUID]] = []

    class Patch(BaseModel):
        name: Optional[str]
        message: Optional[str]

        mode: Optional[EventType]
        notification_type: Optional[NotificationType]

        time_amount: Optional[condecimal(max_digits=8, decimal_places=2, ge=0)]
        time_unit: Optional[TimeUnit]

        email: Optional[bool]
        sms: Optional[bool]
        push: Optional[bool]

        email_2nd: Optional[bool]
        sms_2nd: Optional[bool]
        push_2nd: Optional[bool]

        is_template: Optional[bool]

        id_member: Optional[UUID]
        recipient_type: Optional[RecipientType]

        locations: Optional[List[UUID]] = []

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        name: str
        message: str

        mode: EventType
        notification_type: NotificationType

        time_amount: condecimal(max_digits=8, decimal_places=2, ge=0)
        time_unit: TimeUnit
        before: bool
        after: bool

        email: bool
        sms: bool
        push: bool

        email_2nd: bool
        sms_2nd: bool
        push_2nd: bool

        is_template: bool

        id_member: Optional[UUID]
        member: Optional[Member]
        recipient_type: Optional[RecipientType]

        locations: Optional[List[Location.Read]] = []


class PaginatedNotifications(BaseModel):
    items: list[Notification.Read]

    total: int
    pages: int

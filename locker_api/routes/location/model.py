from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, condecimal
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import BOOLEAN
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID
from util.form import as_form

from ..memberships.link_membership_location import LinkMembershipLocation
from ..notifications.link_notification_location import LinkNotificationLocation
from ..price.model import Price
from ..device.model import Device, Restriction


class Location(SQLModel, table=True):
    __tablename__ = "location"

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

    contact_email: Optional[str]  # new
    contact_phone: Optional[str]  # new

    name: str
    custom_id: Optional[str]
    address: str
    image: Optional[str]

    hidden: bool = Field(sa_column=Column("hidden", BOOLEAN(), default=False))
    shared: bool  # * Allow other sub-orgs to use this location

    latitude: condecimal(max_digits=18, decimal_places=15)
    longitude: condecimal(max_digits=18, decimal_places=15)

    # Delivery
    restrict_by_user_code: bool

    # Pick-up verification
    verify_pin_code: bool
    verify_qr_code: bool
    verify_url: bool
    verify_signature: bool

    # Notification Channels
    email: bool
    phone: bool

    id_org: UUID = Field(foreign_key="org.id")
    id_price: Optional[UUID] = Field(foreign_key="price.id")

    price: Optional["Price"] = Relationship(
        back_populates="locations",
        sa_relationship_kwargs={"lazy": "joined", "join_depth": 1},
    )

    devices: list["Device"] = Relationship(  # noqa: F821
        back_populates="location",
        sa_relationship_kwargs={"lazy": "noload"},
    )

    memberships: list["Membership"] = Relationship(  # noqa: F821
        back_populates="locations",
        link_model=LinkMembershipLocation,
        sa_relationship_kwargs={"lazy": "noload"},
    )

    notifications: list["Notification"] = Relationship(  # noqa: F821
        back_populates="locations",
        link_model=LinkNotificationLocation,
        sa_relationship_kwargs={"lazy": "noload"},
    )

    reservation: Optional["Reservation"] = Relationship(  # noqa: F821
        back_populates="location",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": False,
        },
    )

    user: Optional["LinkOrgUser"] = Relationship(  # noqa: F821
        back_populates="location",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": False,
        },
    )

    @as_form
    class Write(BaseModel):
        name: str
        address: str

        id_price: Optional[UUID] = None

        custom_id: Optional[str] = None

        hidden: bool = False
        shared: bool = False

        latitude: condecimal(max_digits=18, decimal_places=15)
        longitude: condecimal(max_digits=18, decimal_places=15)

        contact_email: Optional[str] = None
        contact_phone: Optional[str] = None

        restrict_by_user_code: Optional[bool] = False

        verify_pin_code: Optional[bool] = True
        verify_qr_code: Optional[bool] = False
        verify_url: Optional[bool] = False
        verify_signature: Optional[bool] = False

        email: Optional[bool] = False
        phone: Optional[bool] = True

    class Patch(BaseModel):
        name: Optional[str]
        address: Optional[str]

        id_price: Optional[UUID] = None

        custom_id: Optional[str]

        hidden: Optional[bool]
        shared: Optional[bool]

        latitude: Optional[condecimal(max_digits=18, decimal_places=15)]
        longitude: Optional[condecimal(max_digits=18, decimal_places=15)]

        contact_email: Optional[str]
        contact_phone: Optional[str]

        restrict_by_user_code: Optional[bool]

        verify_pin_code: Optional[bool]
        verify_qr_code: Optional[bool]
        verify_url: Optional[bool]
        verify_signature: Optional[bool]

        email: Optional[bool]
        phone: Optional[bool]

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        id_org: UUID

        name: str
        custom_id: Optional[str]
        address: str
        restriction: Optional[Restriction]
        image: Optional[str]

        hidden: bool
        shared: bool

        latitude: condecimal(max_digits=18, decimal_places=15)
        longitude: condecimal(max_digits=18, decimal_places=15)

        contact_email: Optional[str]
        contact_phone: Optional[str]

        restrict_by_user_code: bool

        verify_pin_code: Optional[bool]
        verify_qr_code: Optional[bool]
        verify_url: Optional[bool]
        verify_signature: Optional[bool]

        email: Optional[bool]
        phone: Optional[bool]

        available_devices: int = 0
        reserved_devices: int = 0
        maintenance_devices: int = 0

        devices: Optional[List[Device.Read]] = []
        price: Optional[Price.Read]


class PaginatedLocations(BaseModel):
    items: list[Location.Read]

    total: int
    pages: int

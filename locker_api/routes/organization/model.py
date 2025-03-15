from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, constr, AnyHttpUrl
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID

from ..location.model import Location
from ..white_label.model import WhiteLabel

from util.form import as_form


class Org(SQLModel, table=True):
    __tablename__ = "org"

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
            server_default=func.now(),
            nullable=False,
        )
    )

    name: str = Field(unique=True)
    active: bool = Field(default=True, nullable=True)

    user_pool: Optional[str] = Field(nullable=True)
    client_id: Optional[str] = Field(nullable=True)
    stripe_account_id: str = Field(default=None, nullable=True)
    twilio_sid: Optional[str] = Field(default=None, nullable=True)

    rental_mode: bool
    storage_mode: bool
    delivery_mode: bool
    service_mode: bool
    vending_mode: bool

    linka_hardware: bool
    ojmar_hardware: bool
    gantner_hardware: bool
    harbor_hardware: bool
    dclock_hardware: bool
    spintly_hardware: bool

    super_tenant: bool
    lite_app_enabled: bool

    pricing: bool = True
    product: bool = True
    notifications: bool = True
    multi_tenant: bool = True
    toolbox: bool = True

    id_tenant: UUID = Field(foreign_key="org.id", nullable=True)

    white_label: Optional["WhiteLabel"] = Relationship(
        back_populates="org",
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "joined",
        },
    )

    class Write(BaseModel):
        name: constr(strip_whitespace=True)
        active: bool

    class Read(BaseModel):
        id: UUID
        name: str
        active: bool
        created_at: datetime

        user_pool: Optional[str]

        rental_mode: bool
        storage_mode: bool
        delivery_mode: bool
        service_mode: bool
        vending_mode: bool

        linka_hardware: bool
        ojmar_hardware: bool
        gantner_hardware: bool
        harbor_hardware: bool
        dclock_hardware: bool
        spintly_hardware: bool

        super_tenant: bool
        lite_app_enabled: bool

        pricing: bool = True
        product: bool = True
        notifications: bool = True
        multi_tenant: bool = True
        toolbox: bool = True

        stripe_enabled: Optional[bool]
        stripe_account_id: Optional[str]

        id_tenant: Optional[UUID]
        twilio_sid: Optional[str]
        white_label: Optional[WhiteLabel.Read]
        oem_logo: Optional[AnyHttpUrl]
        sub_orgs: Optional[List[dict]]


@as_form
class OrgFeatures(BaseModel):
    rental_mode: Optional[bool] = True
    storage_mode: Optional[bool] = True
    delivery_mode: Optional[bool] = True
    service_mode: Optional[bool] = True
    vending_mode: Optional[bool] = True

    linka_hardware: Optional[bool] = True
    ojmar_hardware: Optional[bool] = True
    gantner_hardware: Optional[bool] = True
    harbor_hardware: Optional[bool] = True
    dclock_hardware: Optional[bool] = True
    spintly_hardware: Optional[bool] = True

    super_tenant: Optional[bool] = True
    lite_app_enabled: Optional[bool] = True

    pricing: bool = True
    product: bool = True
    notifications: bool = True
    multi_tenant: bool = True
    toolbox: bool = True


class OrgReadPublic(BaseModel):
    id: UUID
    name: str
    app_logo: Optional[str]
    user_pool: str
    client_id: Optional[str]
    created_at: datetime

    rental_mode: bool
    storage_mode: bool
    delivery_mode: bool
    service_mode: bool
    vending_mode: bool

    white_label: Optional[WhiteLabel.Read]

    support_email: Optional[str]
    support_phone: Optional[str]

    stripe_enabled: bool
    super_tenant: bool
    oem_logo: Optional[str]


class LinkOrgUser(SQLModel, table=True):
    __tablename__ = "link_org_user"

    created_at: datetime = Field(
        sa_column=Column(
            "created_at",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )

    id_org: UUID = Field(foreign_key="org.id", primary_key=True)
    id_user: UUID = Field(foreign_key="User.id", primary_key=True)
    id_membership: Optional[UUID] = Field(foreign_key="memberships.id", nullable=True)

    id_favorite_location: Optional[UUID] = Field(
        foreign_key="location.id", nullable=True
    )

    location: Optional["Location"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "lazy": "joined",
            "uselist": False,
        },
    )

    stripe_customer_id: Optional[str] = Field(default=None, nullable=True)
    stripe_subscription_id: Optional[str] = Field(default=None, nullable=True)

    class Read(BaseModel):
        location: Optional[Location.Read]


class PaginatedOrgs(BaseModel):
    items: list[Org.Read]

    total: int
    pages: int


class InviteMessageTemplate:
    email_message: str

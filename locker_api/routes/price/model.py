from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, condecimal
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID

from ..device.link_device_price import LinkDevicePrice


class Unit(Enum):
    # Pay per time
    minute = "minute"
    hour = "hour"
    day = "day"
    week = "week"

    # Pay per weight
    lb = "lb"
    kg = "kg"


class Currency(Enum):
    usd = "usd"  # USD
    eur = "eur"  # Euro
    gbp = "gbp"  # British Pound
    aud = "aud"  # Australian Dollar
    cad = "cad"  # Canadian Dollar


class PriceType(Enum):
    pay_per_weight = "pay_per_weight"
    pay_per_time = "pay_per_time"


class Price(SQLModel, table=True):
    __tablename__ = "price"

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

    name: str
    amount: condecimal(max_digits=8, decimal_places=2, ge=0)

    currency: Currency = Field(default=Currency.usd)
    prorated: bool = Field(default=False)
    default: bool = Field(default=False)
    card_on_file: bool = Field(default=True)

    unit: Unit = Field(default=Unit.lb)
    unit_amount: condecimal(max_digits=8, decimal_places=2, gt=0) = Field(default=1)

    price_type: PriceType = Field(default=PriceType.pay_per_weight)

    id_org: UUID = Field(foreign_key="org.id")

    devices: list["Device"] = Relationship(  # noqa: F821
        back_populates="price",
        sa_relationship_kwargs={"lazy": "noload"},
    )

    devices_list: list["Device"] = Relationship(  # noqa: F821
        back_populates="prices",
        link_model=LinkDevicePrice,
        sa_relationship_kwargs={"lazy": "noload"},
    )

    locations: list["Location"] = Relationship(  # noqa: F821
        back_populates="price",
        sa_relationship_kwargs={"lazy": "noload"},
    )

    class Write(BaseModel):
        name: str
        amount: condecimal(max_digits=8, decimal_places=2, ge=0)

        currency: Currency
        prorated: bool
        default: Optional[bool] = False
        card_on_file: bool

        unit: Unit
        unit_amount: condecimal(max_digits=8, decimal_places=2, gt=0) = Field(default=1)

        price_type: PriceType

    class Patch(BaseModel):
        name: Optional[str]
        amount: Optional[condecimal(max_digits=8, decimal_places=2, ge=0)]

        currency: Optional[Currency]
        prorated: Optional[bool]
        default: Optional[bool]
        card_on_file: Optional[bool]

        unit: Optional[Unit]
        unit_amount: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]

        price_type: Optional[PriceType]

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        name: str
        amount: condecimal(max_digits=8, decimal_places=2, ge=0)

        currency: Currency
        prorated: bool
        default: bool
        card_on_file: bool

        unit: Unit
        unit_amount: condecimal(max_digits=8, decimal_places=2, gt=0)

        price_type: PriceType


class PaginatedPrices(BaseModel):
    items: list[Price.Read]

    total: int
    pages: int

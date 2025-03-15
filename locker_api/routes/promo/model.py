from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, condecimal
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID


class DiscountType(Enum):
    percentage = "percentage"
    fixed = "fixed"


class Promo(SQLModel, table=True):
    __tablename__ = "promo"

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
    code: str

    amount: condecimal(max_digits=8, decimal_places=2, gt=0)

    discount_type: DiscountType = Field(default=DiscountType.percentage)

    start_time: datetime = Field(
        sa_column=Column(
            "start_time",
            DateTime(timezone=True),
        )
    )
    end_time: datetime = Field(
        sa_column=Column(
            "end_time",
            DateTime(timezone=True),
        )
    )

    id_org: UUID = Field(foreign_key="org.id")

    events: list["Event"] = Relationship(  # noqa: F821
        back_populates="promo",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": True,
        },
    )

    class Write(BaseModel):
        name: str
        code: str

        amount: condecimal(max_digits=8, decimal_places=2, gt=0)

        discount_type: DiscountType

        start_time: datetime
        end_time: datetime

    class Patch(BaseModel):
        name: Optional[str]
        code: Optional[str]

        amount: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]

        discount_type: Optional[DiscountType]

        start_time: Optional[datetime]
        end_time: Optional[datetime]

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        name: str
        code: str

        amount: condecimal(max_digits=8, decimal_places=2, gt=0)

        discount_type: DiscountType

        start_time: datetime
        end_time: datetime


class PaginatedPromos(BaseModel):
    items: list[Promo.Read]

    total: int
    pages: int

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID

from ..products.model import Product
from ..size.model import Size


class ProductGroup(SQLModel, table=True):
    __tablename__ = "product_group"

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

    auto_repair: bool
    transaction_number: int  # auto repair after this number of transactions (if auto_repair is true)

    charging_time: int
    one_to_one: bool

    id_org: UUID = Field(foreign_key="org.id")
    id_size: Optional[UUID] = Field(foreign_key="size.id")

    total_inventory: int
    products: List["Product"] = Relationship(
        back_populates="product_group",
        sa_relationship_kwargs={"lazy": "joined"},
    )

    size: Optional["Size"] = Relationship(
        back_populates="product_groups",
        sa_relationship_kwargs={"lazy": "joined"},
    )

    class Write(BaseModel):
        name: str
        auto_repair: Optional[bool] = False
        transaction_number: Optional[int] = 0
        charging_time: Optional[int] = 0
        one_to_one: Optional[bool] = False
        id_size: Optional[UUID] = None
        total_inventory: Optional[int] = 0
        products: Optional[List[UUID]] = []

    class Patch(BaseModel):
        name: Optional[str]
        auto_repair: Optional[bool]
        transaction_number: Optional[int]
        charging_time: Optional[int]
        one_to_one: Optional[bool]
        total_inventory: int
        id_size: Optional[UUID] = None

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        name: str
        auto_repair: bool
        transaction_number: int
        charging_time: int
        one_to_one: bool
        total_inventory: int
        products: Optional[List[Product.Read]]
        size: Optional[Size.Read]


class PaginatedProductGroups(BaseModel):
    items: list[ProductGroup.Read]
    total: int
    pages: int

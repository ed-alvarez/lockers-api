from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, condecimal, constr
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID
from util.form import as_form

from ..conditions.model import Condition
from ..device.model import Device
from ..product_tracking.product_tracking import ProductTracking
from .condition import ProductCondition


class Product(SQLModel, table=True):
    __tablename__ = "product"

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

    image: Optional[str]
    name: str
    description: Optional[str]

    price: condecimal(max_digits=8, decimal_places=2, gt=0)
    sales_price: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]
    sku: Optional[str]
    msrp: Optional[str]
    serial_number: Optional[str]

    id_condition: Optional[UUID] = Field(foreign_key="condition.id")
    condition: ProductCondition = ProductCondition.new

    repair_on_broken: bool = False
    report_on_broken: bool = False

    id_org: UUID = Field(foreign_key="org.id")
    id_product_group: Optional[UUID] = Field(foreign_key="product_group.id")

    product_condition: Optional["Condition"] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"lazy": "joined", "join_depth": 1},
    )

    devices: List["Device"] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"lazy": "joined", "join_depth": 1},
    )

    product_group: Optional["ProductGroup"] = Relationship(  # noqa: F821
        back_populates="products",
        sa_relationship_kwargs={"lazy": "noload"},
    )

    product_tracking: List["ProductTracking"] = Relationship(
        back_populates="product",
        # sa_relationship_kwargs={"lazy": "joined", "join_depth": 1},
    )

    reservation: Optional["Reservation"] = Relationship(  # noqa: F821
        back_populates="product",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": False,
        },
    )

    @as_form
    class Write(BaseModel):
        name: str
        description: Optional[str]
        price: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]
        sales_price: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]
        sku: Optional[str] = ""
        msrp: Optional[str] = ""
        serial_number: Optional[constr(strip_whitespace=True)]
        condition: ProductCondition = ProductCondition.new
        id_condition: Optional[UUID] = None
        repair_on_broken: Optional[bool] = False
        report_on_broken: Optional[bool] = False
        id_product_group: Optional[UUID] = None

    class Patch(BaseModel):
        name: Optional[str]
        price: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]
        description: Optional[str]
        sku: Optional[str]
        msrp: Optional[str]
        serial_number: Optional[str]
        condition: Optional[ProductCondition]
        id_condition: Optional[UUID] = None
        repair_on_broken: Optional[bool]
        report_on_broken: Optional[bool]
        id_product_group: Optional[UUID] = None

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        image: Optional[str]
        name: str
        description: Optional[str]
        price: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]
        sales_price: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]
        sku: Optional[str]
        msrp: Optional[str]
        serial_number: Optional[str]
        condition: ProductCondition
        repair_on_broken: bool
        report_on_broken: bool
        id_product_group: Optional[UUID] = None

        devices: Optional[List[Device.Read]]

        product_tracking: Optional[List[ProductTracking.Read]]
        product_condition: Optional[Condition.Read]


class PaginatedProducts(BaseModel):
    items: list[Product.Read]
    total: int
    pages: int

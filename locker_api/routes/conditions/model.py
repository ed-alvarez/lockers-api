import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from ..device.model import Device


class Condition(SQLModel, table=True):
    __tablename__ = "condition"

    id: uuid.UUID = Field(primary_key=True, unique=True, default_factory=uuid.uuid4)

    created_at: datetime = Field(
        sa_column=Column(
            "created_at",
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
            nullable=False,
        )
    )

    name: str

    auto_report: bool
    auto_maintenance: bool

    id_org: uuid.UUID = Field(foreign_key="org.id")

    devices: list["Device"] = Relationship(
        back_populates="condition",
        sa_relationship_kwargs={"lazy": "joined", "join_depth": 1},
    )

    product: Optional["Product"] = Relationship(  # noqa: F821
        back_populates="product_condition",
        sa_relationship_kwargs={
            "lazy": "noload",
        },
    )

    product_tracking: Optional["ProductTracking"] = Relationship(  # noqa: F821
        back_populates="condition",
        sa_relationship_kwargs={
            "lazy": "noload",
        },
    )

    class Write(BaseModel):
        name: str

        auto_report: bool
        auto_maintenance: bool

        devices: Optional[list[uuid.UUID]]

    class Patch(BaseModel):
        name: Optional[str]

        auto_report: Optional[bool]
        auto_maintenance: Optional[bool]

        devices: Optional[list[uuid.UUID]]

    class Read(BaseModel):
        id: uuid.UUID
        created_at: datetime

        name: str

        auto_report: bool
        auto_maintenance: bool

        devices: Optional[list[Device.Read]]


class PaginatedConditions(BaseModel):
    items: list[Condition.Read]

    total: int
    pages: int

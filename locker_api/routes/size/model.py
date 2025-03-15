from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, condecimal
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID
from pydantic import AnyHttpUrl


class Size(SQLModel, table=True):
    __tablename__ = "size"

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

    name: str
    external_id: Optional[str]
    description: Optional[str]
    image: Optional[AnyHttpUrl] = None

    width: condecimal(max_digits=8, decimal_places=4, gt=0)
    depth: condecimal(max_digits=8, decimal_places=4, gt=0)
    height: condecimal(max_digits=8, decimal_places=4, gt=0)

    id_org: UUID = Field(foreign_key="org.id")

    devices: list["Device"] = Relationship(  # noqa: F821
        back_populates="size",
        sa_relationship_kwargs={"lazy": "noload"},
    )

    product_groups: list["ProductGroup"] = Relationship(  # noqa: F821
        back_populates="size",
        sa_relationship_kwargs={"lazy": "noload"},
    )

    reservation: Optional["Reservation"] = Relationship(  # noqa: F821
        back_populates="size",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": False,
        },
    )

    class Write(BaseModel):
        name: str
        external_id: Optional[str]
        description: Optional[str]
        image: Optional[AnyHttpUrl]

        width: condecimal(max_digits=8, decimal_places=4, gt=0)
        depth: condecimal(max_digits=8, decimal_places=4, gt=0)
        height: condecimal(max_digits=8, decimal_places=4, gt=0)

    class Patch(BaseModel):
        name: Optional[str]
        external_id: Optional[str]
        description: Optional[str]
        image: Optional[AnyHttpUrl]

        width: Optional[condecimal(max_digits=8, decimal_places=4, gt=0)]
        depth: Optional[condecimal(max_digits=8, decimal_places=4, gt=0)]
        height: Optional[condecimal(max_digits=8, decimal_places=4, gt=0)]

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        name: str
        external_id: Optional[str]
        description: Optional[str]
        image: Optional[AnyHttpUrl]

        width: float
        depth: float
        height: float

        class Config:
            orm_mode = True

    class ReadWithDevices(BaseModel):
        id: UUID

        name: str
        external_id: Optional[str]
        description: Optional[str]
        image: Optional[AnyHttpUrl]
        width: float
        depth: float
        height: float

        available_devices: int


class PaginatedSizes(BaseModel):
    items: list[Size.Read]

    total: int
    pages: int

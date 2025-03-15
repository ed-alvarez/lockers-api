from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, conint, constr
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from ..device.model import Device


class Locker(BaseModel):
    x: conint(ge=0)
    y: conint(ge=0)

    id: Optional[str] = None
    kiosk: bool = False


class LockerWall(SQLModel, table=True):
    __tablename__ = "locker_wall"

    id: UUID = Field(primary_key=True)
    created_at: datetime

    image: Optional[AnyHttpUrl] = None
    name: str
    description: Optional[str]

    custom_id: Optional[str] = None

    qty_wide: conint(gt=0)  # x
    qty_tall: conint(gt=0)  # y

    is_kiosk: bool = False

    lockers: List[Locker] = Field(
        sa_column=Column(
            "lockers",
            JSON(),
            nullable=False,
        )
    )

    id_org: UUID = Field(foreign_key="org.id")
    id_location: Optional[UUID] = Field(foreign_key="location.id")

    devices: list["Device"] = Relationship(
        back_populates="locker_wall",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )

    class Write(BaseModel):
        name: str
        image: Optional[
            AnyHttpUrl
        ] = "https://koloni-org-data.s3.amazonaws.com/bc6647fb-90d8-4c79-87e9-9b6942383e4a/fceab2de675e4f87a2187e26e1f3bfa5.png"
        description: Optional[str]
        qty_wide: conint(gt=0)
        qty_tall: conint(gt=0)

        custom_id: Optional[constr(max_length=150)] = None

        is_kiosk: bool = False

        id_location: Optional[UUID] = None

        lockers: List[Locker] = Field(
            schema_extra={
                "example": [
                    {
                        "x": 1,
                        "y": 1,
                        "id": "e3d6b8d9-4f6d-4e3a-8b5e-1c9c5c8a0b1e",
                        "kiosk": False,
                    },
                    {
                        "x": 2,
                        "y": 1,
                        "id": None,
                        "kiosk": True,
                    },
                ],
            }
        )

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        image: Optional[AnyHttpUrl] = None
        name: str
        description: Optional[str]

        custom_id: Optional[str] = None

        qty_wide: conint(gt=0)
        qty_tall: conint(gt=0)

        is_kiosk: bool = False

        id_location: Optional[UUID] = None

        lockers: List[Locker] = Field(
            schema_extra={
                "example": [
                    {
                        "x": 1,
                        "y": 1,
                        "id": "e3d6b8d9-4f6d-4e3a-8b5e-1c9c5c8a0b1e",
                        "kiosk": False,
                    },
                    {
                        "x": 2,
                        "y": 1,
                        "id": None,
                        "kiosk": True,
                    },
                ],
            }
        )
        devices: Optional[List[Device.Read]]


class PaginatedLockerWalls(BaseModel):
    items: list[LockerWall.Read]

    total: int
    pages: int

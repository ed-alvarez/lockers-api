from typing import Optional
from uuid import UUID

from pydantic import constr
from sqlalchemy import Column, func
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID


class HarborEvents(SQLModel, table=True):
    __tablename__ = "harbor_events"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID,
            server_default=func.gen_random_uuid(),
            primary_key=True,
            unique=True,
        )
    )

    tower_id: str = Field(nullable=False)
    locker_id: str = Field(nullable=False)
    pin_code: Optional[constr(regex=r"\d{4}")] = Field(nullable=True)
    status: str = Field(nullable=False)

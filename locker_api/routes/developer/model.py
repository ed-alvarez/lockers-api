from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_key"

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

    key: str = Field(unique=True)
    active: bool = Field(default=True)

    id_org: UUID = Field(foreign_key="org.id")

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        key: str
        active: bool

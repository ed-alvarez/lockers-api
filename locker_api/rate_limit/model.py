from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, func
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID


class RateLimit(SQLModel, table=True):
    __tablename__ = "rate_limits"

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

    ip: str = Field(sa_column=Column("ip", String, unique=True, index=True))
    requests: int = Field(sa_column=Column("requests", Integer, default=0))
    timestamp: datetime = Field(sa_column=Column("timestamp", DateTime(timezone=True)))
    exceed_count: int = Field(
        sa_column=Column("exceed_count", Integer, default=0)
    )  # <-- new field

    class Write(BaseModel):
        ip: str
        requests: int
        timestamp: datetime
        exceed_count: int  # <-- new field

    class Read(BaseModel):
        id: UUID
        ip: str
        requests: int
        timestamp: datetime
        created_at: datetime
        exceed_count: int  # <-- new field

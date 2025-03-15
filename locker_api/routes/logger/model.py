from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, func
from sqlmodel.sql.sqltypes import GUID

from ..event.model import Event


class LogType(Enum):
    lock = "lock"
    unlock = "unlock"
    maintenance = "maintenance"
    report_issue = "report_issue"


class Log(SQLModel, table=True):
    __tablename__ = "log"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID(),
            server_default=func.gen_random_uuid(),
            unique=True,
            primary_key=True,
        )
    )
    created_at: datetime

    log_type: LogType
    log_owner: Optional[str]

    id_org: UUID = Field(foreign_key="org.id")
    id_event: Optional[UUID] = Field(foreign_key="event.id", nullable=True)
    id_device: Optional[UUID] = Field(foreign_key="device.id", nullable=True)

    event: Optional["Event"] = Relationship(
        back_populates="log",
        sa_relationship_kwargs={"lazy": "joined", "join_depth": 1},
    )

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        log_type: LogType
        log_owner: Optional[str]

        event: Optional[Event.Read]

    class Write(BaseModel):
        log_type: LogType
        log_owner: Optional[str]
        id_event: Optional[UUID]
        id_device: Optional[UUID]

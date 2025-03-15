from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, func
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID

from ..event.model import Event, EventStatus


class WebhookStatus(Enum):
    ok = "ok"  # Endpoint is working and returning 200
    error = "error"  # Endpoint is reachable but not working, returning 500 or 404
    inactive = "inactive"  # Endpoint has not been tested yet, or connection failed


class Webhook(SQLModel, table=True):
    __tablename__ = "webhook"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID,
            server_default=func.gen_random_uuid(),
            primary_key=True,
            unique=True,
        )
    )

    url: str
    signature_key: str
    status: WebhookStatus = Field(default=WebhookStatus.inactive)

    id_org: UUID = Field(foreign_key="org.id")

    class Write(BaseModel):
        url: str

    class Read(BaseModel):
        id: UUID

        url: str
        signature_key: str
        status: WebhookStatus


class EventChange(BaseModel):
    id_event: UUID
    id_org: Optional[UUID]

    event_status: EventStatus | str

    event_obj: Optional[Event.Read]

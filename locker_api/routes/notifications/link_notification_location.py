# Purpose: SQLAlchemy model for link_notification_location table.
from uuid import UUID

from sqlalchemy import Column, func
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID


class LinkNotificationLocation(SQLModel, table=True):
    __tablename__ = "link_notification_location"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID(),
            server_default=func.gen_random_uuid(),
            unique=True,
            primary_key=True,
        )
    )

    id_notification: UUID = Field(foreign_key="notification.id")
    id_location: UUID = Field(foreign_key="location.id")

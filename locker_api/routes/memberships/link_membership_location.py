# Purpose: SQLAlchemy model for link_membership_location table.
from uuid import UUID

from sqlalchemy import Column, func
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID


class LinkMembershipLocation(SQLModel, table=True):
    __tablename__ = "link_membership_location"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID(),
            server_default=func.gen_random_uuid(),
            unique=True,
            primary_key=True,
        )
    )

    id_membership: UUID = Field(foreign_key="memberships.id")
    id_location: UUID = Field(foreign_key="location.id")

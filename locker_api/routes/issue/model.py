from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID, AutoString
from util.form import as_form

from ..event.model import Event
from ..user.model import User
from ..member.model import Member


class IssueStatus(Enum):
    pending = "pending"
    in_progress = "in_progress"
    resolved = "resolved"


class Issue(SQLModel, table=True):
    __tablename__ = "issue"

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

    issue_id: Optional[str]

    description: str
    pictures: Optional[list[str]] = Field(
        sa_column=Column(ARRAY(AutoString), nullable=True)
    )

    status: IssueStatus = Field(default=IssueStatus.pending)

    team_member_id: Optional[UUID] = Field(default=None, nullable=True)

    id_org: UUID = Field(foreign_key="org.id")
    id_user: Optional[UUID] = Field(foreign_key="User.id")
    id_event: Optional[UUID] = Field(foreign_key="event.id", nullable=True)

    user: Optional["User"] = Relationship(
        back_populates="issues", sa_relationship_kwargs={"lazy": "joined"}
    )

    event: Optional["Event"] = Relationship(
        back_populates="issue",
        sa_relationship_kwargs={"lazy": "joined", "join_depth": 1},
    )

    class Read(BaseModel):
        id: UUID
        created_at: datetime

        issue_id: Optional[str]

        description: str
        pictures: Optional[list[str]]

        status: IssueStatus

        team_member_id: Optional[UUID]
        team_member: Optional[Member]

        id_user: Optional[UUID]
        id_event: Optional[UUID]

        user: Optional[User.Read]
        event: Optional[Event.Read]

    @as_form
    class Write(BaseModel):
        team_member_id: Optional[UUID]

        description: str
        status: IssueStatus = Field(default=IssueStatus.pending)
        id_user: Optional[UUID]


class PaginatedIssues(BaseModel):
    items: list[Issue.Read]

    total: int
    pages: int

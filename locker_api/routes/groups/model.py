from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from ..location.model import Location
from ..user.model import User


class ResourceType(Enum):
    location = "location"
    device = "device"


class AssignmentType(Enum):
    user = "user"
    group = "group"


class Groups(SQLModel, table=True):
    __tablename__ = "groups"

    id: UUID = Field(primary_key=True)

    created_at: datetime
    name: str

    id_org: UUID = Field(foreign_key="org.id")

    class Read(BaseModel):
        id: UUID
        created_at: datetime
        name: str

        users: list[User.Read]
        devices: int
        locations: list[Location.Read]


class PaginatedGroups(BaseModel):
    items: list[Groups.Read]

    total: int
    pages: int


class LinkGroupsUser(SQLModel, table=True):
    __tablename__ = "link_groups_user"

    id: UUID = Field(primary_key=True)

    id_group: UUID = Field(foreign_key="groups.id")
    id_user: UUID = Field(foreign_key="User.id")


class LinkGroupsLocations(SQLModel, table=True):
    __tablename__ = "link_groups_locations"

    id: UUID = Field(primary_key=True)

    id_group: UUID = Field(foreign_key="groups.id")
    id_location: UUID = Field(foreign_key="location.id")


class LinkGroupsDevices(SQLModel, table=True):
    __tablename__ = "link_groups_devices"

    id: UUID = Field(primary_key=True)

    id_group: UUID = Field(foreign_key="groups.id")
    id_device: UUID = Field(foreign_key="device.id")


class LinkUserDevices(SQLModel, table=True):
    __tablename__ = "link_user_devices"

    id: UUID = Field(primary_key=True)

    id_user: UUID = Field(foreign_key="User.id")
    id_device: UUID = Field(foreign_key="device.id")


class LinkUserLocations(SQLModel, table=True):
    __tablename__ = "link_user_locations"

    id: UUID = Field(primary_key=True)

    id_user: UUID = Field(foreign_key="User.id")
    id_location: UUID = Field(foreign_key="location.id")

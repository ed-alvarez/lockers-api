import datetime
from enum import Enum
from typing import List, Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, constr, conint

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID
from ..member.model import Member

EMAIL_BODY = """
    Greetings {user_name},
    <br>
    <br>
    Attached to this email, you will find the latest automated report in CSV format titled "{report_version}".
    <br>
    <br>
    This report contains comprehensive data and analysis regarding the performance of your Organization.
    <br>
    <br>
    Key insights and findings from the report include:
    {report_contents}
    <br>
    <br>
    Koloni
"""


class Recurrence(Enum):
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"
    bimonthly = "bimonthly"


class TimeFrame(Enum):
    start = "start"
    end = "end"


class Report(SQLModel, table=True):
    __tablename__ = "report"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID,
            server_default=func.gen_random_uuid(),
            primary_key=True,
            unique=True,
        )
    )

    created_at: datetime.datetime = Field(
        sa_column=Column(
            "created_at",
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
            nullable=False,
        )
    )

    name: str
    version: Optional[str]
    contents: List[str] = Field(sa_column=Column("contents", ARRAY(VARCHAR)))
    assign_to: List[UUID] = Field(sa_column=Column("assign_to", ARRAY(GUID)))

    recurrence: Optional[str]

    weekday: Optional[int]
    month: Optional[int]

    when: Optional[str]
    include_sub_orgs: bool

    send_time: Annotated[
        str, constr(regex=r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")
    ] = Field(nullable=False)
    last_sent: Optional[datetime.datetime]
    last_content: List[str]

    target_org: Optional[UUID] = Field(foreign_key="org.id")
    id_org: UUID = Field(foreign_key="org.id")

    class Read(BaseModel):
        id: UUID
        created_at: datetime.datetime

        name: str
        version: Optional[str]
        contents: List[str]
        assign_to: List[UUID]
        assignees: List[Member | None] = []

        recurrence: Optional[str]

        weekday: Optional[int]
        month: Optional[int]

        when: Optional[str]
        include_sub_orgs: bool

        send_time: str
        last_sent: Optional[datetime.datetime]

        target_org: Optional[UUID]

    class Write(BaseModel):
        name: str
        contents: List[str] = Field(default=["transactions", "top_locations"])
        assign_to: List[UUID]

        recurrence: Optional[Recurrence] = None

        weekday: Optional[Annotated[int, conint(ge=0, lt=7)]] = 0
        month: Optional[Annotated[int, conint(gt=0, lt=13)]]

        when: Optional[TimeFrame] = TimeFrame.start
        include_sub_orgs: Optional[bool] = False

        send_time: Annotated[
            str, constr(regex=r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")
        ] = "00:00"

        target_org: Optional[UUID]


class PaginatedReports(BaseModel):
    items: List[Report.Read]

    total: int
    pages: int


class TransactionsData(BaseModel):
    month: int
    count: int


class Percentage(BaseModel):
    percentage: int


class Occupancy(BaseModel):
    id: UUID
    name: str
    address: str
    occupancy_rate: float


class User(BaseModel):
    id: UUID
    created_at: datetime.datetime

    name: str
    email: Optional[str]
    phone_number: Optional[str]
    active: bool


class TopUsers(BaseModel):
    User: User
    location: str
    purchases: float


class Earnings(BaseModel):
    earnings: int
    currency: str


class Graph(BaseModel):
    total: int
    data: list[TransactionsData]


class Location(BaseModel):
    id: UUID
    name: str
    address: str


class TopLocations(BaseModel):
    Location: Location
    count: int


class LocationBreakdown(BaseModel):
    location_id: UUID
    total_issues: int
    total_transactions: int
    issue_rate: float


class IssueRate(BaseModel):
    total_issues: int
    total_transactions: int
    issue_rate: float
    locations_breakdown: List[LocationBreakdown]


class NewTransactionPercentageResponse(BaseModel):
    new_transactions: int
    new_transaction_percentage: float


class SystemHealthResponse(BaseModel):
    location_id: Optional[UUID]
    total_devices: int
    unhealthy_devices: int
    health_percentage: float


class Summary(BaseModel):
    earnings: Earnings
    users: Graph
    transactions: Graph
    top_users: list[TopUsers]
    top_locations: list[TopLocations]

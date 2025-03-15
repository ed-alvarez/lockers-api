from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, constr
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID
from util.form import as_form


class WhiteLabel(SQLModel, table=True):
    __tablename__ = "white_label"

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

    image_key: Optional[str] = Field(nullable=True)

    app_logo: Optional[str] = Field(nullable=True)
    app_name: str = Field(nullable=False)

    primary_color: str = Field(nullable=False)
    secondary_color: str = Field(nullable=False)
    tertiary_color: str = Field(nullable=True)

    link_text_color: str = Field(nullable=False)
    button_text_color: str = Field(nullable=False)

    privacy_policy: str = Field(nullable=False)
    user_agreement: str = Field(nullable=False)
    terms_condition: str = Field(nullable=False)
    terms_name_2nd: str = Field(nullable=True)
    terms_condition_2nd: str = Field(nullable=True)

    organization_owner: str = Field(nullable=True)

    # Example
    # app_logo: http://example.url
    # app_name: Laundry App
    # primary_color: #ff6146
    # secondary_color: #ff6146
    # tertiary_color: #8A242A
    # link_text_color: #ff6146
    # button_text_color: #ffffff
    # privacy_policy: https://www.koloni.io/product/legal
    # user_agreement_url: https://www.koloni.io/product/legal
    # terms_condition_url: https://www.koloni.io/product/legal

    id_org: UUID = Field(foreign_key="org.id")

    org: Optional["Org"] = Relationship(  # noqa: F821
        back_populates="white_label",
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "noload",
        },
    )

    @as_form
    class Write(BaseModel):
        app_name: constr(regex=r"^[a-zA-Z0-9\s]+$")

        primary_color: str
        secondary_color: Optional[str] = ""
        tertiary_color: Optional[str] = ""
        link_text_color: Optional[str] = ""
        button_text_color: Optional[str] = ""

        privacy_policy: Optional[str] = "https://www.koloni.io/legal/privacy"
        user_agreement: Optional[str] = "https://www.koloni.io/legal/eula"
        terms_condition: Optional[str] = "https://www.koloni.io/legal/legal"
        terms_name_2nd: Optional[str]
        terms_condition_2nd: Optional[str] = None

        organization_owner: Optional[str]

    class Patch(BaseModel):
        app_name: Optional[constr(regex=r"^[a-zA-Z0-9\s]+$")]
        primary_color: Optional[str]
        secondary_color: Optional[str]
        tertiary_color: Optional[str]
        link_text_color: Optional[str]
        button_text_color: Optional[str]

        privacy_policy: Optional[str]
        user_agreement: Optional[str]
        terms_condition: Optional[str]
        terms_name_2nd: Optional[str]
        terms_condition_2nd: Optional[str]

    class Read(BaseModel):
        id: Optional[UUID]
        created_at: Optional[datetime]
        image_key: Optional[str]

        app_logo: Optional[str]
        app_name: Optional[str]

        primary_color: Optional[str]
        secondary_color: Optional[str]
        tertiary_color: Optional[str]
        link_text_color: Optional[str]
        button_text_color: Optional[str]

        privacy_policy: Optional[str]
        user_agreement: Optional[str]
        terms_condition: Optional[str]
        terms_name_2nd: Optional[str]
        terms_condition_2nd: Optional[str]

        organization_owner: Optional[str]

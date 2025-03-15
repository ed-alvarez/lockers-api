from uuid import UUID

from sqlalchemy import Column, func
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID


class LinkDevicePrice(SQLModel, table=True):
    __tablename__ = "link_device_price"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID(),
            server_default=func.gen_random_uuid(),
            unique=True,
            primary_key=True,
        )
    )

    id_device: UUID = Field(foreign_key="device.id")
    id_price: UUID = Field(foreign_key="price.id")

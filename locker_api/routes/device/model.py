from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, condecimal, constr
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.sql.sqltypes import GUID
from util.form import as_form

from ..price.model import Price
from ..products.condition import ProductCondition
from ..size.model import Size
from .link_device_price import LinkDevicePrice


class LocationRead(BaseModel):
    id: UUID
    created_at: datetime

    name: str
    custom_id: Optional[str]
    address: str
    image: Optional[str]

    hidden: bool
    shared: bool

    latitude: condecimal(max_digits=18, decimal_places=15)
    longitude: condecimal(max_digits=18, decimal_places=15)

    contact_email: Optional[str]
    contact_phone: Optional[str]

    restrict_by_user_code: Optional[bool]
    verify_pin_code: Optional[bool]
    verify_qr_code: Optional[bool]
    verify_url: Optional[bool]

    email: Optional[bool]
    phone: Optional[bool]

    available_devices: int = 0
    reserved_devices: int = 0
    maintenance_devices: int = 0

    price: Optional[Price.Read]


class ProductRead(BaseModel):
    id: UUID
    created_at: datetime

    image: Optional[str]
    name: str
    description: Optional[str]
    price: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]
    sales_price: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)]
    sku: Optional[str]
    msrp: Optional[str]
    serial_number: Optional[str]
    condition: ProductCondition
    repair_on_broken: bool
    report_on_broken: bool


class ConditionRead(BaseModel):
    id: UUID
    created_at: datetime

    name: str
    auto_report: bool
    auto_maintenance: bool
    transaction_number: int


class HardwareType(Enum):
    linka = "linka"
    spintly = "spintly"
    ojmar = "ojmar"
    keynius = "keynius"  # TODO: Remove this
    gantner = "gantner"
    harbor = "harbor"
    dclock = "dclock"
    virtual = "virtual"  # This is used for testing


class Mode(Enum):
    service = "service"
    storage = "storage"
    rental = "rental"
    delivery = "delivery"
    vending = "vending"


class LockStatus(Enum):
    open = "open"
    locked = "locked"
    unknown = "unknown"
    offline = "offline"
    closed = "closed"


class Status(Enum):
    available = "available"
    reserved = "reserved"
    maintenance = "maintenance"
    expired = "expired"


class RestrictionType(Enum):
    groups = "groups"
    users = "users"


class Restriction(BaseModel):
    restriction_type: RestrictionType
    items: list


class Device(SQLModel, table=True):
    __tablename__ = "device"

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

    name: str
    custom_identifier: Optional[str] = Field(nullable=True)
    item: str = Field(nullable=True)
    item_description: Optional[str] = Field(nullable=True)
    image: Optional[str] = Field(nullable=True)

    locker_number: int = Field(nullable=True)
    shared: bool
    require_image: bool
    mode: Mode = Field(default=Mode.service)

    status: Status = Field(default=Status.available)

    hardware_type: HardwareType = Field(default=HardwareType.linka)

    lock_status: Optional[LockStatus] = Field(nullable=False, default="unknown")
    price_required: bool = Field(default=False, nullable=False)

    transaction_count: int = Field(default=0, nullable=False)

    # Linka specific
    mac_address: str = Field(nullable=True)

    # Spintly specific
    integration_id: int = Field(nullable=True)

    # Ojmar specific
    locker_udn: str = Field(nullable=True)
    user_code: constr(regex=r"^[0-9]{4}$") = Field(nullable=True)
    master_code: str = Field(nullable=True)

    # Gantner specific
    # Combination of AN-SN-LN (e.g. 01101689-2248070013-02).
    # AN = Article Number
    # SN = Serial Number of GC7 controller
    # LN = Lock Number (01-24)
    gantner_id: str = Field(nullable=True)

    # Keynius specific
    # This is simply a UUID used to communicate with the Keynius REST API.
    keynius_id: str = Field(nullable=True)

    # Harbor specific
    harbor_tower_id: str = Field(nullable=True)
    harbor_locker_id: str = Field(nullable=True)

    # DCLock specific
    # Terminal No: DC21071701247878
    # Box No: This can go from 1 to 24
    dclock_terminal_no: str = Field(nullable=True)
    dclock_box_no: str = Field(nullable=True)

    # FKs go here
    id_location: Optional[UUID] = Field(foreign_key="location.id", nullable=True)
    id_size: Optional[UUID] = Field(foreign_key="size.id", nullable=True)
    id_price: Optional[UUID] = Field(foreign_key="price.id", nullable=True)
    id_product: Optional[UUID] = Field(foreign_key="product.id")
    id_condition: Optional[UUID] = Field(foreign_key="condition.id", nullable=True)
    id_locker_wall: Optional[UUID] = Field(foreign_key="locker_wall.id", nullable=True)
    id_org: UUID = Field(foreign_key="org.id")

    location: Optional["Location"] = Relationship(  # noqa: F821
        back_populates="devices",
        sa_relationship_kwargs={
            "lazy": "joined",
            "uselist": False,
        },
    )

    size: Optional["Size"] = Relationship(
        back_populates="devices",
        sa_relationship_kwargs={
            "lazy": "joined",
            "uselist": False,
        },
    )

    price: Optional["Price"] = Relationship(
        back_populates="devices",
        sa_relationship_kwargs={
            "lazy": "joined",
            "uselist": False,
        },
    )

    prices: list["Price"] = Relationship(
        back_populates="devices_list",
        link_model=LinkDevicePrice,
        sa_relationship_kwargs={
            "lazy": "joined",
            "uselist": True,
        },
    )

    product: Optional["Product"] = Relationship(  # noqa: F821
        back_populates="devices",
        sa_relationship_kwargs={
            "lazy": "joined",
            "uselist": False,
        },
    )

    events: list["Event"] = Relationship(  # noqa: F821
        back_populates="device",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": True,
        },
    )

    locker_wall: Optional["LockerWall"] = Relationship(  # noqa: F821
        back_populates="devices",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": False,
        },
    )

    product_tracking: list["ProductTracking"] = Relationship(  # noqa: F821
        back_populates="device",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": True,
        },
    )

    condition: Optional["Condition"] = Relationship(  # noqa: F821
        back_populates="devices",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": False,
        },
    )

    reservation: Optional["Reservation"] = Relationship(  # noqa: F821
        back_populates="device",
        sa_relationship_kwargs={
            "lazy": "noload",
            "uselist": False,
        },
    )

    @as_form
    class Write(BaseModel):
        name: str
        custom_identifier: Optional[str]
        item: Optional[str]
        item_description: Optional[str]

        locker_number: Optional[int]
        mode: Mode = Mode.service
        shared: Optional[bool] = False
        require_image: Optional[bool] = False
        status: Status = Status.available

        hardware_type: HardwareType = HardwareType.linka

        # Linka specific
        mac_address: Optional[str]

        # Spintly specific
        integration_id: Optional[int]

        # Ojmar specific
        locker_udn: Optional[str]
        user_code: Optional[constr(regex=r"^[0-9]{4}$")]
        master_code: Optional[constr(regex=r"^[0-9]*$")]

        # Gantner specific
        gantner_id: Optional[str]

        # Keynius specific
        keynius_id: Optional[str]

        # Harbor specific
        harbor_tower_id: Optional[str]
        harbor_locker_id: Optional[str]

        # DCLock specific
        # Terminal No: DC21071701247878
        # Box No: This can go from 1 to 24
        dclock_terminal_no: Optional[str]
        dclock_box_no: Optional[str]

        price_required: bool

        id_location: Optional[UUID]
        id_size: Optional[UUID]
        id_price: Optional[UUID]
        id_product: Optional[UUID]
        id_condition: Optional[UUID]

    class WriteCSV(BaseModel):
        name: str
        custom_identifier: Optional[str]

        locker_number: Optional[int]
        mode: Mode = Mode.service
        status: Status = Status.available

        hardware_type: HardwareType = HardwareType.linka
        # Linka specific
        mac_address: Optional[str]

        # Spintly specific
        integration_id: Optional[int]

        # Ojmar specific
        locker_udn: Optional[str]
        user_code: Optional[constr(regex=r"^[0-9]{4}$")]
        master_code: Optional[constr(regex=r"^[0-9]*$")]

        # Gantner specific
        gantner_id: Optional[str]

        # Keynius specific
        keynius_id: Optional[str]

        # Harbor specific
        harbor_tower_id: Optional[str]
        harbor_locker_id: Optional[str]

        # DCLock specific
        # Terminal No: DC21071701247878
        # Box No: This can go from 1 to 24
        dclock_terminal_no: Optional[str]
        dclock_box_no: Optional[str]

        price_required: bool

        location: Optional[str]
        size: Optional[str]
        price: Optional[str]
        product: Optional[str]
        group: Optional[str]

    class Patch(BaseModel):
        name: Optional[str]
        custom_identifier: Optional[str]
        item: Optional[str]
        item_description: Optional[str]
        locker_number: Optional[int]
        mode: Optional[Mode]
        shared: Optional[bool]
        require_image: Optional[bool]
        status: Optional[Status]
        hardware_type: Optional[HardwareType]
        # Linka specific
        mac_address: Optional[str]
        # Spintly specific
        integration_id: Optional[int]
        # Ojmar specific
        locker_udn: Optional[str]
        user_code: Optional[constr(regex=r"^[0-9]{4}$")]
        master_code: Optional[constr(regex=r"^[0-9]*$")]
        # Gantner specific
        gantner_id: Optional[str]
        # Keynius specific
        keynius_id: Optional[str]
        # Harbor specific
        harbor_tower_id: Optional[str]
        harbor_locker_id: Optional[str]
        # DCLock specific
        # Terminal No: DC21071701247878
        # Box No: This can go from 1 to 24
        dclock_terminal_no: Optional[str]
        dclock_box_no: Optional[str]

        id_location: Optional[UUID]
        id_size: Optional[UUID]
        id_price: Optional[UUID]
        id_product: Optional[UUID]
        id_condition: Optional[UUID]

    class Read(BaseModel):
        def __init__(self, **data):
            if data.get("locker_udn"):
                data["ojmar_id"] = data["locker_udn"]
            super().__init__(**data)

        id: UUID
        created_at: datetime

        name: str
        custom_identifier: Optional[str]
        item: Optional[str]
        item_description: Optional[str]
        image: Optional[str]

        locker_number: Optional[int]
        mode: Mode
        shared: bool
        require_image: bool
        status: Status

        hardware_type: HardwareType

        # Linka specific
        mac_address: Optional[str]

        # Spintly specific
        integration_id: Optional[int]

        # Ojmar specific
        locker_udn: Optional[str]
        ojmar_id: Optional[str]
        user_code: Optional[constr(regex=r"^[0-9]{4}$")]
        master_code: Optional[str]

        # Gantner specific
        gantner_id: Optional[str]

        # Keynius specific
        keynius_id: Optional[str]

        # Harbor specific
        harbor_tower_id: Optional[str]
        harbor_locker_id: Optional[str]

        # DCLock specific
        # Terminal No: DC21071701247878
        # Box No: This can go from 1 to 24
        dclock_terminal_no: Optional[str]
        dclock_box_no: Optional[str]

        # Restriction
        restriction: Optional[Restriction]

        price_required: bool

        id_location: Optional[UUID]
        id_size: Optional[UUID]
        id_price: Optional[UUID]
        id_product: Optional[UUID]
        id_condition: Optional[UUID]

        location: Optional[LocationRead]
        size: Optional[Size.Read]
        price: Optional[Price.Read]
        product: Optional[ProductRead]
        lock_status: Optional[LockStatus]
        condition: Optional[ConditionRead]

        prices: Optional[list[Price.Read]]


class PaginatedDevices(BaseModel):
    items: list[Device.Read]

    total: int
    pages: int


class PublicDevice(BaseModel):
    name: str
    custom_identifier: Optional[str]
    item: Optional[str]
    item_description: Optional[str]
    image: Optional[str]

    locker_number: int
    status: Status

    location: Optional[LocationRead]
    size: Optional[Size.Read]
    price: Optional[Price.Read]

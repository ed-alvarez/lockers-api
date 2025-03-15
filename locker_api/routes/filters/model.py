import json
from enum import Enum
from uuid import UUID

from sqlalchemy import Column, func
from sqlmodel import Field, SQLModel
from sqlmodel.sql.sqltypes import GUID


class FilterType(Enum):
    reporting = "reporting"
    pay_per = "pay-per"
    subscriptions = "subscriptions"
    promo_codes = "promo-codes"
    locations = "locations"
    devices = "devices"
    sizes = "sizes"
    transactions = "transactions"
    users = "users"
    members = "members"
    groups = "groups"
    issues = "issues"
    notifications = "notifications"
    inventory = "inventory"
    product_groups = "product-groups"
    conditions = "conditions"
    reservations = "reservations"
    subscribers = "subscribers"


class OrgFilters(SQLModel, table=True):
    __tablename__ = "org_filters"

    id: UUID = Field(
        sa_column=Column(
            "id",
            GUID(),
            server_default=func.gen_random_uuid(),
            unique=True,
            primary_key=True,
        )
    )

    id_org: UUID = Field(foreign_key="org.id", nullable=False)

    # Filters are JSONB columns in the database
    reporting: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {
                    "value": "name",
                    "label": "Report Name",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "contents",
                    "label": "Contents",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "assignees",
                    "label": "Assignees",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "last_sent",
                    "label": "Last Sent",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "previous",
                    "label": "Previous",
                    "active": True,
                    "sortable": True,
                },
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    pay_per: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "name", "label": "Name", "active": True, "sortable": True},
                {
                    "value": "price_type",
                    "label": "Price Type",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "amount",
                    "label": "Amount",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "unit_amount",
                    "label": "Unit Amount",
                    "active": True,
                    "sortable": True,
                },
                {"value": "unit", "label": "Unit", "active": True, "sortable": True},
                {
                    "value": "prorated",
                    "label": "Prorated",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "card_on_file",
                    "label": "Card on file",
                    "active": True,
                    "sortable": True,
                },
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    subscriptions: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "name", "label": "Name", "active": True, "sortable": True},
                {
                    "value": "membership_type",
                    "label": "Membership Type",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "amount",
                    "label": "Amount",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "billing_type",
                    "label": "Billing Type",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "billing_period",
                    "label": "Billing Period",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "number_of_payments",
                    "label": "No. of Payments",
                    "active": True,
                    "sortable": True,
                },
                {"value": "value", "label": "Value", "active": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    promo_codes: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "name", "label": "Name", "active": True, "sortable": True},
                {"value": "code", "label": "Code", "active": True, "sortable": True},
                {
                    "value": "discount_type",
                    "label": "Discount Type",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "amount",
                    "label": "Amount",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "start_time",
                    "label": "Start Time",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "end_time",
                    "label": "End Time",
                    "active": True,
                    "sortable": True,
                },
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    locations: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "name", "label": "Name", "active": True, "sortable": True},
                {
                    "value": "no_of_devices",
                    "label": "No. of Devices",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "address",
                    "label": "Address",
                    "active": True,
                    "sortable": True,
                },
                {"value": "image", "label": "Image", "active": True},
                {"value": "hidden", "label": "Hidden", "active": True},
                {"value": "shared", "label": "Shared", "active": True},
                {"value": "qrCode", "label": "QR Code", "active": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    devices: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "name", "label": "Name", "active": True, "sortable": True},
                {
                    "value": "locker_number",
                    "label": "Locker Number",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "location",
                    "label": "Location",
                    "active": True,
                    "sortable": True,
                },
                {"value": "size", "label": "Size", "active": True, "sortable": True},
                {
                    "value": "hardware_type",
                    "label": "Hardware Type",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "status",
                    "label": "Status",
                    "active": True,
                    "sortable": True,
                },
                {"value": "state", "label": "State", "active": True, "sortable": True},
                {"value": "mode", "label": "Mode", "active": True, "sortable": True},
                {"value": "item", "label": "Item", "active": True},
                {"value": "qr_code", "label": "QR Code", "active": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    sizes: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "image", "label": "Image", "active": True},
                {"value": "name", "label": "Name", "active": True, "sortable": True},
                {"value": "width", "label": "Width", "active": True, "sortable": True},
                {"value": "depth", "label": "Depth", "active": True, "sortable": True},
                {
                    "value": "height",
                    "label": "Height",
                    "active": True,
                    "sortable": True,
                },
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    transactions: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {
                    "value": "invoice_id",
                    "label": "Invoice ID",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "order_id",
                    "label": "Order Number",
                    "active": True,
                    "sortable": True,
                },
                {"value": "action", "label": "Action", "active": True},
                {
                    "value": "user_phone",
                    "label": "User Phone",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "user_email",
                    "label": "User Email",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "device_name",
                    "label": "Device Name",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "locker_number",
                    "label": "Locker Number",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "location",
                    "label": "Location",
                    "active": True,
                    "sortable": True,
                },
                {"value": "mode", "label": "Mode", "active": True, "sortable": True},
                {
                    "value": "status",
                    "label": "Status",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "start_date",
                    "label": "Start Date",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "end_date",
                    "label": "End Date",
                    "active": True,
                    "sortable": True,
                },
                {"value": "duration", "label": "Duration", "active": True},
                {
                    "value": "refund",
                    "label": "Refund",
                    "active": True,
                    "sortable": True,
                },
                {"value": "amount", "label": "Amount", "active": True},
                {"value": "end", "label": "End", "active": True},
                {"value": "qr_code", "label": "QR Code", "active": True},
                {"value": "image", "label": "Image", "active": True},
            ]
        ),
        nullable=False,
    )

    subscribers: str = Field(
        default=json.dumps(
            [
                {
                    "value": "name",
                    "label": "User Name",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "price",
                    "label": "Price",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "expiration_date",
                    "label": "Expiry",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "recurring",
                    "label": "Recurring",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "membership_name",
                    "label": "Membership Name",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "no_of_transactions",
                    "label": "No. of transactions left",
                    "active": True,
                    "sortable": True,
                },
            ],
        ),
        nullable=False,
    )

    users: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "name", "label": "Name", "active": True, "sortable": True},
                {"value": "email", "label": "Email", "active": True, "sortable": True},
                {
                    "value": "address",
                    "label": "Address",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "phone_number",
                    "label": "Phone",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "user_id",
                    "label": "User ID",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "pin_code",
                    "label": "Pin Code",
                    "active": True,
                    "sortable": True,
                },
                {"value": "qr_code", "label": "QR Code", "active": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    members: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "email", "label": "Email", "active": True, "sortable": True},
                {
                    "value": "first_name",
                    "label": "First Name",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "last_name",
                    "label": "Last Name",
                    "active": True,
                    "sortable": True,
                },
                {"value": "role", "label": "Role", "active": True, "sortable": True},
                {
                    "value": "pin_code",
                    "label": "Pin Code",
                    "active": True,
                    "sortable": True,
                },
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    groups: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "name", "label": "Name", "active": True, "sortable": True},
                {"value": "users", "label": "Users", "active": True, "sortable": True},
                {
                    "value": "devices",
                    "label": "Devices",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "locations",
                    "label": "Locations",
                    "active": True,
                    "sortable": True,
                },
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    issues: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {
                    "value": "issueId",
                    "label": "Issue ID",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "userName",
                    "label": "User Name",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "orderNumber",
                    "label": "Order No.",
                    "active": True,
                    "sortable": True,
                },
                {"value": "status", "label": "Status", "active": True},
                {
                    "value": "reportTime",
                    "label": "Report Time",
                    "active": True,
                    "sortable": True,
                },
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    notifications: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "name", "label": "Name", "active": True},
                {"value": "mode", "label": "Mode", "active": True},
                {"value": "type", "label": "Type", "active": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    inventory: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "image", "label": "Image", "active": True},
                {
                    "value": "product_name",
                    "label": "Product Name",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "serial_number",
                    "label": "Serial Number",
                    "active": True,
                },
                {
                    "value": "assigned_locker",
                    "label": "Assigned Locker",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "assigned_location",
                    "label": "Assigned Location",
                    "active": True,
                    "sortable": True,
                },
                {"value": "cost", "label": "Cost", "active": True, "sortable": True},
                {
                    "value": "sale_price",
                    "label": "Sale",
                    "active": True,
                    "sortable": True,
                },
                {"value": "sku", "label": "ID/SKU", "active": True, "sortable": True},
                {"value": "msrp", "label": "MSRP", "active": True, "sortable": True},
                {"value": "groups", "label": "Groups", "active": True},
                {"value": "qr_code", "label": "QR Code", "active": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    product_groups: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {
                    "value": "group_name",
                    "label": "Group Name",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "locker_size",
                    "label": "Locker Size",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "total_inventory",
                    "label": "Total Inventory",
                    "active": True,
                    "sortable": True,
                },
                {"value": "sku", "label": "ID/SKU", "active": True},
                {"value": "qr_code", "label": "QR Code", "active": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    conditions: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {
                    "value": "condition",
                    "label": "Condition",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "devices_assigned",
                    "label": "Devices Assigned",
                    "active": True,
                    "sortable": True,
                },
                {"value": "maintenance", "label": "Maintenance", "active": True},
                {"value": "report_issue", "label": "Report Issue", "active": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )
    reservations: str = Field(
        default=json.dumps(
            [
                {"value": "select", "label": "Select", "active": True},
                {"value": "mode", "label": "Mode", "active": True},
                {
                    "value": "tracking_number",
                    "label": "Tracking Number",
                    "active": True,
                },
                {"value": "user", "label": "User", "active": True, "sortable": True},
                {
                    "value": "phone",
                    "label": "Phone Number",
                    "active": True,
                    "sortable": True,
                },
                {"value": "email", "label": "Email", "active": True, "sortable": True},
                {"value": "duration", "label": "Duration", "active": True},
                {"value": "date", "label": "Date", "active": True, "sortable": True},
                {
                    "value": "assigned_locker",
                    "label": "Assigned Locker",
                    "active": True,
                    "sortable": True,
                },
                {
                    "value": "location",
                    "label": "Location",
                    "active": True,
                    "sortable": True,
                },
                {"value": "size", "label": "Size", "active": True, "sortable": True},
                {"value": "action", "label": "Action", "active": True},
            ]
        ),
        nullable=False,
    )

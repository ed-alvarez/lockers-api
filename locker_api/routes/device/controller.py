import json
import random
from math import ceil
from typing import List, Optional, Union
from uuid import UUID, uuid4

import httpx
from gmqtt import Client as MQTTClient
from fastapi import HTTPException, UploadFile
from fastapi_async_sqlalchemy import db
from integrations import gantner, keynius, linka, spintly
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, insert, not_, or_, select, update, and_
from sqlalchemy.exc import MultipleResultsFound
from util.images import ImagesService


from ..event.model import Event, EventStatus, EventType
from ..groups.controller import (
    assign_group_to_resource,
    assign_user_to_resource,
    get_groups_from_resource,
    get_users_from_resource,
    get_group_by_name,
)
from ..groups.model import AssignmentType, ResourceType
from ..location.model import Location
from ..price.model import Price, PriceType
from ..price.controller import get_prices
from ..size.controller import get_sizes
from ..product_tracking.product_tracking import State
from ..products.controller import track_product, get_products
from ..organization.controller import get_org
from ..webhook.controller import send_payload
from ..webhook.model import EventChange
from ..groups.controller import (
    is_device_assigned_to_user,
    is_resource_in_group,
    is_resource_in_pseudo_group,
)
from ..logger.controller import add_to_logger
from ..logger.model import LogType
from .link_device_price import LinkDevicePrice
from .model import (
    Device,
    HardwareType,
    Mode,
    PaginatedDevices,
    Status,
    LockStatus,
    RestrictionType,
    Restriction,
)
from .connections import active_connections
from config import get_settings


async def broadcast_event(id_device: UUID, action_type: str, id_org: UUID):
    try:
        query = select(Device).where(Device.id == id_device, Event.id_org == id_org)
        data = await db.session.execute(query)
        device = data.unique().scalar_one_or_none()

        if not device:
            return

        device = Device.Read.parse_obj(device)
        device = device.json(exclude_none=True)

        payload = {"type": action_type, "device": json.loads(device)}

        if id_org in active_connections:
            await active_connections[id_org].send_json(payload)
    except Exception:
        return


async def get_devices(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    from_user: Optional[UUID],
    id_device: Optional[UUID] = None,
    search: Optional[str] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_status: Optional[Status] = None,
    by_mode: Optional[Mode] = None,
    hardware_type: Optional[HardwareType] = None,
    by_locations: Optional[List[UUID]] = None,
    id_locker_wall: Optional[UUID] = None,
    id_location: Optional[UUID] = None,
    id_product: Optional[UUID] = None,
) -> PaginatedDevices | Device.Read:
    org = await get_org(id_org)
    query = select(Device).where(
        or_(
            Device.id_org == id_org,
            and_(Device.id_org == org.id_tenant, Device.shared == True),  # noqa: E712
        )
    )

    if id_device:
        # * Early return if id_device is provided
        query = query.where(Device.id == id_device)

        data = await db.session.execute(query)
        device = data.unique().scalar_one_or_none()
        if device:
            return await eval_restriction(device, id_org)
        else:
            raise HTTPException(status_code=404, detail="Device not found.")

    if key and value:
        # * Early return if key and value are provided
        if key not in Device.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )
        query = query.filter(cast(Device.__table__.columns[key], VARCHAR) == value)

        data = await db.session.execute(query)
        device = data.unique().scalar_one_or_none()
        if device:
            return await eval_restriction(device, id_org)
        else:
            raise HTTPException(status_code=404, detail="Device not found.")

    if search:
        query = query.join(Location)
        query = query.filter(
            or_(
                Location.name.ilike(f"%{search}%"),
                Location.address.ilike(f"%{search}%"),
                Device.name.ilike(f"%{search}%"),
                Device.item.ilike(f"%{search}%"),
                Device.mac_address.ilike(f"%{search}%"),
                cast(Device.integration_id, VARCHAR).ilike(f"%{search}%"),
                cast(Device.locker_number, VARCHAR).ilike(f"%{search}%"),
                cast(Device.user_code, VARCHAR).ilike(f"%{search}%"),
                cast(Device.master_code, VARCHAR).ilike(f"%{search}%"),
            )
        )

    # * Filter by status, mode, hardware type and locations
    if by_status:
        query = query.where(Device.status == by_status)
    if hardware_type:
        query = query.where(Device.hardware_type == hardware_type)
    if by_locations:
        query = query.where(Device.id_location.in_(by_locations))
    if by_mode:
        query = query.where(Device.mode == by_mode)
    if id_locker_wall:
        query = query.where(Device.id_locker_wall == id_locker_wall)
    if id_location:
        query = query.where(Device.id_location == id_location)
    if id_product:
        query = query.where(Device.id_product == id_product)

    count = query
    query = (
        query.limit(size).offset((page - 1) * size).order_by(Device.locker_number.asc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    response = []
    for entry in data.unique().scalars().all():
        response.append(await eval_restriction(entry, id_org))

    # * Filter devices if user is assigned to them
    if from_user:
        response = [
            device
            for device in response
            if await is_device_assigned_to_user(device.id, from_user)
        ]

    return PaginatedDevices(
        items=response,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def get_device_by_loc_and_size(
    id_location: UUID,
    id_size: UUID,
    mode: Mode,
    id_org: UUID,
):
    query = select(Device).where(
        Device.id_location == id_location,
        Device.id_size == id_size,
        Device.mode == mode,
        Device.id_org == id_org,
        Device.status == Status.available,
    )

    res = await db.session.execute(query)

    data = res.unique().scalars().all()

    if not data:
        return None

    return random.choice(data)


async def mobile_get_devices(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    id_user: UUID,
    id_device: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    by_status: Optional[Status] = None,
    by_mode: Optional[Mode] = None,
    hardware_type: Optional[HardwareType] = None,
    id_locker_wall: Optional[UUID] = None,
    id_location: Optional[UUID] = None,
) -> PaginatedDevices:
    query = (
        select(Device)
        .where(
            Device.id_org == id_org,
            or_(
                Device.status == Status.available,
                Device.status == Status.reserved,
            ),
        )
        .join(Location)
    )

    if id_device:
        # * Early return if id_device is provided
        query = query.where(Device.id == id_device)

        data = await db.session.execute(query)
        device = data.unique().scalar_one_or_none()
        if device:
            return device
        else:
            raise HTTPException(status_code=404, detail="Device not found.")

    if key and value:
        # * Early return if key and value are provided
        if key not in Device.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )
        query = query.filter(cast(Device.__table__.columns[key], VARCHAR) == value)

        data = await db.session.execute(query)
        device = data.scalar_one_or_none()
        if device:
            return device
        else:
            raise HTTPException(status_code=404, detail="Device not found.")

    if search:
        query = query.filter(
            or_(
                Location.name.ilike(f"%{search}%"),
                Location.address.ilike(f"%{search}%"),
                Device.name.ilike(f"%{search}%"),
                Device.item.ilike(f"%{search}%"),
                Device.mac_address.ilike(f"%{search}%"),
                cast(Device.integration_id, VARCHAR).ilike(f"%{search}%"),
                cast(Device.locker_number, VARCHAR).ilike(f"%{search}%"),
                cast(Device.user_code, VARCHAR).ilike(f"%{search}%"),
                cast(Device.master_code, VARCHAR).ilike(f"%{search}%"),
            )
        )

    if by_status:
        query = query.where(Device.status == by_status)
    if by_mode:
        query = query.where(Device.mode == by_mode)
    if hardware_type:
        query = query.where(Device.hardware_type == hardware_type)
    if id_locker_wall:
        query = query.where(Device.id_locker_wall == id_locker_wall)
    if id_location:
        query = query.where(Device.id_location == id_location)

    count = query
    query = (
        query.limit(size).offset((page - 1) * size).order_by(Device.created_at.desc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(
        [
            entry
            for entry in total.unique().scalars().all()
            if await is_device_assigned_to_user(entry.id, id_user)
        ]
    )

    # * Filter devices if user is assigned to them
    items = [
        device
        for device in data.unique().scalars().all()
        if await is_device_assigned_to_user(device.id, id_user)
    ]

    return PaginatedDevices(
        items=items,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def create_device(
    id_org: UUID,
    device: Device.Write,
    assignment_type: Optional[AssignmentType],
    assign_to: Optional[List[UUID]],
    image: Optional[UploadFile],
    images_service: ImagesService,
    id_prices: Optional[List[UUID]] = None,
) -> Device.Read:
    await check_device_unique(device, id_org)

    # Validate hardware type
    await validate_device_hardware(device)

    if device.price_required and not device.id_price:
        raise HTTPException(
            status_code=400,
            detail="You must provide a price for this device",
        )

    # Validate price type
    if device.id_price:
        await validate_price_type(device)

    if image:
        try:
            image_url = (
                await images_service.upload(id_org, image)
                if image
                else print("No image")
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to upload image, {e}",
            ) from e

    new_device = Device(
        **device.dict(),
        image=image_url["url"] if image else None,
        id_org=id_org,
        lock_status=(
            LockStatus.locked
            if device.hardware_type == HardwareType.virtual
            else LockStatus.unknown
        ),
    )

    query = insert(Device).values(new_device.dict()).returning(Device)

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    new_device = response.fetchone()

    if assignment_type:
        match assignment_type:
            case AssignmentType.user:
                for id_user in assign_to:
                    await assign_user_to_resource(
                        id_user,
                        new_device.id,
                        ResourceType.device,
                        id_org,
                    )

            case AssignmentType.group:
                for id_group in assign_to:
                    await assign_group_to_resource(
                        id_group,
                        new_device.id,
                        ResourceType.device,
                        id_org,
                    )

            case _:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid assignment type {assignment_type}",
                )

    if device.id_location:
        query = select(Location).where(Location.id == device.id_location)
        response = await db.session.execute(query)
        location = response.unique().scalar_one_or_none()
        if location and location.shared:
            query = (
                update(Device)
                .where(Device.id == new_device.id)
                .values(shared=location.shared)
            )
            await db.session.execute(query)
            await db.session.commit()

    if id_prices:
        query = insert(LinkDevicePrice).values(
            [{"id_price": price, "id_device": new_device.id} for price in id_prices]
        )

        await db.session.execute(query)
        await db.session.commit()

    else:
        await db.session.commit()

    new_device = Device.Read(**new_device)

    return new_device


async def create_device_csv(id_org: UUID, device: Device.WriteCSV):
    try:
        if device.location:
            query = select(Location).where(
                Location.id_org == id_org, Location.name == device.location
            )
            res = await db.session.execute(query)
            location = res.scalar_one()
        if device.price:
            price = await get_prices(id_org, None, None, key="name", value=device.price)
        if device.size:
            size = await get_sizes(id_org, None, None, key="name", value=device.size)
        if device.product:
            product = await get_products(
                None, None, id_org=id_org, key="name", value=device.product
            )
        if device.group:
            group = await get_group_by_name(device.group, id_org)

        new_device: Device.Write = Device.Write.parse_obj(device)

        new_device.id_product = product.id if device.product else None
        new_device.id_size = size.id if device.size else None
        new_device.id_price = price.id if device.price else None
        new_device.id_location = location.id if device.location else None

        print(*new_device)

        await create_device(
            id_org,
            new_device,
            AssignmentType.group if device.group else None,
            [group["id"]] if device.group else None,
            None,
            ImagesService,
        )  # type: ignore
    except HTTPException as e:
        return e.detail

    return True


async def update_device_csv(id_org: UUID, device: Device.Write, id_device: UUID):
    try:
        await patch_device(id_device, id_org, device, False)
    except HTTPException as e:
        return e.detail

    return True


async def update_device(
    id_device: UUID,
    id_org: UUID,
    device: Device.Write,
    image: Optional[UploadFile],
    images_service: ImagesService,
    id_prices: Optional[List[UUID]] = None,
    member_name: Optional[str] = None,
) -> Device.Read:
    await check_device_unique(device, id_org, id_device)

    if device.price_required and not device.id_price:
        raise HTTPException(
            status_code=400,
            detail="You must provide a price for this device",
        )

    # Validate price type
    if device.id_price:
        await validate_price_type(device)

    device_query = select(Device).where(Device.id == id_device)
    device_response = await db.session.execute(device_query)
    device_data = device_response.unique().scalar_one_or_none()

    if not device_data:
        raise HTTPException(
            status_code=404,
            detail=f"Device with id '{id_device}' was not found",
        )

    # Check if device has active events
    event_query = select(Event).where(
        Event.id_device == id_device,
        Event.id_org == id_org,
        not_(
            Event.event_status.in_(
                [
                    EventStatus.canceled,
                    EventStatus.finished,
                    EventStatus.refunded,
                ]
            )
        ),
    )

    response = await db.session.execute(event_query)
    events = response.unique().scalars().all()

    if len(events) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Device with name: '{device_data.name}', has active events",
        )

    # Validate hardware type
    await validate_device_hardware(device)

    # Try to upload image, if any
    try:
        image_url = (
            await images_service.upload(id_org, image) if image else print("No image")
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to upload image, {e}",
        )

    query = (
        update(Device)
        .where(Device.id == id_device, Device.id_org == id_org)
        .values(
            **device.dict(exclude_unset=True),
            image=image_url["url"] if image else Device.image,
            lock_status=(
                LockStatus.locked
                if device.hardware_type == HardwareType.virtual
                else LockStatus.unknown
            ),
        )
        .returning(Device)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError
    updated_device = response.fetchone()

    if updated_device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device with id '{id_device}' was not found after update",
        )

    if device.id_location:
        query = select(Location).where(Location.id == device.id_location)
        response = await db.session.execute(query)
        location = response.unique().scalar_one_or_none()
        if location and location.shared:
            query = (
                update(Device)
                .where(Device.id == updated_device.id)
                .values(shared=location.shared)
            )
            await db.session.execute(query)
            await db.session.commit()

    if id_prices:
        query = delete(LinkDevicePrice).where(
            LinkDevicePrice.id_device == updated_device.id
        )

        await db.session.execute(query)
        await db.session.commit()

        query = insert(LinkDevicePrice).values(
            [{"id_price": price, "id_device": updated_device.id} for price in id_prices]
        )

        await db.session.execute(query)
        await db.session.commit()

    if len(id_prices) == 0:
        query = delete(LinkDevicePrice).where(
            LinkDevicePrice.id_device == updated_device.id
        )

        await db.session.execute(query)
        await db.session.commit()

    if device.status == Status.maintenance:
        await add_to_logger(
            id_org,
            id_device,
            LogType.maintenance,
            log_owner=member_name if member_name else "API",
        )

    return Device.Read(**updated_device)


async def patch_device(
    id_device: UUID,
    id_org: UUID,
    device: Device.Patch,
    bypass_events: bool = False,  # * Used to bypass event validation, used by "mobile_confirm_event"
    member_name: Optional[str] = None,
) -> Device.Read:
    await check_device_unique(device, id_org, id_device)

    query = select(Device).where(Device.id == id_device)
    response = await db.session.execute(query)
    data = response.unique().scalar_one_or_none()

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Device with id '{id_device}' was not found",
        )

    if not bypass_events:
        query = select(Event).where(
            Event.id_device == id_device,
            Event.id_org == id_org,
            not_(
                Event.event_status.in_(
                    [
                        EventStatus.canceled,
                        EventStatus.finished,
                        EventStatus.refunded,
                    ]
                )
            ),
        )

        response = await db.session.execute(query)
        events = response.unique().scalars().all()

        if len(events) > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Device with name: '{data.name}', has active events",
            )

    # Validate hardware type
    await validate_device_hardware(device, True)

    query = (
        update(Device)
        .where(Device.id == id_device, Device.id_org == id_org)
        .values(
            **device.dict(exclude_unset=True),
        )
        .returning(Device)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    updated_device = response.fetchone()

    if updated_device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device with id '{id_device}' was not found after update",
        )

    if device.id_location:
        query = select(Location).where(Location.id == device.id_location)
        response = await db.session.execute(query)
        location = response.unique().scalar_one_or_none()
        if location and location.shared:
            query = (
                update(Device)
                .where(Device.id == updated_device.id)
                .values(shared=location.shared)
            )
            await db.session.execute(query)
            await db.session.commit()

    if device.status == Status.maintenance:
        await add_to_logger(
            id_org,
            id_device,
            LogType.maintenance,
            log_owner=member_name if member_name else "API",
        )

    return Device.Read(**updated_device)


async def set_lock_state(
    id_device: UUID,
    id_org: UUID,
    lock_status: LockStatus,
    member_name: Optional[str] = None,
) -> Device.Read:
    query = (
        update(Device)
        .where(Device.id == id_device, Device.id_org == id_org)
        .values(
            lock_status=lock_status,
        )
        .returning(Device)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    updated_device = response.fetchone()

    if updated_device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device with id '{id_device}' was not found after update",
        )

    if lock_status == LockStatus.closed:
        await add_to_logger(
            id_org,
            id_device,
            LogType.lock,
            log_owner=member_name if member_name else "API",
        )
    elif lock_status == LockStatus.open:
        await add_to_logger(
            id_org,
            id_device,
            LogType.unlock,
            log_owner=member_name if member_name else "API",
        )

    return Device.Read(**updated_device)


async def patch_devices(
    id_devices: List[UUID],
    device: Device.Patch,
    id_org: UUID,
):
    update_results = []
    for id_device in id_devices:
        try:
            await patch_device(id_device, id_org, device)
            update_results.append({"id": id_device, "status": "updated"})

        except Exception as e:
            update_results.append(
                {"id": id_device, "status": "failed", "error": str(e)}
            )

    return {"detail": "Devices updated", "results": update_results}


async def set_device_maintenance(
    id_device: UUID,
    id_org: UUID,
    disable: bool = True,
):
    query = select(Device).where(Device.id == id_device, Device.id_org == id_org)
    response = await db.session.execute(query)
    device = response.unique().scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=404,
            detail=f"Device with id '{id_device}' was not found",
        )

    query = (
        update(Device)
        .where(Device.id == id_device, Device.id_org == id_org)
        .values(
            status=Status.maintenance if disable else Status.available,
        )
    )

    response = await db.session.execute(query)
    await db.session.commit()

    await add_to_logger(id_org, id_device, LogType.report_issue, log_owner="API")

    return device


async def set_devices_shared(
    id_location: UUID,
    id_org: UUID,
    shared: bool,
):
    query = (
        update(Device)
        .where(Device.id_location == id_location, Device.id_org == id_org)
        .values(shared=shared)
    )

    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Devices updated"}


async def delete_devices(devices: List[UUID], id_org: UUID):
    query = (
        select(Device.name)
        .where(Device.id_org == id_org, Device.id.in_(devices))
        .join_from(Device, Event, Device.id == Event.id_device)
        .where(
            not_(
                Event.event_status.in_(
                    [
                        EventStatus.canceled,
                        EventStatus.finished,
                    ]
                )
            )
        )
    )

    response = await db.session.execute(query)
    devices_r = response.unique().scalars().all()

    if len(devices_r) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Devices with names {devices_r} have active events",
        )

    query = select(Event.id).where(Event.id_org == id_org, Event.id_device.in_(devices))

    response = await db.session.execute(query)
    events = response.unique().scalars().all()

    if len(events) > 0:
        query = update(Event).where(Event.id.in_(events)).values(id_device=None)
        await db.session.execute(query)
        await db.session.commit()

    # Check if one or more devices are part of a locker wall
    query = select(Device).where(Device.id_org == id_org, Device.id.in_(devices))
    response = await db.session.execute(query)
    devices_selected = response.unique().scalars().all()

    for device in devices_selected:
        if device.id_locker_wall:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete device: {device.name}, it is part of a locker wall",
            )

    query = delete(Device).where(Device.id_org == id_org, Device.id.in_(devices))

    response = await db.session.execute(query)
    await db.session.commit()

    return {"detail": f"Deleted {response.rowcount} devices"}


async def validate_price_type(device: Device.Write):
    id_price = device.id_price

    query = select(Price).where(Price.id == id_price)

    response = await db.session.execute(query)
    price = response.unique().scalar_one()  # raises NoResultFound

    # Only allow PriceType.pay_per_weight if device mode is set to
    # service:
    if price.price_type == PriceType.pay_per_weight and device.mode != Mode.service:
        raise HTTPException(
            status_code=400,
            detail="You can only set a pay-per-weight price to a device with mode service pick-up",
        )

    return True


async def validate_device_hardware(
    device: Device.Write | Device.Patch, patch: bool = False
):
    match device.dict():
        case {
            "hardware_type": HardwareType.linka,
            "mac_address": device.mac_address,
            "integration_id": None,
            "user_code": None,
            "master_code": None,
            "gantner_id": None,
            "keynius_id": None,
            "harbor_tower_id": None,
            "harbor_locker_id": None,
            "dclock_terminal_no": None,
            "dclock_box_no": None,
        }:
            pass

        case {
            "hardware_type": HardwareType.spintly,
            "mac_address": None,
            "integration_id": device.integration_id,
            "user_code": None,
            "master_code": None,
            "gantner_id": None,
            "keynius_id": None,
            "harbor_tower_id": None,
            "harbor_locker_id": None,
            "dclock_terminal_no": None,
            "dclock_box_no": None,
        }:
            pass

        case {
            "hardware_type": HardwareType.ojmar,
            "mac_address": None,
            "integration_id": None,
            "locker_udn": device.locker_udn,
            "user_code": device.user_code,
            "master_code": device.master_code,
            "gantner_id": None,
            "keynius_id": None,
            "harbor_tower_id": None,
            "harbor_locker_id": None,
            "dclock_terminal_no": None,
            "dclock_box_no": None,
        }:
            pass

        case {
            "hardware_type": HardwareType.gantner,
            "mac_address": None,
            "integration_id": None,
            "user_code": None,
            "master_code": None,
            "gantner_id": device.gantner_id,
            "keynius_id": None,
            "harbor_tower_id": None,
            "harbor_locker_id": None,
            "dclock_terminal_no": None,
            "dclock_box_no": None,
        }:
            pass
        case {
            "hardware_type": HardwareType.keynius,
            "mac_address": None,
            "integration_id": None,
            "user_code": None,
            "master_code": None,
            "gantner_id": None,
            "keynius_id": device.keynius_id,
            "harbor_tower_id": None,
            "harbor_locker_id": None,
            "dclock_terminal_no": None,
            "dclock_box_no": None,
        }:
            pass
        case {
            "hardware_type": HardwareType.harbor,
            "mac_address": None,
            "integration_id": None,
            "user_code": None,
            "master_code": None,
            "gantner_id": None,
            "keynius_id": None,
            "harbor_tower_id": device.harbor_tower_id,
            "harbor_locker_id": device.harbor_locker_id,
            "dclock_terminal_no": None,
            "dclock_box_no": None,
        }:
            pass
        case {
            "hardware_type": HardwareType.dclock,
            "mac_address": None,
            "integration_id": None,
            "user_code": None,
            "master_code": None,
            "gantner_id": None,
            "keynius_id": None,
            "harbor_tower_id": None,
            "harbor_locker_id": None,
            "dclock_terminal_no": device.dclock_terminal_no,
            "dclock_box_no": device.dclock_box_no,
        }:
            pass
        case {
            "hardware_type": None,
            "mac_address": None,
            "integration_id": None,
            "user_code": None,
            "master_code": None,
            "gantner_id": None,
            "keynius_id": None,
            "harbor_tower_id": None,
            "harbor_locker_id": None,
            "dclock_terminal_no": None,
            "dclock_box_no": None,
        }:
            if patch is False:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid hardware type",
                )

        case {
            "hardware_type": HardwareType.virtual,
            "mac_address": None,
            "integration_id": None,
            "user_code": None,
            "master_code": None,
            "gantner_id": None,
            "keynius_id": None,
            "harbor_tower_id": None,
            "harbor_locker_id": None,
            "dclock_terminal_no": None,
            "dclock_box_no": None,
        }:
            pass
        case _:
            raise HTTPException(
                status_code=400,
                detail="Invalid hardware type",
            )


async def linka_unlock(device: Device):
    token = await linka.get_token()

    await linka.test_token(token)
    await linka.unlock(token=token, mac_addr=device.mac_address)

    return {"detail": "Unlock message sent to Linka device"}


async def spintly_unlock(device: Device):
    async with httpx.AsyncClient() as client:
        token = await spintly.get_token(client)

        await spintly.activate(
            client=client,
            token=token,
            access_point_id=device.integration_id,
        )

    return {"detail": "Unlock message sent to Spintly device"}


async def keynius_unlock(device: Device):
    client = await keynius.get_client()

    await keynius.unlock(
        token=client["accessToken"],
        locker_id=device.keynius_id,
    )

    return {"detail": "Unlock message sent to Keynius device"}


async def gantner_unlock(device: Device):
    query = select(Device).where(Device.id == device.id)

    response = await db.session.execute(query)
    device = response.unique().scalar_one()  # raises NoResultFound

    if device.lock_status.value == "offline":
        raise HTTPException(
            status_code=400,
            detail="Cannot unlock device, device is offline",
        )

    if device.lock_status.value != "locked":
        return {"detail": "Device is already open"}

    await gantner.unlock(device.gantner_id)

    return {"detail": "Unlock message sent to Gantner device"}


async def dclock_unlock(device: Device):
    query = select(Device).where(Device.id == device.id)

    response = await db.session.execute(query)
    device = response.unique().scalar_one()  # raises NoResultFound

    settings = get_settings()

    client = MQTTClient(str(uuid4()))

    client.set_auth_credentials(settings.mqtt_user, settings.mqtt_pass)
    await client.connect(settings.mqtt_host, settings.mqtt_port, True)

    client.publish(f"{device.dclock_terminal_no}/cmd", device.dclock_box_no)

    await client.disconnect()

    return {
        "detail": f"Unlock message sent to terminal no. '{device.dclock_terminal_no}' locker no '{device.dclock_box_no}'"
    }


async def virtual_device_unlock(device: Device):
    query = select(Device).where(Device.id == device.id)

    response = await db.session.execute(query)
    device = response.unique().scalar_one()  # raises NoResultFound

    # Run update query after checking for device:
    query = (
        update(Device)
        .where(
            Device.id == device.id,
        )
        .values(
            lock_status=(
                LockStatus.open
                if device.lock_status == LockStatus.locked
                else LockStatus.locked
            )
        )
        .returning(Device)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    return {"detail": "Virtual device unlocked"}


async def partner_repair_all_devices(
    devices: List[UUID],
    id_org: UUID,
    disable: bool = False,
):
    query = select(Device).where(
        Device.id.in_(devices),
        Device.id_org == id_org,
        Device.status == Status.reserved,
    )

    response = await db.session.execute(query)
    count = response.unique().scalars().all()

    query = (
        update(Device)
        .where(
            Device.id.in_(devices),
            Device.id_org == id_org,
            Device.status != Status.reserved,
        )
        .values(
            status=Status.maintenance if disable else Status.available,
        )
        .returning(Device)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raise IntegrityError

    data = response.unique().all()

    for device in data:
        if device.id_product and disable is True:
            await track_product(
                device.id_product,
                State.maintenance,
                id_org,
                None,
                device.id,
            )

    text = "maintenance" if disable else "available"

    if len(count) > 0:
        detail_message = f"Set {len(data)} device(s) to {text}, {len(count)} device(s) were reserved and could not be set to {text}"
    else:
        detail_message = f"Set {len(data)} device(s) to {text}"

    return {"detail": detail_message}


async def partner_unlock_devices(
    devices: List[UUID],
    id_org: UUID,
    member_name: Optional[str] = None,
):
    query = select(Device).where(
        Device.id.in_(devices),
        Device.id_org == id_org,
    )

    response = await db.session.execute(query)
    devices = response.unique().scalars().all()

    unlock_results = []
    for device_record in devices:
        try:
            await partner_unlock_device(device_record.id, id_org, False, member_name)
            unlock_results.append({"id": device_record.id, "status": "unlocked"})
        except Exception as e:
            unlock_results.append(
                {"id": device_record.id, "status": "failed", "error": str(e)}
            )

    return {
        "detail": "Unlock message sent to selected devices",
        "results": unlock_results,
    }


async def partner_unlock_device(
    id_device: UUID,
    id_org: UUID = None,
    complete_event: Optional[bool] = False,
    member_name: Optional[str] = None,
):
    if id_org:
        query = select(Device).where(
            Device.id == id_device,
            Device.id_org == id_org,
        )
    else:
        query = select(Device).where(Device.id == id_device)

    response = await db.session.execute(query)
    device = response.unique().scalar_one()  # raises NoResultFound

    # This is for TRAX FP, which has a different unlock flow
    if device.mode == Mode.delivery and complete_event is False:
        # Select the event that is currently in progress, with the device id
        query = select(Event).where(
            Event.id_device == id_device,
            Event.event_status == EventStatus.awaiting_service_dropoff,
        )
        result = await db.session.execute(query)
        try:
            event = result.unique().scalar_one_or_none()
        except MultipleResultsFound:
            print("No event found")

        # If there is an event, update to awaiting_user_pickup
        if event:
            query = (
                update(Event)
                .where(
                    Event.id == event.id,
                )
                .values(
                    event_status=EventStatus.awaiting_user_pickup,
                )
                .returning(Event)
            )

            response = await db.session.execute(query)
            await db.session.commit()

            # Send webhook payload
            print("Sending webhook payload")
            await send_payload(
                id_org,
                EventChange(
                    id_org=event.id_org,
                    id_event=event.id,
                    event_status=EventStatus.awaiting_user_pickup,
                    event_obj=response.all().pop(),
                ),
            )

            print("Updated event status to awaiting_user_pickup")

    await add_to_logger(
        id_org,
        id_device,
        LogType.unlock,
        log_owner=member_name if member_name else "API",
    )

    match device.hardware_type:
        case HardwareType.linka:
            return await linka_unlock(device)
        case HardwareType.spintly:
            return await spintly_unlock(device)
        case HardwareType.gantner:
            return await gantner_unlock(device)
        case HardwareType.keynius:
            return await keynius_unlock(device)
        case HardwareType.harbor:
            return True
        case HardwareType.dclock:
            return await dclock_unlock(device)
        case HardwareType.virtual:
            return await virtual_device_unlock(device)
        case _:
            raise HTTPException(
                status_code=400,
                detail="Unsupported command",
            )


async def mobile_unlock_device(
    id_event: UUID,
    id_org: UUID,
    id_user: UUID,
):
    query = (
        select(Event, Device)
        .where(
            Event.id == id_event,
            Event.id_org == id_org,
            Event.id_user == id_user,
        )
        .join(Device)
    )

    response = await db.session.execute(query)

    try:
        event = response.unique().all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find device in event id {id_event} associated with user id {id_user}",
        )

    if event.Device.status != Status.reserved:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot unlock device with status {event.Device.status}",
        )

    if (
        event.Event.event_status != EventStatus.awaiting_user_pickup
        and event.Event.event_status != EventStatus.awaiting_service_pickup
        and (
            event.Event.event_status != EventStatus.in_progress
            and (
                event.Event.event_type != EventType.storage
                or event.Event.event_type == EventType.rental
            )
        )
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot unlock device with event status {event.Event.event_status}",
        )

    await add_to_logger(id_org, event.Device.id, LogType.unlock, "API")

    match event.Device.hardware_type:
        case HardwareType.linka:
            return await linka_unlock(event.Device)
        case HardwareType.spintly:
            return await spintly_unlock(event.Device)
        case HardwareType.gantner:
            return await gantner_unlock(event.Device)
        case HardwareType.keynius:
            return await keynius_unlock(event.Device)
        case HardwareType.dclock:
            return await dclock_unlock(event.Device)
        case HardwareType.virtual:
            return {"detail": "Virtual device unlocked"}
        case _:
            raise HTTPException(
                status_code=400,
                detail="Unsupported command",
            )


async def mobile_unlock_device_service(
    id_device: UUID,
    id_org: UUID,
):
    query = select(Device).where(
        Device.id == id_device,
        Device.id_org == id_org,
    )

    response = await db.session.execute(query)

    device = response.unique().scalar_one()

    if device.mode != Mode.service:
        raise HTTPException(
            status_code=400,
            detail="Cannot unlock a device for service that is not in service mode",
        )

    if device.status != Status.available:
        raise HTTPException(
            status_code=400,
            detail="This device is not currently available",
        )

    match device.hardware_type:
        case HardwareType.linka:
            return await linka_unlock(device)
        case HardwareType.spintly:
            return await spintly_unlock(device)
        case HardwareType.gantner:
            return await gantner_unlock(device)
        case HardwareType.keynius:
            return await keynius_unlock(device)
        case HardwareType.dclock:
            return await dclock_unlock(device)
        case HardwareType.virtual:
            return {"detail": "Virtual device unlocked"}
        case _:
            raise HTTPException(
                status_code=400,
                detail="Unsupported command",
            )


async def delivery_unlock_device(
    id_event: UUID,
    id_device: UUID,
):
    query = select(Event).where(
        Event.id == id_event,
        Event.id_device == id_device,
        Event.event_type == EventType.delivery,
    )

    response = await db.session.execute(query)
    event = response.unique().scalar_one()  # raises NoResultFound

    match event.device.hardware_type:
        case HardwareType.linka:
            await linka_unlock(event.device)
        case HardwareType.spintly:
            await spintly_unlock(event.device)
        case HardwareType.gantner:
            await gantner_unlock(event.device)
        case HardwareType.keynius:
            await keynius_unlock(event.device)
        case HardwareType.dclock:
            await dclock_unlock(event.device)
        case HardwareType.virtual:
            print("Virtual device")
        case _:
            raise HTTPException(
                status_code=400,
                detail="Unsupported command",
            )

    return event


async def reserve_device(
    id_device: UUID,
    id_org: UUID,
) -> Device.Read:
    query = select(Device).where(
        Device.id == id_device,
        Device.id_org == id_org,
        Device.status == Status.available,
    )

    response = await db.session.execute(query)
    device = response.unique().scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=404,
            detail="This Device is not currently available",
        )

    query = (
        update(Device)
        .where(
            Device.id == id_device,
            Device.id_org == id_org,
            Device.status == Status.available,
        )
        .values(
            status=Status.reserved,
        )
        .returning(Device)
    )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    return device


async def unreserve_device(
    id_device: UUID,
    id_org: Optional[UUID] = None,
):
    if id_org:
        query = (
            update(Device)
            .where(
                Device.id == id_device,
                Device.id_org == id_org,
            )
            .values(
                status=Status.available,
            )
            .returning(Device)
        )
    else:
        query = (
            update(Device)
            .where(
                Device.id == id_device,
            )
            .values(
                status=Status.available,
            )
            .returning(Device)
        )

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    try:
        return response.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=400,
            detail=f"Could not unreserve device with id '{id_device}', is it already available?",
        )


async def check_device_unique(
    device: Union[Device.Write, Device.Patch],
    id_org: UUID,
    id_device: Optional[UUID] = None,
):
    query = select(Device).where(
        Device.id_org == id_org,
        Device.name == device.name,
    )

    if device.custom_identifier:
        query = select(Device).where(
            Device.id_org == id_org,
            or_(
                Device.name == device.name,
                Device.custom_identifier == device.custom_identifier,
            ),
        )

    if id_device:
        query = query.where(Device.id != id_device)

    response = await db.session.execute(query)

    data = response.unique().scalars().all()

    if len(data) > 0:
        raise HTTPException(
            status_code=409,
            detail="One or more fields are not unique, check the following fields: [Name, Custom Identifier]",
        )

    if device.locker_number:
        query = select(Device).where(
            Device.id_org == id_org,
            Device.locker_number == device.locker_number,
            Device.id_location == device.id_location,
            Device.mode == device.mode,
        )

        if id_device:
            query = query.where(Device.id != id_device)

        response = await db.session.execute(query)

        data = response.unique().scalar_one_or_none()

        if data:
            raise HTTPException(
                status_code=409,
                detail=f"Locker number {device.locker_number} is already in use at this location in {device.mode} mode",
            )


async def eval_restriction(entry, id_org: UUID):
    device = Device.Read.parse_obj(entry)

    in_group = await is_resource_in_group(device.id, ResourceType.device)
    in_users = await is_resource_in_pseudo_group(device.id, ResourceType.device)

    if in_users:
        device.restriction = Restriction(
            restriction_type=RestrictionType.users,
            items=await get_users_from_resource(device.id, ResourceType.device, id_org),
        )
    elif in_group:
        device.restriction = Restriction(
            restriction_type=RestrictionType.groups,
            items=await get_groups_from_resource(
                device.id, ResourceType.device, id_org
            ),
        )
    else:
        device.restriction = None

    return device

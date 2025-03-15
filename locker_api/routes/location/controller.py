import math
import re
from math import ceil
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from fastapi_async_sqlalchemy import db
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, desc, insert, or_, select, update, and_
from util.images import ImagesService
from util.validator import lookup_phone

from ..device.controller import partner_unlock_device, set_devices_shared
from ..device.model import Device, Mode, Status, Restriction, RestrictionType
from ..event.model import Event
from ..groups.controller import (
    assign_group_to_resource,
    assign_user_to_resource,
    is_resource_in_group,
    is_resource_in_pseudo_group,
    is_device_assigned_to_user,
    get_groups_from_resource,
    get_users_from_resource,
)
from ..groups.model import AssignmentType, ResourceType
from ..organization.model import LinkOrgUser
from ..organization.controller import get_org, get_org_tree_bfs
from ..size.model import Size
from .model import Location, PaginatedLocations


async def get_last_location(current_user):
    query = (
        select(Event)
        .where(Event.id_user == current_user)
        .order_by(desc(Event.created_at))
        .limit(1)
    )

    data = await db.session.execute(query)
    event = data.unique().scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="User doesn't have any events yet",
        )

    if not event.device:
        raise HTTPException(
            status_code=404,
            detail="Device for latest location not found or removed",
        )

    if not event.device.location:
        raise HTTPException(
            status_code=404,
            detail="Latest location not found or removed",
        )

    location = event.device.location
    devices = await mobile_get_devices_in_location(
        location.id,
        None,
        None,
        None,
    )

    return {
        **location.dict(),
        "devices": devices,
    }


async def get_recent_locations(current_user):
    query = (
        select(Event)
        .where(Event.id_user == current_user)
        .order_by(desc(Event.created_at))
        .limit(10)
    )

    data = await db.session.execute(query)
    events = data.unique().scalars().all()

    if not events:
        raise HTTPException(
            status_code=404,
            detail="User doesn't have any events yet",
        )

    locations = []

    for event in events:
        if not event.device:
            continue

        if not event.device.location:
            continue

        location = event.device.location
        location.devices = await mobile_get_devices_in_location(
            location.id,
            None,
            None,
            None,
        )
        locations.append(location)

    return locations


async def get_favorite_location(current_user):
    query = select(LinkOrgUser).where(
        LinkOrgUser.id_user == current_user,
    )

    data = await db.session.execute(query)
    link = data.unique().scalar_one_or_none()

    return link


async def set_favorite_location(current_user, id_location: UUID):
    query = select(Location).where(Location.id == id_location)

    data = await db.session.execute(query)
    location = data.unique().scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    query = (
        update(LinkOrgUser)
        .where(LinkOrgUser.id_user == current_user)
        .values(id_favorite_location=id_location)
        .returning(LinkOrgUser)
    )

    data = await db.session.execute(query)
    await db.session.commit()
    link = data.all().pop()

    return link


async def partner_get_locations(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    id_location: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    hidden: Optional[bool] = None,
    search: Optional[str] = None,
):
    org = await get_org(id_org)
    query = select(Location).where(
        or_(
            Location.id_org == id_org,
            and_(Location.id_org == org.id_tenant, Location.shared == True),  # noqa: E712
        )
    )

    if id_location:
        # * Early return if id_location is provided
        query = query.where(Location.id == id_location)

        result = await db.session.execute(query)
        location = result.unique().scalar_one()

        location.devices = await partner_get_devices_in_location(
            location.id, None, None, None, None
        )

        return await eval_restriction(location, id_org)

    if key and value:
        # * Early return if key and value are provided
        if key not in Location.__table__.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {key}",
            )

        query = query.filter(cast(Location.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        location = result.unique().scalar_one()

        location.devices = await partner_get_devices_in_location(
            location.id, None, None, None, None
        )

        return await eval_restriction(location, id_org)

    if search:
        query = query.filter(
            or_(
                cast(Location.address, VARCHAR).ilike(f"%{search}%"),
                cast(Location.name, VARCHAR).ilike(f"%{search}%"),
            )
        )

    if hidden:
        query = query.where(Location.hidden == hidden)

    count = query

    query = (
        query.limit(size).offset((page - 1) * size).order_by(Location.created_at.desc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())
    locations = data.unique().scalars().all()

    response = []
    for entry in locations:
        location = await eval_restriction(entry, id_org)
        location.devices = await partner_get_devices_in_location(
            location.id, None, None, None, None
        )
        response.append(location)

    return PaginatedLocations(
        items=response,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def mobile_get_locations(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    id_location: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    device_mode: Optional[Mode] = None,
    search: Optional[str] = None,
    expand: Optional[bool] = False,
):
    query = select(Location).where(Location.hidden == False)  # noqa: E712

    if id_location:
        # * Early return if id_location is provided
        query = query.where(Location.id == id_location, Location.id_org == id_org)

        result = await db.session.execute(query)
        location = result.unique().scalar_one()

        location.devices = await mobile_get_devices_in_location(
            location.id, None, None, None
        )
        location = await eval_restriction(location, id_org)
        return location

    if key and value:
        # * Early return if key and value are provided
        if key not in Location.__table__.columns:
            raise HTTPException(status_code=400, detail=f"Invalid field: {key}")

        query = query.filter(cast(Location.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        location = result.unique().scalar_one()

        location.devices = await mobile_get_devices_in_location(
            location.id, None, None, None
        )
        location = await eval_restriction(location, id_org)
        return location

    if expand is True:
        ids = await get_org_tree_bfs(id_org)
        query = select(Location).where(
            Location.id_org.in_(ids),
            Location.hidden == False,  # noqa: E712
        )  # noqa: E712
    else:
        query = query.where(Location.id_org == id_org)

    if search:
        query = query.filter(
            or_(
                cast(Location.address, VARCHAR).ilike(f"%{search}%"),
                cast(Location.name, VARCHAR).ilike(f"%{search}%"),
            )
        )

    count = query
    query = (
        query.limit(size).offset((page - 1) * size).order_by(Location.created_at.desc())
    )

    locations_session = await db.session.execute(query)
    locations_data = locations_session.unique().scalars().all()

    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    response = []

    for location in locations_data:
        devices = await mobile_get_devices_in_location(
            location.id, device_mode, None, None
        )

        available = 0
        reserved = 0
        maintenance = 0

        for device in devices:
            if device.status == Status.available:
                available += 1
            elif device.status == Status.reserved:
                reserved += 1
            elif device.status == Status.maintenance:
                maintenance += 1

        location = await eval_restriction(location, id_org)
        response.append(location)

        response.append(
            {
                **location.dict(),
                "available_devices": available,
                "reserved_devices": reserved,
                "maintenance_devices": maintenance,
                "devices": devices,
            }
        )

    return PaginatedLocations(
        items=response,
        total=total_count,
        pages=ceil(total_count / size),
    )


def haversine(lat1: float, lon1: float, lat2: float, lon2: float):
    R = 6371  # radius of Earth in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


async def mobile_get_geo_locations(
    id_org: UUID,
    lat: Optional[float],
    lng: Optional[float],
    radius: Optional[int],
    expand: Optional[bool] = False,
):
    query = select(Location).where(Location.hidden == False)  # noqa: E712

    if expand is True:
        ids = await get_org_tree_bfs(id_org)
        query = select(Location).where(
            Location.id_org.in_(ids),
            Location.hidden == False,  # noqa: E712
        )  # noqa: E712
    else:
        query = query.where(Location.id_org == id_org)

    if lat and lng and radius:
        locations = await db.session.execute(query)
        locations_data = locations.unique().scalars().all()

        locations_in_radius = [
            location
            for location in locations_data
            if haversine(lat, lng, float(location.latitude), float(location.longitude))
            <= radius
        ]

        return locations_in_radius

    data = await db.session.execute(query)

    locations = data.unique().scalars().all()

    response = []
    for location in locations:
        location.devices = await mobile_get_devices_in_location(
            location.id, None, None, None
        )
        response.append(location)

    return response


async def mobile_get_devices_in_location(
    id_location: UUID,
    device_mode: Optional[Mode],
    by_size: Optional[UUID],
    id_org: Optional[UUID],
):
    query = select(Device).where(
        Device.id_location == id_location,
        or_(
            Device.status == Status.available,
            Device.status == Status.reserved,
        ),
    )

    if device_mode:
        query = query.where(Device.mode == device_mode)

    if by_size:
        query = query.where(Device.id_size == by_size)

    if id_org:
        query = query.where(Device.id_org == id_org)

    data = await db.session.execute(query)

    devices = data.unique().scalars().all()

    return devices


async def partner_get_sizes_in_location(
    id_location: UUID,
    id_org: UUID,
    device_mode: Optional[Mode],
    device_status: Optional[Status],
):
    # Fail if there is no location
    query = select(Location).where(
        Location.id == id_location, Location.id_org == id_org
    )
    data = await db.session.execute(query)
    data.scalar_one()

    query = select(Device).where(
        Device.id_location == id_location, Device.id_org == id_org
    )

    if device_mode:
        query = query.where(Device.mode == device_mode)

    if device_status:
        query = query.where(Device.status == device_status)

    data = await db.session.execute(query)
    devices = data.unique().scalars().all()

    sizes = {}

    for device in devices:
        if device.size:
            if device.size.id in sizes:
                sizes[device.size.id]["available_devices"] += (
                    1 if device.status == Status.available else 0
                )
            else:
                sizes[device.size.id] = {
                    "id": device.size.id,
                    "name": device.size.name,
                    "width": device.size.width,
                    "height": device.size.height,
                    "depth": device.size.depth,
                    "available_devices": 1 if device.status == Status.available else 0,
                }

    return list(sizes.values())


async def partner_get_devices_in_location(
    id_location: UUID,
    from_user: Optional[UUID],
    device_mode: Optional[Mode],
    by_status: Optional[Status],
    id_org: Optional[UUID],
):
    query = select(Device).where(
        Device.id_location == id_location,
    )

    if device_mode:
        query = query.where(Device.mode == device_mode)

    if by_status:
        query = query.where(Device.status == by_status)

    if id_org:
        query = query.where(Device.id_org == id_org)

    query = query.order_by(Device.locker_number.asc())

    data = await db.session.execute(query)
    response = data.unique().scalars().all()

    # * Filter devices if user is assigned to them
    if from_user:
        response = [
            device
            for device in response
            if await is_device_assigned_to_user(device.id, from_user)
        ]

    return response


async def mobile_get_sizes_in_location(
    id_location: UUID,
    id_org: UUID,
    device_mode: Optional[Mode],
    device_status: Optional[Status],
):
    query = (
        select(Size)
        .distinct(Size.id)
        .join(Device)
        .where(Device.id_location == id_location)
        .where(Device.id_org == id_org)
    )

    if device_mode:
        query = query.where(Device.mode == device_mode)

    if device_status:
        query = query.where(Device.status == device_status)

    data = await db.session.execute(query)

    sizes = data.unique().scalars().all()

    return sizes


async def get_location(id_location: UUID, id_org: UUID):
    query = (
        select(Location)
        .where(Location.id == id_location)
        .where(Location.id_org == id_org)
    )

    data = await db.session.execute(query)

    location = data.unique().scalar_one()
    location.devices = await partner_get_devices_in_location(
        location.id, None, None, None, None
    )
    return location


async def get_location_by_external_id(external_id: str, id_org: UUID):
    query = select(Location).where(
        Location.custom_id == external_id, Location.id_org == id_org
    )

    data = await db.session.execute(query)
    location = data.unique().scalar_one()
    location.devices = await partner_get_devices_in_location(
        location.id, None, None, None, None
    )
    return location


async def get_public_location(id_location: UUID):
    query = select(Location).where(Location.id == id_location)

    data = await db.session.execute(query)
    location = data.unique().scalar_one()
    return location


async def get_location_by_custom_id(
    custom_id: str,
    id_org: UUID,
):
    query = (
        select(Location)
        .where(Location.custom_id == custom_id)
        .where(Location.id_org == id_org)
    )

    data = await db.session.execute(query)

    location = Location.Read.parse_obj(data.unique().scalar_one_or_none())
    location.devices = await partner_get_devices_in_location(
        location.id, None, None, None, None
    )

    return location


async def create_location(
    location: Location.Write,
    image: Optional[UploadFile],
    assignment_type: Optional[AssignmentType],
    assign_to: Optional[List[UUID]],
    id_org: UUID,
    images_service: ImagesService,
):
    await check_unique_location(location, id_org)

    if location.contact_email:
        check_email = re.match(
            r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+",
            location.contact_email.lower(),
        )
        if not check_email:
            raise HTTPException(
                status_code=400,
                detail="Invalid email",
            )

    if location.contact_phone:
        check_phone = re.match(
            r"^\+?[1-9]\d{1,14}$",
            location.contact_phone,
        )
        if not check_phone:
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number",
            )
        lookup_phone(location.contact_phone)

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
            )

    new_location = Location(
        **location.dict(), image=image_url["url"] if image else None, id_org=id_org
    )

    query = insert(Location).values(new_location.dict()).returning(Location)
    response = await db.session.execute(query)

    await db.session.commit()

    new_location = response.all().pop()

    if assignment_type:
        match assignment_type:
            case AssignmentType.user:
                for id_user in assign_to:
                    await assign_user_to_resource(
                        id_user,
                        new_location.id,
                        ResourceType.location,
                        id_org,
                    )

            case AssignmentType.group:
                for id_group in assign_to:
                    await assign_group_to_resource(
                        id_group,
                        new_location.id,
                        ResourceType.location,
                        id_org,
                    )

            case _:
                error_detail = f"Invalid assignment type {assignment_type}"

                raise HTTPException(status_code=400, detail=error_detail)

    return new_location


async def update_location(
    id_location: UUID,
    id_org: UUID,
    location: Location.Write,
    image: Optional[UploadFile],
    images_service: ImagesService,
):
    await check_unique_location(location, id_org, id_location)

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
            )

    if location.contact_email:
        check_email = re.match(
            r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+",
            location.contact_email.lower(),
        )
        if not check_email:
            raise HTTPException(
                status_code=400,
                detail="Invalid email",
            )

    if location.contact_phone:
        check_phone = re.match(
            r"^\+?[1-9]\d{1,14}$",
            location.contact_phone,
        )
        if not check_phone:
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number",
            )
        lookup_phone(location.contact_phone)

    query = (
        update(Location)
        .where(Location.id == id_location)
        .values(
            **location.dict(exclude_unset=True),
            image=image_url["url"] if image else Location.image,
        )
        .returning(Location)
    )

    try:
        response = await db.session.execute(query)
        await db.session.commit()
        updated_location = response.all().pop()
    except IndexError:
        raise HTTPException(
            status_code=404, detail=f"Location with id {id_location} was not found"
        )

    # Update devices shared status, according to location
    await set_devices_shared(id_location, id_org, updated_location.shared)

    return updated_location


async def create_location_csv(id_org: UUID, location: Location.Write):
    try:
        await create_location(location, None, None, None, id_org, ImagesService)

        return True
    except HTTPException as e:
        return e.detail


async def update_location_csv(
    id_org: UUID, location: Location.Write, id_location: UUID
):
    try:
        await patch_location(id_location, location, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def patch_location(
    id_location: UUID,
    location: Location.Patch,
    id_org: UUID,
):
    if location.name:
        await check_unique_location(location, id_org, id_location)

    query = (
        update(Location)
        .where(Location.id == id_location, Location.id_org == id_org)
        .values(**location.dict(exclude_unset=True))
        .returning(Location)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        updated_location = response.all().pop()
    except IndexError:
        error_detail = f"Location with id {id_location} was not found"
        raise HTTPException(status_code=404, detail=error_detail)

    # Update devices shared status, according to location
    await set_devices_shared(id_location, id_org, updated_location.shared)

    return updated_location


async def patch_locations(
    id_locations: list[UUID],
    location: Location.Patch,
    id_org: UUID,
):
    for id_location in id_locations:
        await patch_location(id_location, location, id_org)

    return {"detail": "Locations updated"}


async def delete_location(id_location: UUID, id_org: UUID):
    query = (
        delete(Location)
        .where(Location.id == id_location, Location.id_org == id_org)
        .returning(Location)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        return response.all().pop()
    except IndexError:
        error_detail = f"Location with id {id_location} was not found"

        raise HTTPException(status_code=404, detail=error_detail)


async def delete_locations(
    locations: List[UUID],
    id_org: UUID,
):
    query = select(Device.name).where(
        Device.id_org == id_org, Device.id_location.in_(locations)
    )

    response = await db.session.execute(query)
    data = response.unique().scalars().all()

    if len(data) > 0:
        error_detail = f"Could not delete locations from devices: {data} locations are already assigned"
        raise HTTPException(status_code=400, detail=error_detail)

    query = delete(Location).where(
        Location.id_org == id_org, Location.id.in_(locations)
    )
    response = await db.session.execute(query)
    await db.session.commit()

    return {"detail": f"Deleted {response.rowcount} locations"}


async def check_unique_location(
    location: Location.Write,
    id_org: UUID,
    id_location: Optional[UUID] = None,
):
    query = select(Location).where(
        Location.id_org == id_org, Location.name == location.name
    )

    if location.custom_id:
        query = query.where(Location.custom_id == location.custom_id)

    if id_location:
        query = query.where(Location.id != id_location)

    response = await db.session.execute(query)

    data = response.unique().scalar_one_or_none()

    if data:
        error_detail = "Location with name or custom id already exists"

        raise HTTPException(status_code=400, detail=error_detail)


async def unlock_device_by_location(id_location: UUID, id_org: UUID):
    query = select(Device).where(
        Device.id_location == id_location,
        Device.id_org == id_org,
    )

    data = await db.session.execute(query)
    devices = data.unique().scalars().all()

    available_devices = []
    reserved_devices = []

    for device in devices:
        if device.status == Status.available:
            available_devices.append(device)
        elif device.status == Status.reserved:
            reserved_devices.append(device)

    for device in available_devices:
        await partner_unlock_device(device.id, device.id_org)

    return {
        "detail": f"Unlocked {len(available_devices)}/{len(devices)} devices in this location."
    }


async def eval_restriction(entry, id_org: UUID):
    location = Location.Read.parse_obj(entry)

    in_group = await is_resource_in_group(location.id, ResourceType.location)
    in_users = await is_resource_in_pseudo_group(location.id, ResourceType.location)

    if in_users:
        location.restriction = Restriction(
            restriction_type=RestrictionType.users,
            items=await get_users_from_resource(
                location.id, ResourceType.location, id_org
            ),
        )
    elif in_group:
        location.restriction = Restriction(
            restriction_type=RestrictionType.groups,
            items=await get_groups_from_resource(
                location.id, ResourceType.location, id_org
            ),
        )
    else:
        location.restriction = None

    return location

import uuid
import datetime
from math import ceil
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import delete, insert, or_, select, update


from ..device.model import Device
from ..location.model import Location
from ..organization.model import LinkOrgUser
from ..user.model import User
from .model import (
    Groups,
    LinkGroupsDevices,
    LinkGroupsLocations,
    LinkGroupsUser,
    LinkUserDevices,
    LinkUserLocations,
    PaginatedGroups,
    ResourceType,
)


async def get_groups(
    page: int, size: int, id_group: Optional[UUID], search: str, id_org: UUID
):
    query = select(Groups).where(Groups.id_org == id_org)

    if id_group:
        # * Early return if id_group is provided

        query = query.where(Groups.id == id_group)

        result = await db.session.execute(query)
        group = result.scalar_one()

        return {
            "id": group.id,
            "name": group.name,
            "created_at": group.created_at,
            "users": await get_group_users(group.id),
            "devices": len(await get_group_devices(group.id, id_org)),
            "locations": await get_group_locations(group.id, id_org),
        }

    count = query

    if search:
        query = query.filter(Groups.name.ilike(f"%{search}%"))

    query = (
        query.limit(size).offset((page - 1) * size).order_by(Groups.created_at.desc())
    )

    response = await db.session.execute(query)
    total = await db.session.execute(count)

    groups = response.scalars().all()

    cureated_groups = []

    for group in groups:
        cureated_groups.append(
            {
                "id": group.id,
                "name": group.name,
                "created_at": group.created_at,
                "users": await get_group_users(group.id),
                "devices": len(await get_group_devices(group.id, id_org)),
                "locations": await get_group_locations(group.id, id_org),
            }
        )

    total_count = len(total.all())

    return PaginatedGroups(
        items=cureated_groups,
        total=total_count,
        pages=ceil(total_count / size),
    )


async def get_group(id_group: UUID, id_org: UUID):
    query = select(Groups).where(Groups.id_org == id_org, Groups.id == id_group)
    response = await db.session.execute(query)

    group = response.scalar_one()

    return {
        "id": group.id,
        "name": group.name,
        "created_at": group.created_at,
        "users": await get_group_users(group.id),
        "devices": len(await get_group_devices(group.id, id_org)),
        "locations": await get_group_locations(group.id, id_org),
    }


async def get_group_by_name(name: str, id_org: UUID):
    query = select(Groups).where(Groups.id_org == id_org, Groups.name == name)
    response = await db.session.execute(query)

    group = response.scalar_one()

    return {
        "id": group.id,
        "name": group.name,
        "created_at": group.created_at,
        "users": await get_group_users(group.id),
        "devices": len(await get_group_devices(group.id, id_org)),
        "locations": await get_group_locations(group.id, id_org),
    }


async def get_devices_from_group(id_group: UUID, id_org: UUID):
    query = (
        select(Device)
        .where(
            LinkGroupsDevices.id_group == id_group,
            LinkGroupsDevices.id_device == Device.id,
            Device.id_org == id_org,
        )
        .join(LinkGroupsDevices)
        .union(
            select(Device)
            .where(
                LinkGroupsLocations.id_group == id_group,
            )
            .join(
                LinkGroupsLocations,
                LinkGroupsLocations.id_location == Device.id_location,
            )
        )
    )

    response = await db.session.execute(query)

    devices = response.all()

    return devices


async def get_group_users(id_group: UUID):
    query = select(User).join(LinkGroupsUser).where(LinkGroupsUser.id_group == id_group)
    response = await db.session.execute(query)

    return response.scalars().all()


async def get_group_locations(id_group: UUID, id_org: UUID):
    query = (
        select(Location)
        .where(
            LinkGroupsLocations.id_group == id_group,
            LinkGroupsLocations.id_location == Location.id,
            Location.id_org == id_org,
        )
        .join(LinkGroupsLocations)
    )
    response = await db.session.execute(query)

    return response.unique().scalars().all()


async def get_group_location_ids(id_group: UUID, id_org: UUID):
    query = (
        select(Location.id)
        .where(
            LinkGroupsLocations.id_group == id_group,
            LinkGroupsLocations.id_location == Location.id,
            Location.id_org == id_org,
        )
        .join(LinkGroupsLocations)
    )
    response = await db.session.execute(query)

    return response.scalars().all()


async def get_group_devices(id_group: UUID, id_org: UUID):
    query = (
        select(Device)
        .where(
            LinkGroupsDevices.id_group == id_group,
            LinkGroupsDevices.id_device == Device.id,
            Device.id_org == id_org,
        )
        .join(LinkGroupsDevices)
        .union(
            select(Device)
            .where(
                LinkGroupsLocations.id_group == id_group,
            )
            .join(
                LinkGroupsLocations,
                LinkGroupsLocations.id_location == Device.id_location,
            )
        )
    )
    response = await db.session.execute(query)

    return response.scalars().all()


async def create_group(name: str, id_org: UUID):
    group = Groups(
        id=uuid4(), created_at=datetime.datetime.utcnow(), name=name, id_org=id_org
    )

    query = insert(Groups).values(group.dict()).returning(Groups)

    response = await db.session.execute(query)

    await db.session.commit()  # raise IntegrityError

    data = response.all().pop()

    return {
        "id": data.id,
        "name": data.name,
        "created_at": data.created_at,
        "users": await get_group_users(data.id),
        "devices": len(await get_group_devices(data.id, id_org)),
        "locations": await get_group_locations(data.id, id_org),
    }


async def update_group(id_group: UUID, name: str, id_org: UUID):
    query = (
        update(Groups)
        .where(Groups.id == id_group, Groups.id_org == id_org)
        .values(name=name)
        .returning(Groups)
    )

    await db.session.execute(query)

    await db.session.commit()

    return {"detail": "Group updated"}


async def delete_group(id_group: UUID, id_org: UUID):
    query_groups = delete(Groups).where(
        Groups.id == id_group,
        Groups.id_org == id_org,
    )

    query_users = delete(LinkGroupsUser).where(LinkGroupsUser.id_group == id_group)

    query_devices = delete(LinkGroupsDevices).where(
        LinkGroupsDevices.id_group == id_group
    )

    query_locations = delete(LinkGroupsLocations).where(
        LinkGroupsLocations.id_group == id_group
    )

    await db.session.execute(query_users)

    await db.session.execute(query_locations)

    await db.session.execute(query_devices)

    await db.session.execute(query_groups)

    await db.session.commit()  # raise IntegrityError

    return {"detail": "Group deleted"}


async def delete_groups(id_org: UUID, id_groups: list[UUID]):
    query_groups = delete(Groups).where(
        Groups.id_org == id_org,
        Groups.id.in_(id_groups),
    )

    query_users = delete(LinkGroupsUser).where(LinkGroupsUser.id_group.in_(id_groups))

    query_devices = delete(LinkGroupsDevices).where(
        LinkGroupsDevices.id_group.in_(id_groups)
    )

    query_locations = delete(LinkGroupsLocations).where(
        LinkGroupsLocations.id_group.in_(id_groups)
    )

    await db.session.execute(query_users)

    await db.session.execute(query_locations)

    await db.session.execute(query_devices)

    await db.session.execute(query_groups)

    await db.session.commit()  # raise IntegrityError

    return {"detail": "Groups deleted"}


async def assign_user_to_group(id_group: UUID, id_user: UUID, id_org: UUID):
    query = select(Groups).where(Groups.id == id_group, Groups.id_org == id_org)
    response = await db.session.execute(query)

    if not response.scalar_one_or_none():
        error_detail = "Group not found"

        raise HTTPException(status_code=404, detail=error_detail)

    query = select(LinkGroupsUser).where(
        LinkGroupsUser.id_group == id_group, LinkGroupsUser.id_user == id_user
    )
    response = await db.session.execute(query)

    if response.scalar_one_or_none():
        error_detail = "User already assigned to group"

        raise HTTPException(status_code=400, detail=error_detail)

    query = (
        select(User)
        .join(LinkOrgUser)
        .where(LinkOrgUser.id_org == id_org, User.id == id_user)
    )

    response = await db.session.execute(query)

    if not response.scalar_one_or_none():
        error_detail = "User not found in organization"

        raise HTTPException(status_code=404, detail=error_detail)

    query = (
        insert(LinkGroupsUser)
        .values(id=uuid.uuid4(), id_group=id_group, id_user=id_user)
        .returning(LinkGroupsUser)
    )

    response = await db.session.execute(query)

    await db.session.commit()  # raise IntegrityError

    return {"detail": "User assigned to group"}


async def remove_user_from_group(id_group: UUID, id_user: UUID, id_org: UUID):
    query = select(Groups).where(Groups.id == id_group, Groups.id_org == id_org)
    response = await db.session.execute(query)

    if not response.scalar_one_or_none():
        error_detail = "Group not found"

        raise HTTPException(status_code=404, detail=error_detail)

    query = (
        delete(LinkGroupsUser)
        .where(
            LinkGroupsUser.id_group == id_group,
            LinkGroupsUser.id_user == id_user,
        )
        .returning(LinkGroupsUser)
    )

    response = await db.session.execute(query)

    await db.session.commit()

    return {"detail": "User removed from group"}


async def assign_group_to_resource(
    id_group: UUID,
    id_resource: UUID,
    resource_type: ResourceType,
    id_org: UUID,
):
    query = select(Groups).where(Groups.id == id_group, Groups.id_org == id_org)
    response = await db.session.execute(query)

    if not response.scalar_one_or_none():
        error_detail = "Group not found"

        raise HTTPException(status_code=404, detail="Group not found")

    query = (
        select(Device.id)
        .where(Device.id == id_resource, Device.id_org == id_org)
        .union(
            select(Location.id).where(
                Location.id == id_resource, Location.id_org == id_org
            )
        )
    )

    response = await db.session.execute(query)

    if len(response.all()) == 0:
        error_detail = "Resource not found"

        raise HTTPException(status_code=404, detail="Resource not found")

    query = (
        select(LinkGroupsDevices)
        .where(
            LinkGroupsDevices.id_group == id_group,
            LinkGroupsDevices.id_device == id_resource,
        )
        .union(
            select(LinkGroupsLocations).where(
                LinkGroupsLocations.id_group == id_group,
                LinkGroupsLocations.id_location == id_resource,
            )
        )
    )

    response = await db.session.execute(query)

    if len(response.all()) > 0:
        error_detail = "Group already assigned to resource"

        raise HTTPException(
            status_code=409, detail="Group already assigned to resource"
        )

    if await is_resource_in_pseudo_group(id_resource, resource_type):
        error_detail = "Cannot assign group to resource, resource is assigned to users"

        raise HTTPException(
            status_code=400,
            detail="Cannot assign group to resource, resource is assigned to users",
        )

    match resource_type:
        case ResourceType.device:
            query = select(LinkGroupsLocations).where(
                LinkGroupsLocations.id_group == id_group
            )
            response = await db.session.execute(query)

            if len(response.all()) > 0:
                error_detail = (
                    "Group already assigned to locations, cannot assign to devices"
                )

                raise HTTPException(
                    status_code=400,
                    detail=error_detail,
                )

        case ResourceType.location:
            query = select(LinkGroupsDevices).where(
                LinkGroupsDevices.id_group == id_group
            )
            response = await db.session.execute(query)

            if len(response.all()) > 0:
                error_detail = (
                    "Group already assigned to devices, cannot assign to locations"
                )

                raise HTTPException(
                    status_code=400,
                    detail=error_detail,
                )

        case _:
            error_detail = "Invalid resource type"

            raise HTTPException(status_code=400, detail=error_detail)

    if resource_type == ResourceType.device:
        query = (
            insert(LinkGroupsDevices)
            .values(id=uuid4(), id_group=id_group, id_device=id_resource)
            .returning(LinkGroupsDevices)
        )

    elif resource_type == ResourceType.location:
        query = (
            insert(LinkGroupsLocations)
            .values(id=uuid4(), id_group=id_group, id_location=id_resource)
            .returning(LinkGroupsLocations)
        )
    else:
        error_detail = "Invalid resource type"

        raise HTTPException(status_code=400, detail=error_detail)

    response = await db.session.execute(query)
    await db.session.commit()  # This line may raise IntegrityError

    return {"detail": "Group assigned to resource"}


async def remove_group_from_resource(
    id_group: UUID,
    id_resource: UUID,
    resource_type: ResourceType,
    id_org: UUID,
):
    query = select(Groups).where(Groups.id == id_group, Groups.id_org == id_org)

    response = await db.session.execute(query)

    if not response.scalar_one_or_none():
        error_detail = "Group not found"

        raise HTTPException(status_code=404, detail=error_detail)

    match resource_type:
        case ResourceType.device:
            query = (
                delete(LinkGroupsDevices)
                .where(
                    LinkGroupsDevices.id_group == id_group,
                    LinkGroupsDevices.id_device == id_resource,
                )
                .returning(LinkGroupsDevices)
            )
        case ResourceType.location:
            query = (
                delete(LinkGroupsLocations)
                .where(
                    LinkGroupsLocations.id_group == id_group,
                    LinkGroupsLocations.id_location == id_resource,
                )
                .returning(LinkGroupsLocations)
            )
        case _:
            error_detail = "Invalid resource type"

            raise HTTPException(status_code=400, detail=error_detail)

    response = await db.session.execute(query)

    await db.session.commit()  # raise IntegrityError

    return {"detail": "Group removed from resource"}


async def assign_user_to_resource(
    id_user: UUID,
    id_resource: UUID,
    resource_type: ResourceType,
    id_org: UUID,
):
    query = (
        select(Device.id)
        .where(Device.id == id_resource, Device.id_org == id_org)
        .union(
            select(Location.id).where(
                Location.id == id_resource, Location.id_org == id_org
            )
        )
    )

    response = await db.session.execute(query)

    if len(response.all()) == 0:
        error_detail = "Resource not found"

        raise HTTPException(status_code=404, detail=error_detail)

    if await is_resource_in_group(id_resource, resource_type):
        error_detail = (
            "Cannot assign user to resource, resource is assigned to one group or more"
        )

        raise HTTPException(status_code=400, detail=error_detail)

    query = (
        select(User)
        .join(LinkOrgUser)
        .where(LinkOrgUser.id_org == id_org, LinkOrgUser.id_user == id_user)
    )

    response = await db.session.execute(query)

    if not response.scalar_one_or_none():
        error_detail = "User not found"

        raise HTTPException(status_code=404, detail=error_detail)

    query = (
        select(LinkUserDevices)
        .where(
            LinkUserDevices.id_user == id_user,
            LinkUserDevices.id_device == id_resource,
        )
        .union(
            select(LinkUserLocations).where(
                LinkUserLocations.id_user == id_user,
                LinkUserLocations.id_location == id_resource,
            )
        )
    )

    response = await db.session.execute(query)

    if len(response.all()) > 0:
        error_detail = "User already assigned to resource"

        raise HTTPException(status_code=409, detail=error_detail)

    match resource_type:
        case ResourceType.device:
            query = (
                select(LinkUserLocations)
                .join_from(
                    Device,
                    LinkUserLocations,
                    LinkUserLocations.id_location == Device.id_location,
                )
                .where(Device.id == id_resource)
            )
            response = await db.session.execute(query)

            if len(response.all()) > 0:
                error_detail = "Device's location already assigned to users, cannot assign device to user"

                raise HTTPException(status_code=400, detail=error_detail)

        case ResourceType.location:
            query = (
                select(LinkUserDevices)
                .join_from(
                    Device,
                    LinkUserDevices,
                    LinkUserDevices.id_device == Device.id,
                )
                .where(Device.id_location == id_resource)
            )
            response = await db.session.execute(query)

            if len(response.all()) > 0:
                error_detail = "Location's device already assigned to users, cannot assign location to single user"

                raise HTTPException(status_code=400, detail=error_detail)
        case _:
            error_detail = "Invalid resource type"

            raise HTTPException(status_code=400, detail=error_detail)

    if resource_type == ResourceType.device:
        query = (
            insert(LinkUserDevices)
            .values(id=uuid4(), id_user=id_user, id_device=id_resource)
            .returning(LinkUserDevices)
        )

    elif resource_type == ResourceType.location:
        query = (
            insert(LinkUserLocations)
            .values(id=uuid4(), id_user=id_user, id_location=id_resource)
            .returning(LinkUserLocations)
        )

    response = await db.session.execute(query)

    await db.session.commit()

    return {"detail": "User assigned to resource"}


async def remove_user_from_resource(
    id_resource: UUID,
    id_user: UUID,
    resource_type: ResourceType,
    id_org: UUID,
):
    query = (
        select(User)
        .join(LinkOrgUser)
        .where(LinkOrgUser.id_org == id_org, LinkOrgUser.id_user == id_user)
    )

    response = await db.session.execute(query)

    if not response.scalar_one_or_none():
        error_detail = "User not found"

        raise HTTPException(status_code=404, detail=error_detail)

    match resource_type:
        case ResourceType.device:
            query = (
                delete(LinkUserDevices)
                .where(
                    LinkUserDevices.id_device == id_resource,
                    LinkUserDevices.id_user == id_user,
                )
                .returning(LinkUserDevices)
            )
        case ResourceType.location:
            query = (
                delete(LinkUserLocations)
                .where(
                    LinkUserLocations.id_location == id_resource,
                    LinkUserLocations.id_user == id_user,
                )
                .returning(LinkUserLocations)
            )
        case _:
            error_detail = "Invalid resource type"

            raise HTTPException(status_code=400, detail=error_detail)

    response = await db.session.execute(query)

    await db.session.commit()

    return {"detail": "User removed from resource"}


async def get_groups_from_resource(
    id_resource: UUID,
    resource_type: ResourceType,
    id_org: UUID,
):
    query = None

    match resource_type:
        case ResourceType.device:
            query = (
                select(Groups)
                .where(Groups.id_org == id_org)
                .join_from(
                    LinkGroupsDevices,
                    Groups,
                    LinkGroupsDevices.id_group == Groups.id,
                )
                .join_from(
                    LinkGroupsDevices,
                    Device,
                    LinkGroupsDevices.id_device == Device.id,
                )
                .where(Device.id == id_resource)
            )
        case ResourceType.location:
            query = (
                select(Groups)
                .where(Groups.id_org == id_org)
                .join_from(
                    LinkGroupsLocations,
                    Groups,
                    LinkGroupsLocations.id_group == Groups.id,
                )
                .join_from(
                    LinkGroupsLocations,
                    Location,
                    LinkGroupsLocations.id_location == Location.id,
                )
                .where(Location.id == id_resource)
            )
        case _:
            error_detail = "Invalid resource type"

            raise HTTPException(status_code=400, detail=error_detail)

    response = await db.session.execute(query)

    groups = response.scalars().all()

    return groups


async def get_users_from_resource(
    id_resource: UUID,
    resource_type: ResourceType,
    id_org: UUID,
):
    query = None

    match resource_type:
        case ResourceType.device:
            query = (
                select(User)
                .join_from(
                    User,
                    LinkUserDevices,
                    LinkUserDevices.id_user == User.id,
                )
                .where(LinkUserDevices.id_device == id_resource)
                .join(LinkOrgUser)
                .where(LinkOrgUser.id_org == id_org)
            )
        case ResourceType.location:
            query = (
                select(User)
                .join_from(
                    User,
                    LinkUserLocations,
                    LinkUserLocations.id_user == User.id,
                )
                .where(LinkUserLocations.id_location == id_resource)
                .join(LinkOrgUser)
                .where(LinkOrgUser.id_org == id_org)
            )

    response = await db.session.execute(query)

    users = response.scalars().all()

    return users


async def get_groups_from_user(
    id_user: UUID,
    id_org: UUID,
):
    query = (
        select(Groups)
        .join_from(
            Groups,
            LinkGroupsUser,
            Groups.id == LinkGroupsUser.id_group,
        )
        .where(LinkGroupsUser.id_user == id_user, Groups.id_org == id_org)
    )
    response = await db.session.execute(query)
    groups = response.scalars().all()
    cureated_groups = []

    for group in groups:
        cureated_groups.append(
            {
                "id": group.id,
                "name": group.name,
                "created_at": group.created_at,
                "devices": await get_group_devices(group.id, id_org),
                "locations": await get_group_location_ids(group.id, id_org),
            }
        )
    return cureated_groups


async def dissolve_user_access(
    id_resource: UUID,
    resource_type: ResourceType,
    id_org: UUID,
):
    query = (
        select(Device.id)
        .where(Device.id == id_resource, Device.id_org == id_org)
        .union(
            select(Location.id).where(
                Location.id == id_resource, Location.id_org == id_org
            )
        )
    )

    response = await db.session.execute(query)

    if len(response.scalars().all()) == 0:
        error_detail = "Resource not found or not owned by organization"

        raise HTTPException(status_code=404, detail=error_detail)

    match resource_type:
        case ResourceType.device:
            query = (
                delete(LinkUserDevices)
                .where(LinkUserDevices.id_device == id_resource)
                .returning(LinkUserDevices)
            )
        case ResourceType.location:
            query = (
                delete(LinkUserLocations)
                .where(LinkUserLocations.id_location == id_resource)
                .returning(LinkUserLocations)
            )
        case _:
            error_detail = "Invalid resource type"

            raise HTTPException(status_code=400, detail=error_detail)

    response = await db.session.execute(query)

    await db.session.commit()

    return {"detail": "User access dissolved"}


async def get_resource_permission(
    id_resource: UUID,
    resource_type: ResourceType,
    id_org: UUID,
):
    query = (
        select(Device.id)
        .where(Device.id == id_resource, Device.id_org == id_org)
        .union(
            select(Location.id).where(
                Location.id == id_resource, Location.id_org == id_org
            )
        )
    )

    response = await db.session.execute(query)

    if len(response.scalars().all()) == 0:
        error_detail = "Resource not found or not owned by organization"

        raise HTTPException(status_code=404, detail=error_detail)

    match resource_type:
        case ResourceType.device:
            query = (
                select(LinkUserLocations)
                .join_from(
                    Device,
                    LinkUserLocations,
                    LinkUserLocations.id_location == Device.id_location,
                )
                .where(Device.id == id_resource)
                .union(
                    select(LinkGroupsLocations)
                    .join_from(
                        Device,
                        LinkGroupsLocations,
                        LinkGroupsLocations.id_location == Device.id_location,
                    )
                    .where(Device.id == id_resource)
                )
            )
            response = await db.session.execute(query)

            if len(response.all()) > 0:
                error_detail = "Device is assigned at location level"

                raise HTTPException(status_code=400, detail=error_detail)

        case ResourceType.location:
            query = (
                select(LinkUserDevices)
                .join_from(
                    Device,
                    LinkUserDevices,
                    LinkUserDevices.id_device == Device.id,
                )
                .where(Device.id_location == id_resource)
                .union(
                    select(LinkGroupsDevices)
                    .join_from(
                        Device,
                        LinkGroupsDevices,
                        LinkGroupsDevices.id_device == Device.id,
                    )
                    .where(Device.id_location == id_resource)
                )
            )
            response = await db.session.execute(query)

            if len(response.all()) > 0:
                error_detail = "Some devices are assigned at location level"

                raise HTTPException(status_code=400, detail=error_detail)

        case _:
            error_detail = "Invalid resource type"

            raise HTTPException(status_code=400, detail=error_detail)

    return {"detail": "Resource can be assigned to user or group"}


async def is_resource_in_pseudo_group(
    id_resource: UUID,
    resource_type: ResourceType,
) -> bool:
    query = None

    match resource_type:
        case ResourceType.device:
            query = select(LinkUserDevices).where(
                LinkUserDevices.id_device == id_resource
            )
        case ResourceType.location:
            query = select(LinkUserLocations).where(
                LinkUserLocations.id_location == id_resource
            )
        case _:
            raise HTTPException(status_code=400, detail="Invalid resource type")

    response = await db.session.execute(query)

    return True if len(response.all()) > 0 else False


async def is_resource_in_group(
    id_resource: UUID,
    resource_type: ResourceType,
) -> bool:
    query = None

    match resource_type:
        case ResourceType.device:
            query = select(LinkGroupsDevices).where(
                LinkGroupsDevices.id_device == id_resource,
            )
        case ResourceType.location:
            query = select(LinkGroupsLocations).where(
                LinkGroupsLocations.id_location == id_resource,
            )
        case _:
            raise HTTPException(status_code=400, detail="Invalid resource type")

    response = await db.session.execute(query)

    return True if len(response.all()) > 0 else False


async def is_device_assigned_to_user(
    id_device: UUID,
    id_user: UUID,
) -> bool:
    # is device assigned to group or users?
    query = (
        select(
            Device.id,
            LinkUserDevices.id,
            LinkGroupsDevices.id,
            LinkUserLocations.id,
            LinkGroupsLocations.id,
        )
        .where(Device.id == id_device)
        .outerjoin(
            LinkUserDevices,
            LinkUserDevices.id_device == Device.id,
        )
        .outerjoin(
            LinkUserLocations,
            LinkUserLocations.id_location == Device.id_location,
        )
        .outerjoin(
            LinkGroupsDevices,
            LinkGroupsDevices.id_device == Device.id,
        )
        .outerjoin(
            LinkGroupsLocations,
            LinkGroupsLocations.id_location == Device.id_location,
        )
        .where(
            or_(
                LinkUserDevices.id_device == Device.id,
                LinkUserLocations.id_location == Device.id_location,
                LinkGroupsDevices.id_device == Device.id,
                LinkGroupsLocations.id_location == Device.id_location,
            )
        )
    )

    response = await db.session.execute(query)

    # device is not assigned to user or group, so all users have access
    if len(response.all()) == 0:
        return True

    # does user have access to device?
    query = (
        select(Device)
        .where(Device.id == id_device)
        .outerjoin(
            LinkGroupsUser,
            LinkGroupsUser.id_user == id_user,
        )
        .outerjoin(LinkGroupsDevices, LinkGroupsDevices.id_device == Device.id)
        .outerjoin(
            LinkGroupsLocations,
            LinkGroupsLocations.id_location == Device.id_location,
        )
        .outerjoin(
            LinkUserDevices,
            LinkUserDevices.id_device == Device.id,
        )
        .outerjoin(
            LinkUserLocations,
            LinkUserLocations.id_location == Device.id_location,
        )
        .where(
            or_(
                LinkGroupsUser.id_group == LinkGroupsDevices.id_group,
                LinkGroupsUser.id_group == LinkGroupsLocations.id_group,
                LinkUserDevices.id_user == id_user,
                LinkUserLocations.id_user == id_user,
            ),
        )
    )

    response = await db.session.execute(query)

    return True if len(response.unique().all()) > 0 else False

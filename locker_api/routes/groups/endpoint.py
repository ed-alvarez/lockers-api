from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from fastapi import APIRouter, Depends, HTTPException
from pydantic import conint

from util.response import BasicResponse

from ..device.model import Device
from ..member.model import RoleType
from ..organization.controller import is_sub_org
from ..user.model import User
from . import controller
from .model import Groups, PaginatedGroups, ResourceType

router = APIRouter(tags=["groups"])


@router.get("/partner/groups", response_model=PaginatedGroups | Groups.Read)
async def get_groups(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_group: Optional[UUID] = None,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all groups: `/partner/groups?page=1&size=50`
    ### * Search groups: `/partner/groups?search=Group%20A`
    ### * Get a single group: `/partner/groups?id_group=UUID`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_group | UUID | The unique ID of a group | Single |
    | search | str | Search | List |
    """

    # Logging at the start
    # Logging input objects
    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org
    groups = await controller.get_groups(page, size, id_group, search, current_org)
    # Logging result
    # Logging at the end

    return groups


@router.post("/partner/groups", status_code=201, response_model=Groups.Read)
async def create_group(
    name: str,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    group_creation_result = await controller.create_group(name, current_org)
    # Logging result
    # Logging at the end

    return group_creation_result


@router.put("/partner/groups/{id_group}", response_model=BasicResponse)
async def update_group(
    id_group: UUID,
    name: str,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.update_group(id_group, name, current_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/groups/{id_group}", response_model=BasicResponse)
async def delete_group(
    id_group: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.delete_group(id_group, current_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/groups", response_model=BasicResponse)
async def delete_groups(
    id_groups: list[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin",
        )
    return await controller.delete_groups(current_org, id_groups)


@router.patch("/partner/groups/{id_group}/assign", response_model=BasicResponse)
async def assign_group_to_resource(
    id_group: UUID,
    id_resource: UUID,
    resource_type: ResourceType,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.assign_group_to_resource(
        id_group, id_resource, resource_type, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/groups/{id_group}/remove", response_model=BasicResponse)
async def remove_group_from_resource(
    id_group: UUID,
    id_resource: UUID,
    resource_type: ResourceType,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.remove_group_from_resource(
        id_group, id_resource, resource_type, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/groups/{id_group}/assign-user", response_model=BasicResponse)
async def assign_user_to_group(
    id_group: UUID,
    id_user: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.assign_user_to_group(id_group, id_user, current_org)
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/groups/{id_group}/remove-user", response_model=BasicResponse)
async def remove_user_from_group(
    id_group: UUID,
    id_user: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.remove_user_from_group(id_group, id_user, current_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/groups/{id_group}/devices", response_model=list[Device.Read])
async def get_devices_from_group(
    id_group: UUID,
    current_org: UUID = Depends(get_current_org),
):
    """Get devices from a group."""

    # Logging at the start
    # Logging input objects

    # Perform the action
    devices = await controller.get_devices_from_group(id_group, current_org)
    # Logging result
    # Logging at the end

    return devices


@router.get("/partner/resources/{id_resource}/groups", response_model=list[Groups])
async def get_groups_from_resource(
    id_resource: UUID,
    resource_type: ResourceType,
    current_org: UUID = Depends(get_current_org),
):
    """Get groups from a resource. resource can be a location or a device."""

    # Logging at the start

    groups = await controller.get_groups_from_resource(
        id_resource, resource_type, current_org
    )
    # Logging result
    # Logging at the end

    return groups


@router.get("/partner/resources/{id_resource}/permission", response_model=BasicResponse)
async def get_resource_permission(
    id_resource: UUID,
    resource_type: ResourceType,
    current_org: UUID = Depends(get_current_org),
):
    """Returns if the given resource can be assigned to a group or a user,
    or if it has already been assigned (at location level or at device level)
    """

    # Logging at the start

    permission = await controller.get_resource_permission(
        id_resource, resource_type, current_org
    )
    # Logging result
    # Logging at the end

    return permission


@router.patch(
    "/partner/resources/{id_resource}/assign-user", response_model=BasicResponse
)
async def assign_user_to_resource(
    id_resource: UUID,
    id_user: UUID,
    resource_type: ResourceType,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Assign a user to a resource. The resource can be a location or a device."""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    response = await controller.assign_user_to_resource(
        id_user, id_resource, resource_type, current_org
    )
    # Logging result
    # Logging at the end

    return response


@router.patch(
    "/partner/resources/{id_resource}/remove-user", response_model=BasicResponse
)
async def remove_user_from_resource(
    id_resource: UUID,
    id_user: UUID,
    resource_type: ResourceType,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Remove a user from a resource. The resource can be a location or a device."""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    response = await controller.remove_user_from_resource(
        id_resource, id_user, resource_type, current_org
    )
    # Logging result
    # Logging at the end

    return response


@router.get("/partner/resources/{id_resource}/users", response_model=list[User.Read])
async def get_users_from_resource(
    id_resource: UUID,
    resource_type: ResourceType,
    current_org: UUID = Depends(get_current_org),
):
    """Get users from a resource. resource can be a location or a device."""

    # Logging at the start
    # Logging input objects

    users = await controller.get_users_from_resource(
        id_resource, resource_type, current_org
    )
    # Logging result
    # Logging at the end

    return users


@router.delete("/partner/resources/{id_resource}", response_model=BasicResponse)
async def dissolve_user_access(
    id_resource: UUID,
    resource_type: ResourceType,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Dissolve all access from a resource. The resource can be a location or a device."""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.dissolve_user_access(
        id_resource, resource_type, current_org
    )
    # Logging result
    # Logging at the end

    return result

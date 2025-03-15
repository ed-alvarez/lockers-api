from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, HTTPException
from pydantic import conint


from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import LockerWall, PaginatedLockerWalls

router = APIRouter(tags=["locker-walls"])


@router.get("/mobile/locker-walls", response_model=PaginatedLockerWalls)
async def get_mobile_locker_walls(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    search: Optional[str] = None,
    id_location: Optional[UUID] = None,
    id_org: UUID = Depends(get_current_user_id_org),
):
    # Logging at the start

    result = await controller.get_locker_walls(page, size, search, id_org, id_location)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/locker-walls", response_model=PaginatedLockerWalls)
async def get_partner_locker_walls(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    search: Optional[str] = None,
    id_location: Optional[UUID] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    # Logging at the start

    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    result = await controller.get_locker_walls(page, size, search, id_org, id_location)
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/locker-walls", status_code=201, response_model=LockerWall.Read)
async def create_partner_locker_wall(
    locker_wall: LockerWall.Write,
    id_org: UUID = Depends(get_current_org),
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

    result = await controller.create_locker_wall(locker_wall, id_org)
    # Logging result
    # Logging at the end

    return result


@router.put("/partner/locker-walls/{id_locker_wall}", response_model=LockerWall.Read)
async def update_partner_locker_wall(
    id_locker_wall: UUID,
    locker_wall: LockerWall.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.update_locker_wall(id_locker_wall, locker_wall, id_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/locker-walls/{id_locker_wall}", response_model=LockerWall.Read)
async def delete_partner_locker_wall(
    id_locker_wall: UUID,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging warning
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.delete_locker_wall(id_locker_wall, id_org)
    # Logging result
    # Logging at the end

    return result

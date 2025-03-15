from typing import List, Optional
from uuid import UUID

from auth.cognito import (
    get_current_org,
    get_current_user,
    get_current_user_pool,
    get_permission,
)
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload


from . import controller
from .model import (
    BasicResponse,
    Member,
    MemberUpdate,
    MemberPatch,
    PaginatedMembers,
    RoleType,
)

router = APIRouter(tags=["members"])


@router.get("/partner/members/self", response_model=Member)
async def get_self(
    user_pool_id: str = Depends(get_current_user_pool),
    user_id: str = Depends(get_current_user),
):
    # Logging at the start
    # Logging input objects

    result = await controller.get_self(user_pool_id, user_id)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/members", response_model=PaginatedMembers | Member)
async def get_members(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    user_id: Optional[str] = None,
    search: Optional[str] = None,
    user_pool_id: str = Depends(get_current_user_pool),
    permission: RoleType = Depends(get_permission),
):
    """
    # Usage:
    ### * Get all members: `/partner/members?page=1&size=50`
    ### * Search members: `/partner/members?search=John`
    ### * Get a single member: `/partner/members?user_id=UUID`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | user_id | UUID | The unique ID of a member | Single |
    | search | str | Search | List |
    """

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.get_users(page, size, user_id, search, user_pool_id)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/members/{user_id}", response_model=Member)
async def get_member(
    user_id: str,
    user_pool_id: str = Depends(get_current_user_pool),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.get_user(user_pool_id, user_id)
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/members", response_model=Member)
async def create_member(
    email: str,
    member: MemberUpdate,
    user_pool_id: str = Depends(get_current_user_pool),
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.create_user(user_pool_id, current_org, email, member)
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/members/csv")
async def upload_members_csv(
    file: UploadFile = File(...),
    permission: RoleType = Depends(get_permission),
    id_org: UUID = Depends(get_current_org),
):
    """
    Endpoint to upload and process CSV files containing device data.
    """

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    if file.filename.split(".")[-1].lower() != "csv":
        # Logging of ERROR
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        id_org,
        file,
        Member,
        controller.create_members_csv,
        controller.update_members_csv,
    )

    # Logging result
    # Logging at the end

    return result


@router.put("/partner/members/{user_id}", response_model=BasicResponse)
async def update_member(
    user_id: str,
    member: MemberUpdate,
    user_pool_id: str = Depends(get_current_user_pool),
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.update_user(user_pool_id, current_org, user_id, member)
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/members/{user_id}", response_model=BasicResponse)
async def patch_member(
    user_id: str,
    member: MemberPatch,
    user_pool_id: str = Depends(get_current_user_pool),
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.patch_user(user_pool_id, current_org, user_id, member)
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/members/", response_model=BasicResponse)
async def patch_members(
    user_ids: List[UUID],
    member: MemberPatch,
    user_pool_id: str = Depends(get_current_user_pool),
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.patch_users(user_pool_id, current_org, user_ids, member)

    return result


@router.patch("/partner/members/{user_id}/status", response_model=BasicResponse)
async def switch_member_status(
    user_id: str,
    enabled: bool,
    user_pool_id: str = Depends(get_current_user_pool),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.switch_member_status(user_pool_id, user_id, enabled)
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/members/{user_id}/verify", response_model=BasicResponse)
async def verify_member(
    user_id: str,
    user_pool_id: str = Depends(get_current_user_pool),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.verify_email(user_pool_id, user_id)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/members/{user_id}", response_model=BasicResponse)
async def delete_member(
    user_id: str,
    user_pool_id: str = Depends(get_current_user_pool),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_user(user_pool_id, user_id)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/members", response_model=BasicResponse)
async def delete_members(
    user_ids: List[str],
    user_pool_id: str = Depends(get_current_user_pool),
    permission: RoleType = Depends(get_permission),
):
    """Delete multiple members"""

    # Logging at the start

    if permission != RoleType.admin:
        # Logging warning
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_users(user_pool_id, user_ids)
    # Logging result
    # Logging at the end

    return result

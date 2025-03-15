from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user, get_current_user_id_org
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload

from util.response import BasicResponse

from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import Membership, PaginatedMemberships, SubscriptionResponse

router = APIRouter(tags=["memberships"])


@router.get("/mobile/memberships/current", response_model=Membership.Read)
async def mobile_get_current_membership(
    current_org: UUID = Depends(get_current_user_id_org),
    current_user: UUID = Depends(get_current_user),
):
    """Get the current Membership for a mobile user"""

    # Logging at the start

    result = await controller.get_current_membership(current_org, current_user)
    # Logging result
    # Logging at the end

    return result


@router.get(
    "/mobile/memberships", response_model=PaginatedMemberships | Membership.Read
)
async def mobile_get_memberships(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_membership: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_user_id_org),
    id_location: Optional[UUID] = None,
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all memberships: `/mobile/memberships?page=1&size=50`
    ### * Search memberships: `/mobile/memberships?search=Gym%20Only`
    ### * Get a single membership: `/mobile/memberships?id_membership=UUID`
    ### * Get a single membership by key: `/mobile/memberships?key=name&value=Gym%20Only`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_membership | UUID | The unique ID of a membership | Single |
    | key | str | Parameter to look for a single membership | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    """
    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org
    result = await controller.get_memberships(
        current_org, page, size, id_membership, key, value, search, False, id_location
    )
    # Logging result
    # Logging at the end

    return result


@router.post("/mobile/memberships/{id_membership}", response_model=SubscriptionResponse)
async def mobile_subscribe(
    id_membership: UUID,
    payment_method: Optional[str] = None,
    current_org: UUID = Depends(get_current_user_id_org),
    current_user: UUID = Depends(get_current_user),
):
    """Subscribe to a Membership for a mobile user"""

    # Logging at the start

    result = await controller.subscribe(
        id_membership, current_org, current_user, payment_method
    )
    # Logging result
    # Logging at the end

    return result


@router.delete("/mobile/memberships", response_model=BasicResponse)
async def mobile_cancel_subscription(
    current_org: UUID = Depends(get_current_user_id_org),
    current_user: UUID = Depends(get_current_user),
):
    """Cancel a Membership for a mobile user"""

    # Logging at the start
    # Logging input objects

    result = await controller.cancel_subscription(current_org, current_user)
    # Logging result
    # Logging at the end

    return result


@router.get(
    "/partner/memberships", response_model=PaginatedMemberships | Membership.Read
)
async def partner_get_memberships(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_membership: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    subscribed: Optional[bool] = False,
    current_org: UUID = Depends(get_current_org),
):
    """
    # Usage:
    ### * Get all memberships: `/partner/memberships?page=1&size=50`
    ### * Search memberships: `/partner/memberships?search=Gym%20Only`
    ### * Get a single membership: `/partner/memberships?id_membership=UUID`
    ### * Get a single membership by key: `/partner/memberships?key=name&value=Gym%20Only`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_membership | UUID | The unique ID of a membership | Single |
    | key | str | Parameter to look for a single membership | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    """

    # Logging at the start

    # Permission checks and business logic here

    result = await controller.get_memberships(
        current_org, page, size, id_membership, key, value, search, subscribed, None
    )
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/memberships", response_model=Membership.Read)
async def partner_create_membership(
    membership: Membership.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Create a new membership"""

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging warning
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.partner_create_membership(membership, current_org)
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/memberships/csv")
async def upload_memberships_csv(
    file: UploadFile = File(...),
    permission: RoleType = Depends(get_permission),
    id_org: UUID = Depends(get_current_org),
):
    """
    Endpoint to upload and process CSV files containing device data.
    """

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    if file.filename.split(".")[-1].lower() != "csv":
        # Logging of ERROR
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        id_org,
        file,
        Membership.Write,
        controller.create_membership_csv,
        controller.update_membership_csv,
    )

    # Logging result
    # Logging at the end

    return result


@router.put("/partner/memberships/{id_membership}", response_model=Membership.Read)
async def partner_update_membership(
    id_membership: UUID,
    membership: Membership.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Update a membership"""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging warning
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.partner_update_membership(
        id_membership, membership, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/memberships/{id_membership}", response_model=Membership.Read)
async def partner_delete_membership(
    id_membership: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete a membership, this will also cancel all the subscriptions to this membership"""

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging warning
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.partner_delete_membership(id_membership, current_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/memberships", response_model=BasicResponse)
async def partner_delete_memberships(
    id_memberships: list[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete multiple memberships, this will also cancel all the subscriptions to these memberships"""
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )
    return await controller.partner_delete_memberships(id_memberships, current_org)


@router.patch("/partner/memberships/{id_membership}", response_model=Membership.Read)
async def partner_switch_membership(
    id_membership: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Activate/Deactivate a membership, this will only affect new subscriptions"""

    # Log when entering the endpoint

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.partner_switch_membership(id_membership, current_org)
    # Log the result
    # Log when exiting the endpoint successfully

    return result

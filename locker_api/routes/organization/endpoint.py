from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic import conint
from util.images import ImagesService

from util.response import BasicResponse

from ..member.model import MemberUpdate, RoleType
from ..organization.controller import is_sub_org
from ..settings.model import OrgSettings
from ..white_label.model import WhiteLabel
from . import controller
from .model import Org, OrgReadPublic, PaginatedOrgs, OrgFeatures

router = APIRouter(tags=["organizations"])


@router.get("/organization", response_model=OrgReadPublic)
async def public_get_org(name: str):
    """
    This endpoint returns public information to our frontend
    and it is used to configure the AWS Amplify SDK.

    Using this information we can manage tenant logins."""

    # Logging at the start
    # Logging input objects

    result = await controller.public_get_org(name)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/organizations/self", response_model=Org.Read)
async def get_org(current_org: UUID = Depends(get_current_org)):
    """Get organization details for the current organization"""

    # Logging at the start
    # Logging input objects

    result = await controller.get_org(current_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/organizations", response_model=PaginatedOrgs)
async def get_orgs(
    current_org: UUID = Depends(get_current_org),
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    expand: Optional[bool] = False,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    permission: RoleType = Depends(get_permission),
    target_org: Optional[UUID] = None,
):
    """
    Retrieve a list of organizations with pagination.
    Requires admin or member role permissions.
    """

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org

    result = await controller.get_orgs(current_org, page, size, expand, search, active)
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/organizations", status_code=201, response_model=dict)
async def create_org(
    email: str = Form(...),
    features: OrgFeatures = Depends(OrgFeatures.as_form),
    member: MemberUpdate = Depends(MemberUpdate.as_form),
    white_label: WhiteLabel.Write = Depends(WhiteLabel.Write.as_form),
    settings: OrgSettings.Write = Depends(OrgSettings.Write.as_form),
    image: Optional[UploadFile] = None,
    current_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.create_org(
        member,
        settings,
        email,
        white_label,
        features,
        current_org,
        images_service,
        image,
    )
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/organizations/{id_org}", response_model=OrgFeatures)
async def patch_org_features(
    id_org: UUID,
    features: OrgFeatures,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.patch_org_features(id_org, features, current_org)

    return result


@router.delete("/partner/organizations/{id_org}/cancel", response_model=BasicResponse)
async def restore_org(
    id_org: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.restore_org(id_org, current_org)
    return result


@router.delete("/partner/organizations/{id_org}", response_model=BasicResponse)
async def archive_org(
    id_org: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.archive_org(id_org, current_org)
    return result


@router.get("/mobile/organization", response_model=Org.Read)
async def mobile_get_current_org(current_org: UUID = Depends(get_current_user_id_org)):
    """
    Fetch the current organization details for a mobile client.
    """

    # Logging at the start
    # Logging input objects

    result = await controller.mobile_get_org(current_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/mobile/organizations/{user_pool}", response_model=PaginatedOrgs)
async def mobile_get_orgs(
    user_pool: str,
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
):
    """Since this endpoint can relate to multiple tenants, we need to pass in the user_pool.
    this will return all the orgs for that tenant.

    The user pool will not change in the entire development process.
    """

    # Logging at the start
    # Logging input parameters

    result = await controller.mobile_get_orgs(user_pool, page, size)
    # Logging result
    # Logging at the end

    return result

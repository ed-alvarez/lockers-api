from typing import List, Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission, get_current_user_pool
from auth.user import get_current_user, get_current_user_id_org
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import conint
from util.images import ImagesService

from util.response import BasicResponse

from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import Issue, IssueStatus, PaginatedIssues

router = APIRouter(tags=["issues"])


@router.get("/mobile/issues", response_model=PaginatedIssues | Issue.Read)
async def get_mobile_issues(
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
    page: conint(ge=1) = 1,
    size: conint(ge=1) = 50,
    id_issue: Optional[UUID] = None,
    search: Optional[str] = None,
):
    """
    # Usage:
    ### * Get all issues: `/mobile/issues?page=1&size=50`
    ### * Search issues: `/mobile/issues?search=Problem%20with%20the%20locker`
    ### * Get a single issue: `/mobile/issues?id_issue=UUID`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_issue | UUID | The unique ID of an issue | Single |
    | search | str | Search | List |
    """

    # Logging at the start
    # Logging input parameters

    # Controller method that actually handles the logic for fetching issues
    issues = await controller.get_mobile_issues(
        id_user, id_org, page, size, id_issue, search
    )

    # Logging the result
    # Logging at the end

    return issues


@router.post("/mobile/issues", response_model=Issue.Read)
async def create_mobile_issue(
    images: Optional[list[UploadFile]] = None,
    id_event: Optional[UUID] = None,
    issue: Issue.Write = Depends(Issue.Write.as_form),
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
    images_service: ImagesService = Depends(ImagesService),
):
    """
    Create a mobile issue with associated images.
    """

    # Controller method that actually handles the logic for creating an issue
    created_issue = await controller.create_issue(
        id_event, issue, images, id_user, id_org, images_service, None
    )

    return created_issue


@router.get("/partner/issues", response_model=PaginatedIssues | Issue.Read)
async def get_partner_issues(
    id_org: UUID = Depends(get_current_org),
    page: conint(ge=1) = 1,
    size: conint(ge=1) = 50,
    id_issue: Optional[UUID] = None,
    search: Optional[str] = None,
    target_org: Optional[UUID] = None,
    current_user_pool=Depends(get_current_user_pool),
):
    """
    # Usage:
    ### * Get all issues: `/partner/issues?page=1&size=50`
    ### * Search issues: `/partner/issues?search=Problem%20with%20the%20locker`
    ### * Get a single issue: `/partner/issues?id_issue=UUID`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_issue | UUID | The unique ID of an issue | Single |
    | search | str | Search | List |
    """

    # Logging at the start

    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    issues = await controller.get_partner_issues(
        id_org, page, size, id_issue, search, current_user_pool
    )

    # Logging the result
    # Logging at the end

    return issues


@router.post("/partner/issues", response_model=Issue.Read)
async def create_partner_issue(
    images: Optional[list[UploadFile]] = None,
    id_event: Optional[UUID] = None,
    issue: Issue.Write = Depends(Issue.Write.as_form),
    id_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    user_pool_id: UUID = Depends(get_current_user_pool),
):
    """
    Create a new partner issue with optional images and event ID.
    """
    new_issue = await controller.create_issue(
        id_event, issue, images, issue.id_user, id_org, images_service, user_pool_id
    )

    return new_issue


@router.put("/partner/issues/{id_issue}", response_model=Issue.Read)
async def update_partner_issue(
    id_issue: UUID,
    updated_issue: Issue.Write = Depends(Issue.Write.as_form),
    id_org: UUID = Depends(get_current_org),
    images: Optional[list[UploadFile]] = None,
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
    user_pool_id: UUID = Depends(get_current_user_pool),
):
    """
    Update an existing partner issue by ID.
    """
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member."
        )

    updated_issue_result = await controller.update_issue(
        id_issue, id_org, updated_issue, images_service, images, user_pool_id
    )

    return updated_issue_result


@router.patch("/partner/issues/{id_issue}", response_model=Issue.Read)
async def switch_issue_status(
    id_issue: UUID,
    status: IssueStatus,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Switches the status of an issue from the current user's organization."""

    # Logging at the start
    # Logging input parameters

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member."
        )

    issue_status_result = await controller.switch_issue_status(id_issue, status, id_org)

    # Logging the result
    # Logging at the end

    return issue_status_result


@router.delete("/partner/issues/{id_issue}", response_model=Issue.Read)
async def delete_issue(
    id_issue: UUID,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Deletes an issue from the current user's organization."""

    # Logging at the start
    # Logging input parameters

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging permission issue
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member."
        )

    delete_result = await controller.delete_issue(id_issue, id_org)

    # Logging the result
    # Logging at the end

    return delete_result


@router.delete("/partner/issues", response_model=BasicResponse)
async def delete_issues(
    id_issues: List[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete multiple Issues"""

    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_issues(id_issues, current_org)
    # Logging result
    # Logging at the end

    return result

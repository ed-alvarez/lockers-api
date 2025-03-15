from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload

from util.response import BasicResponse

from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import Condition, PaginatedConditions

router = APIRouter(tags=["conditions"])


@router.get("/mobile/conditions", response_model=PaginatedConditions | Condition.Read)
async def mobile_get_conditions(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_condition: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_user_id_org),
):
    """
    # Usage:
    ### * Get all conditions: `/mobile/conditions?page=1&size=10`
    ### * Get condition by id: `/mobile/conditions?id_condition=123e4567-e89b-12d3-a456-426614174000`
    ### * Get condition by key and value: `/mobile/conditions?key=name&value=example`
    ### * Get condition by search: `/mobile/conditions?search=condition`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_condition | UUID | id of condition | Single |
    | key | str | Parameter to look for a single condition | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    """

    result = await controller.get_conditions(
        page=page,
        size=size,
        id_condition=id_condition,
        key=key,
        value=value,
        search=search,
        id_org=current_org,
    )

    return result


@router.get(
    "/partner/conditions",
    response_model=PaginatedConditions | Condition.Read,
    response_model_exclude_none=True,
)
async def get_conditions(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_condition: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all conditions: `/partner/conditions?page=1&size=10`
    ### * Get condition by id: `/partner/conditions?id_condition=123e4567-e89b-12d3-a456-426614174000`
    ### * Get condition by key and value: `/partner/conditions?key=name&value=example`
    ### * Get condition by search: `/partner/conditions?search=condition`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_condition | UUID | id of condition | Single |
    | key | str | Parameter to look for a single condition | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    """

    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )

    result = await controller.get_conditions(
        page=page,
        size=size,
        id_condition=id_condition,
        key=key,
        value=value,
        search=search,
        id_org=current_org,
    )

    return result


@router.post(
    "/partner/conditions",
    status_code=201,
    response_model=Condition.Read,
    response_model_exclude_none=True,
)
async def create_condition(
    condition: Condition.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.create_condition(
        condition=condition,
        id_org=current_org,
    )

    return result


@router.post(
    "/partner/conditions/csv",
)
async def upload_conditions_csv(
    file: UploadFile = File(...),
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )
    if file.filename.split(".")[-1].lower() != "csv":
        # Logging of ERROR
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        file=file,
        id_org=current_org,
        write_model=Condition.Write,
        create_func=controller.create_condition_csv,
        update_func=controller.update_condition_csv,
    )

    return result


@router.put(
    "/partner/conditions/{id_condition}",
    response_model=Condition.Read,
    response_model_exclude_none=True,
)
async def update_condition(
    id_condition: UUID,
    condition: Condition.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.update_condition(
        id_condition=id_condition,
        condition=condition,
        id_org=current_org,
    )

    return result


@router.patch(
    "/partner/conditions",
    response_model=BasicResponse,
    response_model_exclude_none=True,
)
async def patch_conditions(
    id_conditions: list[UUID],
    condition: Condition.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    data = await controller.patch_conditions(
        id_conditions=id_conditions,
        condition=condition,
        id_org=current_org,
    )

    return data


@router.patch(
    "/partner/conditions/{id_condition}",
    response_model=Condition.Read,
    response_model_exclude_none=True,
)
async def patch_condition(
    id_condition: UUID,
    condition: Condition.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    data = await controller.patch_condition(
        id_condition=id_condition,
        condition=condition,
        id_org=current_org,
    )

    return data


@router.delete(
    "/partner/conditions",
    response_model=BasicResponse,
    response_model_exclude_none=True,
)
async def delete_conditions(
    id_conditions: list[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.delete_conditions(
        id_conditions=id_conditions,
        id_org=current_org,
    )

    return result


@router.delete(
    "/partner/conditions/{id_condition}",
    response_model=Condition.Read,
    response_model_exclude_none=True,
)
async def delete_condition(
    id_condition: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.delete_condition(
        id_condition=id_condition,
        id_org=current_org,
    )

    return result

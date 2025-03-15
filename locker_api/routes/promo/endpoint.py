from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user_id_org, get_current_user
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload

from util.response import BasicResponse

from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import DiscountType, PaginatedPromos, Promo

router = APIRouter(tags=["promos"])


@router.get("/mobile/promos", response_model=Promo.Read)
async def get_promo_code(
    promo_code: str,
    id_org: UUID = Depends(get_current_user_id_org),
    id_user: UUID = Depends(get_current_user),
):
    """"""
    promo = await controller.get_promo_by_code(promo_code, id_org, id_user)
    if not promo:
        raise HTTPException(status_code=404, detail="invalid promo code")

    return promo


@router.get("/partner/promos", response_model=PaginatedPromos | Promo.Read)
async def get_promos(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_promo: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_type: Optional[DiscountType] = None,
    search: Optional[str] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all promos: `/partner/promos?page=1&size=50`
    ### * Search promos: `/partner/promos?search=Locker&by_type=percent`
    ### * Get a single promo: `/partner/promos?id_promo=UUID`
    ### * Get a single promo by key: `/partner/promos?key=name&value=Small`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_promo | UUID | The unique ID of a promo | Single |
    | key | str | Parameter to look for a single promo | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | by_type | DiscountType | Filter by discount type | List |
    """

    # Logging at the start
    # Logging input objects
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    result = await controller.get_promos(
        page, size, id_org, id_promo, key, value, by_type, search
    )
    # Logging result

    return result


@router.post("/partner/promos", status_code=201, response_model=Promo.Read)
async def create_promo(
    promo: Promo.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.create_promo(promo, id_org)
    # Logging result

    return result


@router.post("/partner/promos/csv")
async def upload_promos_csv(
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
        Promo.Write,
        controller.create_promo_csv,
        controller.update_promo_csv,
    )

    # Logging result
    # Logging at the end

    return result


@router.put("/partner/promos/{id_promo}", response_model=Promo.Read)
async def update_promo(
    id_promo: UUID,
    promo: Promo.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.update_promo(id_promo, promo, id_org)
    # Logging result

    return result


@router.patch("/partner/promos/{id_promo}", response_model=Promo.Read)
async def patch_promo(
    id_promo: UUID,
    promo: Promo.Patch,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    Updates a promo's parameters such as name, code, etc. without requiring to send all the parameters.
    """

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.patch_promo(id_promo, promo, id_org)
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/promos", response_model=BasicResponse)
async def patch_promos(
    id_promos: list[UUID],
    promo: Promo.Patch,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    Updates a promo's parameters such as name, code, etc. without requiring to send all the parameters.
    """

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.patch_promos(id_promos, promo, id_org)

    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/promos/{id_promo}", response_model=Promo.Read)
async def delete_promo(
    id_promo: UUID,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_promo(id_promo, id_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/promos", response_model=BasicResponse)
async def delete_promos(
    id_promos: list[UUID],
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_promos(id_promos, id_org)
    # Logging result
    # Logging at the end

    return result

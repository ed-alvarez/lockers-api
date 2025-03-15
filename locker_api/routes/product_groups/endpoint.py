from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, HTTPException
from pydantic import conint

from util.response import BasicResponse

from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import PaginatedProductGroups, ProductGroup

router = APIRouter(tags=["product-groups"])


@router.get("/mobile/product-groups", response_model=PaginatedProductGroups)
async def mobile_get_product_groups(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    current_org: UUID = Depends(get_current_user_id_org),
    search: Optional[str] = None,
):
    """Get All Product Groups, paginated"""

    result = await controller.get_product_groups(page, size, current_org, search)

    return result


@router.get("/partner/product-groups", response_model=PaginatedProductGroups)
async def get_product_groups(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    current_org: UUID = Depends(get_current_org),
    search: Optional[str] = None,
    target_org: Optional[UUID] = None,
):
    """Get All Product Groups, paginated"""

    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org
    result = await controller.get_product_groups(page, size, current_org, search)

    return result


@router.post("/partner/product-groups", response_model=ProductGroup.Read)
async def create_product_group(
    product_group: ProductGroup.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Create a Product Group"""

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.create_product_group(product_group, current_org)

    return result


@router.put(
    "/partner/product-groups/{id_product_group}", response_model=ProductGroup.Read
)
async def update_product_group(
    id_product_group: UUID,
    product_group: ProductGroup.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Update a Product Group"""

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.update_product_group(
        id_product_group, product_group, current_org
    )

    return result


@router.patch(
    "/partner/product-groups/{id_product_group}", response_model=ProductGroup.Read
)
async def patch_product_group(
    id_product_group: UUID,
    product_group: ProductGroup.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Patch a Product Group"""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging warning
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.patch_product_group(
        id_product_group, product_group, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/product-groups", response_model=BasicResponse)
async def patch_product_groups(
    id_product_groups: list[UUID],
    product_group: ProductGroup.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Patch multiple Product Groups"""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging warning
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.patch_product_groups(
        id_product_groups, product_group, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.delete(
    "/partner/product-groups/{id_product_group}", response_model=ProductGroup.Read
)
async def delete_product_group(
    id_product_group: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete a Product Group"""

    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_product_group(id_product_group, current_org)

    return result


@router.delete("/partner/product-groups", response_model=BasicResponse)
async def delete_product_groups(
    ids_product_group: list[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete multiple Product Groups"""

    # Logging at the start

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_product_groups(ids_product_group, current_org)
    # Logging result
    # Logging at the end

    return result

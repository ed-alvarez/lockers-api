from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission, get_current_user_pool
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from util.images import ImagesService

from ..organization.controller import is_sub_org
from ..member.model import RoleType
from . import controller
from .model import WhiteLabel

router = APIRouter(tags=["white label"])


@router.get("/partner/white-label", response_model=Optional[WhiteLabel.Read])
async def partner_get_white_label(
    id_org: UUID = Depends(get_current_org),
):
    # Logging at the start
    # Logging input

    # Retrieve white label information
    white_label_info = await controller.partner_get_white_label(id_org)
    # Logging result
    # Logging at the end

    return white_label_info


@router.patch("/partner/white-label/logo", response_model=WhiteLabel.Read)
async def partner_update_white_label_logo(
    image: UploadFile,
    id_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    # Check permissions
    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Update the logo
    white_label_info = await controller.partner_update_white_label_logo(
        image, id_org, images_service
    )
    # Logging result
    # Logging at the end

    return white_label_info


@router.patch("/partner/white-label", response_model=WhiteLabel.Read)
async def partner_patch_white_label(
    white_label: WhiteLabel.Patch,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    # Check permissions
    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Apply the white-label patch
    updated_white_label = await controller.partner_patch_white_label(
        white_label, id_org
    )
    # Logging result
    # Logging at the end

    return updated_white_label


@router.put("/partner/white-label", response_model=WhiteLabel.Read)
async def partner_update_white_label(
    image: Optional[UploadFile] = None,
    white_label: WhiteLabel.Write = Depends(WhiteLabel.Write.as_form),
    id_org: UUID = Depends(get_current_org),
    user_pool: str = Depends(get_current_user_pool),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    updated_white_label = await controller.partner_update_white_label(
        image, white_label, id_org, user_pool, images_service
    )

    return updated_white_label


@router.put("/partner/white-label/{target_org}", response_model=WhiteLabel.Read)
async def partner_update_white_label_sub_org(
    target_org: UUID,
    image: Optional[UploadFile] = None,
    white_label: WhiteLabel.Write = Depends(WhiteLabel.Write.as_form),
    current_org: UUID = Depends(get_current_org),
    user_pool: str = Depends(get_current_user_pool),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    if str(target_org) != str(current_org):
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="The target organization is not a sub-org of the current organization",
            )

    updated_white_label = await controller.partner_update_white_label(
        image, white_label, target_org, user_pool, images_service
    )

    return updated_white_label


@router.post("/partner/white-label", response_model=WhiteLabel.Read)
async def partner_create_white_label(
    image: UploadFile,
    white_label: WhiteLabel.Write = Depends(WhiteLabel.Write.as_form),
    id_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    # Permission check
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Creating white label settings
    created_white_label = await controller.partner_create_white_label(
        image, white_label, id_org, images_service
    )

    return created_white_label


@router.get("/mobile/white-label", response_model=WhiteLabel.Read)
async def mobile_get_white_label(
    id_org: UUID = Depends(get_current_user_id_org),
):
    white_label_settings = await controller.mobile_get_white_label(id_org)

    return white_label_settings

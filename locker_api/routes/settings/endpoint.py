from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, HTTPException


from ..member.model import RoleType
from . import controller
from .model import OrgSettings, LiteAppSettings, ReservationWidgetSettings

router = APIRouter(tags=["settings"])


@router.get("/mobile/settings", response_model=OrgSettings.Read)
async def mobile_get_settings(id_org: UUID = Depends(get_current_user_id_org)):
    return await controller.get_settings_org(id_org)


@router.get("/partner/settings", response_model=OrgSettings.Read)
async def partner_get_settings(
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    return await controller.get_settings_org(id_org)


@router.put("/partner/settings", response_model=OrgSettings.Read)
async def update_settings(
    settings: OrgSettings.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    return await controller.update_settings(id_org, settings)


@router.post("/partner/settings", status_code=201, response_model=OrgSettings.Read)
async def create_settings(
    settings: OrgSettings.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    return await controller.create_settings(id_org, settings)


@router.get("/settings/lite-app", response_model=LiteAppSettings.Read)
async def public_get_lite_app_settings(
    id_org: UUID,
):
    return await controller.get_lite_app_settings(id_org)


@router.get("/partner/settings/lite-app", response_model=LiteAppSettings.Read)
async def partner_get_lite_app_settings(
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    return await controller.get_lite_app_settings(id_org)


@router.put("/partner/settings/lite-app", response_model=LiteAppSettings.Read)
async def update_lite_app_settings(
    settings: LiteAppSettings.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    return await controller.update_lite_app_settings(id_org, settings)


@router.post(
    "/partner/settings/lite-app", status_code=201, response_model=LiteAppSettings.Read
)
async def create_lite_app_settings(
    settings: LiteAppSettings.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    return await controller.create_lite_app_settings(id_org, settings)


@router.get(
    "/partner/settings/reservation-widget",
    response_model=ReservationWidgetSettings.Read,
)
async def partner_get_res_widget_settings(
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    return await controller.get_res_widget_settings(id_org)


@router.put(
    "/partner/settings/reservation-widget",
    response_model=ReservationWidgetSettings.Read,
)
async def update_res_widget_settings(
    settings: ReservationWidgetSettings.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    return await controller.update_res_widget_settings(id_org, settings)


@router.post(
    "/partner/settings/reservation-widget",
    status_code=201,
    response_model=ReservationWidgetSettings.Read,
)
async def create_res_widget_settings(
    settings: ReservationWidgetSettings.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    return await controller.create_res_widget_settings(id_org, settings)

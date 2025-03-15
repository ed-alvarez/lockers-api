from typing import List, Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission, get_current_user_pool
from fastapi import APIRouter, Depends, HTTPException
from pydantic import conint

from util.response import BasicResponse

from ..member.model import RoleType
from . import controller
from .model import Notification, NotificationType, PaginatedNotifications

router = APIRouter(tags=["notifications"])


@router.get(
    "/partner/notifications", response_model=PaginatedNotifications | Notification.Read
)
async def partner_get_notifications(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_notification: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    by_type: Optional[NotificationType] = None,
    current_org: UUID = Depends(get_current_org),
    current_user_pool: str = Depends(get_current_user_pool),
):
    """
    # Usage:
    ### * Get all notifications: `/partner/notifications?page=1&size=50&by_type=welcome`
    ### * Search notifications: `/partner/notifications?search=Welcome%20to%20the%20locker%20app`
    ### * Get a single notification: `/partner/notifications?id_notification=UUID`
    ### * Get a single notification by key: `/partner/notifications?key=name&value=Welcome%20to%20the%20locker%20app`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_notification | UUID | The unique ID of a notification | Single |
    | key | str | Parameter to look for a single notification | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | by_type | NotificationType | Filter by notification type | List |
    """

    # Logging at the start

    result = await controller.partner_get_notifications(
        page,
        size,
        current_user_pool,
        current_org,
        id_notification,
        key,
        value,
        search,
        by_type,
    )
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/notifications", response_model=Notification.Read)
async def partner_create_notification(
    notification: Notification.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
) -> Notification.Read:
    """Create a Notification for a partner"""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.partner_create_notification(notification, current_org)
    # Logging result
    # Logging at the end

    return result


@router.patch(
    "/partner/notifications/{id_notification}", response_model=Notification.Read
)
async def partner_patch_notification(
    id_notification: UUID,
    notification: Notification.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
) -> Notification.Read:
    """Patch a Notification for a partner"""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.partner_patch_notification(
        id_notification, notification, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/notifications", response_model=BasicResponse)
async def partner_patch_notifications(
    id_notifications: list[UUID],
    notification: Notification.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Patch multiple Notifications for a partner"""

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging warning
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.partner_patch_notifications(
        id_notifications, notification, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.put(
    "/partner/notifications/{id_notification}", response_model=Notification.Read
)
async def partner_update_notification(
    id_notification: UUID,
    notification: Notification.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
) -> Notification.Read:
    """Update a Notification for a partner"""

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.partner_update_notification(
        id_notification, notification, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.delete(
    "/partner/notifications/{id_notification}", response_model=Notification.Read
)
async def partner_delete_notification(
    id_notification: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
) -> Notification.Read:
    """Delete a Notification for a partner"""

    # Logging at the start

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.partner_delete_notification(id_notification, current_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/notifications", response_model=BasicResponse)
async def partner_delete_notifications(
    id_notifications: List[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete multiple Notifications for a partner"""

    # Logging at the start

    if permission != RoleType.admin:
        # Logging warning
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.partner_delete_notifications(
        id_notifications, current_org
    )
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/twilio")
async def partner_get_twilio_link(
    current_org: UUID = Depends(get_current_org),
):
    """Check if Twilio is authorized for a partner"""

    # Logging at the start
    # Logging input objects

    result = await controller.partner_get_twilio_link(current_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/twilio")
async def partner_delete_twilio_link(
    current_org: UUID = Depends(get_current_org),
):
    """Delete the Twilio link for a partner"""

    # Logging at the start
    # Logging input objects

    result = await controller.partner_delete_twilio_link(current_org)
    # Logging result
    # Logging at the end

    return result


@router.get("/twilio/authorize")
async def partner_authorize_twilio(
    AccountSid: str,
    state: UUID,
):
    """Authorize Twilio for a partner, the state must be the Org's ID"""

    # Logging at the start
    # Logging input objects

    result = await controller.partner_auth_twilio(state, AccountSid)
    # Logging result
    # Logging at the end

    return result


@router.post("/twilio/deauthorize")
async def partner_deauthorize_twilio(
    AccountSid: str,
    state: UUID,
):
    """Deauthorize Twilio for a partner, the state must be the Org's ID"""

    # Logging at the start
    # Logging input objects

    result = await controller.partner_deauth_twilio(state, AccountSid)
    # Logging result
    # Logging at the end

    return result

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission, get_current_username
from auth.user import get_current_user, get_current_user_id_org
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
)
from pydantic import AnyHttpUrl, condecimal, conint, constr
from starlette.websockets import WebSocketDisconnect
from util.images import ImagesService

from util.response import BasicResponse, Message

from ..device.model import HardwareType
from ..device.controller import unreserve_device
from ..member.model import RoleType
from ..organization.controller import is_sub_org
from ..reservations.controller import (
    get_reservation_by_tracking_number,
    delete_reservation,
)
from ..price.model import Currency
from . import controller
from ..logger.controller import get_event_logs
from ..logger.model import Log
from .connections import active_connections
from .controller import ServiceStep
from .model import (
    CompleteReservationResponse,
    Event,
    EventStatus,
    EventType,
    PaginatedEvents,
    StartReservationResponse,
    StartEvent,
    Duration,
    EventBatch,
    PenalizeReason,
    BatchResponse,
)

router = APIRouter(tags=["events"])


@router.get(
    "/public/events/{id_event}",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def public_get_event(id_event: UUID):
    """Get a single event"""
    return await controller.partner_get_event_public(id_event)


@router.get(
    "/mobile/events",
    response_model=PaginatedEvents | Event.Read,
    response_model_exclude_none=True,
)
async def mobile_get_events(
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_event: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_type: Optional[EventType] = None,
    by_status: Optional[EventStatus] = None,
    by_hardware_type: Optional[HardwareType] = None,
    search: Optional[str] = None,
):
    """
    # Usage:
    ### * Get all events: `/mobile/events?page=1&size=50`
    ### * Search events: `/mobile/events?search=Robert`
    ### * Get a single event: `/mobile/events?id_event=UUID`
    ### * Get a single event by key: `/mobile/events?key=order_id&value=ORD0031`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_event | UUID | The unique ID of a size | Single |
    | key | str | Parameter to look for a single size | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | by_type | Unit | Filter by event type | List |
    | by_status | PriceType | Filter by event status | List |
    | by_hardware_type | HardwareType | Filter by hardware device type | List |
    """

    return await controller.mobile_get_events(
        id_user=id_user,
        id_org=id_org,
        page=page,
        size=size,
        id_event=id_event,
        key=key,
        value=value,
        by_type=by_type,
        by_status=by_status,
        by_hardware_type=by_hardware_type,
        search=search,
    )


@router.post(
    "/mobile/events",
    status_code=201,
    response_model=StartReservationResponse,
    response_model_exclude_none=True,
)
async def mobile_start_event(
    id_device: Optional[UUID] = None,
    id_size: Optional[UUID] = None,
    id_location: Optional[UUID] = None,
    current_user: UUID = Depends(get_current_user),
    current_org: UUID = Depends(get_current_user_id_org),
    promo_code: Optional[str] = None,
    order_id: Optional[str] = None,
):
    """Starts an Event, logic depends on the device type"""

    try:
        event = await controller.mobile_start_event(
            id_device=id_device,
            id_org=current_org,
            id_user=current_user,
            id_size=id_size,
            id_location=id_location,
            promo_code=promo_code,
            order_id=order_id,
        )
    except HTTPException as e:
        try:
            await controller.unreserve_device(id_device, current_org)
        except Exception:
            pass
        raise e
    except Exception as e:
        try:
            await controller.unreserve_device(id_device, current_org)
        except Exception:
            pass
        raise e

    await controller.broadcast_event(event.id, "create", current_org)

    return event


@router.post(
    "/mobile/events/{id_event}/confirm",
    status_code=201,
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def mobile_confirm_event(
    id_event: UUID,
    id_org: UUID = Depends(get_current_user_id_org),
    id_user: UUID = Depends(get_current_user),
    payment_method: Optional[str] = None,
    user_code: Optional[constr(regex=r"\d{4}")] = None,
):
    """Confirm an event's payment for a user, could be a service-pickup or storage"""

    event = await controller.mobile_confirm_event(
        id_event, id_org, id_user, payment_method, user_code
    )
    await controller.broadcast_event(event.id, "update", id_org)

    return event


@router.post(
    "/mobile/events/{id_event}/complete",
    response_model=CompleteReservationResponse,
    response_model_exclude_none=True,
)
async def mobile_complete_event(
    id_event: UUID,
    request: Request,
    payment_method: Optional[str] = None,
    user_code: Optional[constr(regex=r"\d{4}")] = None,
    image: Optional[UploadFile] = File(None),
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
    image_service: ImagesService = Depends(ImagesService),
):
    """Complete an event for a user, could be a service-pickup or storage"""

    image_url = None
    if image:
        image_url = await image_service.upload(str(id_org), image)

    event = await controller.mobile_complete_event(
        id_event,
        id_user,
        id_org,
        request,
        image_url["url"] if image_url else None,
        user_code,
        payment_method,
    )
    await controller.broadcast_event(event["id"], "update", id_org)

    try:
        await controller.unreserve_device(event["id_device"], id_org)
    except Exception:
        pass

    return event


@router.patch(
    "/mobile/events/{id_event}/cancel",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def mobile_cancel_event(
    id_event: UUID,
    id_org: UUID = Depends(get_current_user_id_org),
    id_user: UUID = Depends(get_current_user),
):
    """Mobile user cancels an event"""

    event = await controller.mobile_cancel_event(id_event, id_user, id_org)
    await controller.broadcast_event(event.id, "update", id_org)

    return event


@router.post(
    "/partner/events/{id_event}/share",
    response_model=BasicResponse,
    response_model_exclude_none=True,
)
async def partner_share_event(
    id_event: UUID,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    message: Optional[Message] = None,
    current_org: UUID = Depends(get_current_org),
):
    """Send event code to phone number"""

    response = await controller.share_event(
        id_event, phone_number, email, message, current_org
    )

    return response


@router.post(
    "/mobile/events/{id_event}/share",
    response_model=BasicResponse,
    response_model_exclude_none=True,
)
async def mobile_share_event(
    id_event: UUID,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    message: Optional[Message] = None,
    current_org: UUID = Depends(get_current_user_id_org),
):
    """Send event code to phone number"""

    response = await controller.share_event(
        id_event, phone_number, email, message, current_org
    )

    return response


@router.get(
    "/partner/events",
    response_model=PaginatedEvents | Event.Read,
    response_model_exclude_none=True,
)
async def partner_get_events(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_event: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_type: Optional[EventType] = None,
    by_status: Optional[EventStatus] = None,
    search: Optional[str] = None,
    by_device: Optional[HardwareType] = None,
    current_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all events: `/partner/events?page=1&size=50`
    ### * Search events: `/partner/events?search=Robert`
    ### * Get a single event: `/partner/events?id_event=UUID`
    ### * Get a single event by key: `/partner/events?key=order_id&value=ORD0031`
    ### * Filter events by device: `/partner/events?by_device=linka`  # New usage example

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_event | UUID | The unique ID of an event | Single |
    | key | str | Parameter to look for a single event | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | by_type | EventType | Filter by event type | List |
    | by_status | EventStatus | Filter by event status | List |
    | by_device | HardwareType | Filter by hardware device type | List |  # New parameter details"""
    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org

    events = await controller.partner_get_events(
        by_type,
        by_status,
        current_org,
        page,
        size,
        id_event,
        key,
        value,
        search,
        by_device,
    )

    # We need to set a hard limit on the `size` query param.
    # If a size of 10000 is sent (?size=10000), Cloudwatch will reject
    # the request due to the size of the payload exceeding the limit.
    #
    # This will result in a 500 error. In the meantime, this will be commented
    # until a proper pagination system is in place.
    #
    # ...

    # Logging at the end

    return events


@router.get("/partner/event-logs/{id_event}", response_model=list[Log.Read])
async def get_device_log_history(
    id_event: UUID,
    current_org: UUID = Depends(get_current_org),
):
    return await get_event_logs(id_event, current_org)


@router.get(
    "/partner/events/device/{id_device}",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_get_event_by_device(
    id_device: UUID,
    current_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Get any concurrent event by device ID"""

    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access event from a non-sub organization",
            )
        current_org = target_org
    event: Event.Read = await controller.get_event_by_device(id_device, current_org)

    return event


@router.get(
    "/partner/events_by_user/{id_user}",
    response_model=List[Event.Read],
    response_model_exclude_none=True,
)
async def partner_get_events_by_user(
    id_user: UUID,
    by_type: Optional[EventType] = None,
    active: Optional[bool] = True,
    current_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Get all 'in_progress' events by user, default type is 'storage'"""

    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org
    events: List = await controller.partner_get_events_by_user(
        id_user, current_org, by_type, active
    )

    return events


@router.get(
    "/partner/events/delivery",
    response_model=List[Event.Read],
    response_model_exclude_none=True,
)
async def get_deliveries_by_access_code(
    access_code: str,
    current_org: UUID = Depends(get_current_org),
):
    """Get all 'in_progress' deliveries by access code"""
    events: List = await controller.partner_get_deliveries(access_code, current_org)

    return events


@router.post(
    "/partner/events", response_model=Event.Read, response_model_exclude_none=True
)
async def partner_start_event(
    request: Request,
    payload: StartEvent,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Create an event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.partner_start_event(
        payload, current_org, request
    )

    await controller.broadcast_event(event.id, "create", current_org)

    return event


@router.post(
    "/partner/events/storage/batch",
    response_model=EventBatch,
    response_model_exclude_none=True,
)
async def partner_start_storage_batch(
    id_sizes: List[UUID],
    id_location: UUID,
    id_user: UUID,
    from_user: Optional[UUID] = None,
    duration: Optional[Duration] = None,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Create a storage event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    return await controller.partner_start_storage_batch(
        current_org,
        id_sizes,
        id_location,
        id_user,
        duration,
        from_user,
    )


@router.post(
    "/partner/events/vending",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_start_vending(
    id_device: UUID,
    id_user: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Create a storage event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.partner_start_vending(
        id_device,
        id_user,
        current_org,
    )

    await controller.broadcast_event(event.id, "create", current_org)

    return event


@router.post(
    "/partner/events/storage",
    response_model=Event.Read,
    response_model_exclude_none=True,
    deprecated=True,
)
async def partner_start_storage(
    id_size: Optional[UUID] = None,
    size_external_id: Optional[str] = None,
    id_location: Optional[UUID] = None,
    location_external_id: Optional[str] = None,
    id_user: Optional[UUID] = None,
    user_external_id: Optional[str] = None,
    passcode: Optional[constr(regex=r"\d{4}", max_length=4, min_length=4)] = None,
    from_user: Optional[UUID] = None,
    duration: Optional[Duration] = None,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Create a storage event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.partner_start_storage(
        id_size,
        size_external_id,
        id_location,
        location_external_id,
        current_org,
        id_user,
        user_external_id,
        from_user,
        duration,
        passcode,
    )

    await controller.broadcast_event(event.id, "create", current_org)

    return event


@router.patch(
    "/partner/events/storage/complete",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_complete_storage(
    id_event: Optional[UUID] = None,
    passcode: Optional[constr(regex=r"\d{4}", max_length=4, min_length=4)] = None,
    locker_number: Optional[int] = None,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Complete a storage event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )

    event: Event.Read = await controller.partner_complete_storage(
        id_event, passcode, locker_number, current_org
    )

    await controller.broadcast_event(event.id, "update", current_org)

    return event


@router.post(
    "/partner/events/delivery",
    response_model=Event.Read,
    response_model_exclude_none=True,
    deprecated=True,
)
async def partner_start_delivery(
    request: Request,
    id_device: Optional[UUID] = None,
    id_size: Optional[UUID] = None,
    size_external_id: Optional[str] = None,
    id_location: Optional[UUID] = None,
    location_external_id: Optional[str] = None,
    id_user: Optional[UUID] = None,
    user_external_id: Optional[str] = None,
    from_user: Optional[UUID] = None,
    order_id: Optional[str] = None,
    phone_number: Optional[str] = None,
    pin_code: Optional[str] = None,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """# Create a delivery event

    ## Using External IDs:

    - size_external_id = size.external_id
    - location_external_id = location.custom_id
    - user_external_id = user.user_id

    """

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )

    if phone_number and not re.match(r"^\+[1-9]\d{1,14}$", phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number")

    if pin_code and not re.match(r"^\d{4}$", pin_code):
        raise HTTPException(status_code=400, detail="Invalid pin code")

    event: Event.Read = await controller.partner_start_delivery(
        id_device,
        id_size,
        size_external_id,
        id_location,
        location_external_id,
        current_org,
        id_user,
        user_external_id,
        from_user,
        order_id,
        pin_code,
        phone_number,
        request,
    )

    await controller.broadcast_event(event.id, "create", current_org)

    return event


@router.post(
    "/partner/events/delivery-parcel",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_start_delivery_parcel(
    request: Request,
    tracking_number: str,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    # Create a delivery event from a reservation's tracking number
    """

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )

    reservation = await get_reservation_by_tracking_number(tracking_number, current_org)

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail=f"No reservation with tracking number '{tracking_number}' was found",
        )

    if not reservation.id_device:
        raise HTTPException(
            status_code=400, detail="no device was assinged to this reservation"
        )

    await unreserve_device(reservation.id_device, current_org)

    event = await controller.partner_start_delivery(
        reservation.id_device,
        None,
        None,
        None,
        None,
        current_org,
        reservation.id_user,
        None,
        None,
        tracking_number,
        None,
        None,
        request,
    )

    await delete_reservation(reservation.id, current_org)

    await controller.broadcast_event(event.id, "create", current_org)

    return event


@router.post(
    "/partner/events/rental",
    response_model=Event.Read,
    response_model_exclude_none=True,
    deprecated=True,
)
async def partner_start_rental(
    id_device: UUID,
    id_user: UUID,
    id_condition: Optional[UUID] = None,
    current_org: UUID = Depends(get_current_org),
    from_user: Optional[UUID] = None,
    permission: RoleType = Depends(get_permission),
):
    """Create a rental event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.partner_start_rental(
        current_org, from_user, id_user, None, id_device, id_condition
    )

    await controller.broadcast_event(event.id, "create", current_org)

    return event


@router.patch(
    "/partner/events/rental/complete",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_complete_rental(
    id_device: UUID,
    id_user: Optional[UUID] = None,
    id_condition: Optional[UUID] = None,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Complete a rental event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.partner_complete_rental(
        current_org, id_user, id_device, id_condition
    )

    await controller.broadcast_event(event.id, "create", current_org)

    return event


@router.patch(
    "/partner/events/{id_event}/service",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_service_step(
    step: ServiceStep,
    id_event: UUID,
    id_device: Optional[UUID] = None,
    weight: Optional[condecimal(max_digits=5, decimal_places=2, gt=0)] = None,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Instead of having multiple endpoints, we decided to include all of the steps in one endpoint"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )

    event: Event.Read = await controller.partner_service_step(
        step, weight, id_device, id_event, current_org
    )

    await controller.broadcast_event(event.id, "update", current_org)

    return event


@router.patch(
    "/partner/events/{id_event}/penalize",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_penalize_event(
    id_event: UUID,
    amount: condecimal(gt=0.5, decimal_places=2, max_digits=6),
    reason: PenalizeReason,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Instead of having multiple endpoints, we decided to include all of the steps in one endpoint"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )

    event: Event.Read = await controller.partner_penalize_event(
        id_event, amount, reason, current_org
    )

    await controller.broadcast_event(event.id, "update", current_org)

    return event


@router.patch(
    "/partner/events/{id_event}/unlock",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_unlock_event(
    id_event: UUID,
    code: int,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Unlock an event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.partner_unlock_event(
        id_event, code, current_org
    )
    await controller.broadcast_event(event.id, "update", current_org)

    return event


@router.patch(
    "/partner/events/{id_event}/cancel",
    response_model=Event.Read,
    response_model_exclude_none=True,
    deprecated=True,
)
async def partner_cancel_event(
    id_event: UUID,
    cancel_at: Optional[datetime] = None,
    maintenance: Optional[bool] = None,
    current_org: UUID = Depends(get_current_org),
    member_name: Optional[str] = Depends(get_current_username),
    permission: RoleType = Depends(get_permission),
):
    """Cancels an event"""
    print(member_name)
    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )

    event: Event.Read = await controller.partner_cancel_event(
        id_event=id_event,
        id_org=current_org,
        cancel_at=cancel_at,
        maintenance=maintenance,
        canceled_by=member_name,
    )

    try:
        await controller.unreserve_device(event.id_device, current_org)
    except Exception:
        pass

    return event


@router.patch(
    "/partner/event/cancel",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_cancel_event_by(
    id_event: Optional[UUID] = None,
    invoice_id: Optional[str] = None,
    order_id: Optional[str] = None,
    cancel_at: Optional[datetime] = None,
    maintenance: Optional[bool] = None,
    current_org: UUID = Depends(get_current_org),
    member_name: Optional[str] = Depends(get_current_username),
    permission: RoleType = Depends(get_permission),
):
    """Cancels an event by event ID or order ID"""
    print(member_name)
    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )

    event: Event.Read = await controller.partner_cancel_event(
        id_event=id_event,
        id_org=current_org,
        invoice_id=invoice_id,
        order_id=order_id,
        cancel_at=cancel_at,
        maintenance=maintenance,
        canceled_by=member_name,
    )

    try:
        await controller.unreserve_device(event.id_device, current_org)
    except Exception:
        pass

    return event


@router.patch(
    "/partner/events",
    response_model=BasicResponse,
    response_model_exclude_none=True,
)
async def partner_cancel_events(
    events: list[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Cancels multiple events"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )

    res = await controller.partner_cancel_events(events, current_org)

    return res


@router.patch(
    "/partner/events/{id_event}/unreserve_device",
    response_model=Event.Read,
    response_model_exclude_none=True,
    deprecated=True,
)
async def partner_unreserve_device(
    id_event: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Unreserve device of an event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.partner_unreserve_device(id_event, current_org)
    await controller.broadcast_event(event.id, "update", current_org)

    return event


@router.patch(
    "/partner/events/{id_event}/refund",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def partner_refund_event(
    id_event: UUID,
    amount: Optional[condecimal(max_digits=8, decimal_places=2, gt=0)] = None,
    currency: Optional[Currency] = None,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Refunds an event"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.partner_refund_event(
        id_event, current_org, amount, currency
    )
    await controller.broadcast_event(event.id, "update", current_org)

    return event


@router.post("/partner/event/{id_event}/sign", response_model_exclude_none=True)
async def partner_sign_event(
    id_event: UUID,
    id_org: UUID = Depends(get_current_org),
    image: UploadFile = File(...),
    images_service: ImagesService = Depends(ImagesService),
):
    response = await controller.partner_sign_event(
        id_event, id_org, image, images_service
    )

    return response


@router.post(
    "/partner/events/sign",
    response_model=BasicResponse,
    response_model_exclude_none=True,
)
async def partner_sign_events(
    events: list[UUID] = Body(),
    image_url: AnyHttpUrl = Body(),
    id_org: UUID = Depends(get_current_org),
):
    response = await controller.partner_sign_events(events, id_org, image_url)

    return response


@router.patch(
    "/mobile/event/delivery/complete",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def mobile_delivery_complete_event(
    code: Optional[int] = None,
    user_code: Optional[constr(regex=r"\d{4}")] = None,
):
    """Complete a delivery event, automatically unreserves the device"""

    event = await controller.complete_delivery(
        # Complete transaction by only using 4 digits pin:
        code=code,
        order_id=None,
        user_code=user_code,
        id_org=None,
    )
    id_org = event.id_org
    await controller.broadcast_event(event.id, "update", id_org)

    return event


@router.patch(
    "/mobile/event/service/complete",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def public_complete_service(
    id_event: UUID,
):
    """Complete a service event, automatically unreserves the device"""
    event = await controller.partner_get_event_public(id_event)

    if event.event_status != EventStatus.awaiting_user_pickup:
        raise HTTPException(
            status_code=400, detail="This transaction is not ready to be picked up"
        )

    await controller.complete_service(event)
    await controller.partner_unlock_device(event.id_device, event.id_org)

    await controller.broadcast_event(event.id, "update", event.id_org)

    return event


@router.patch(
    "/partner/events/delivery/complete",
    response_model=Event.Read,
    response_model_exclude_none=True,
)
async def delivery_complete_event(
    code: Optional[int] = None,
    user_code: Optional[constr(regex=r"\d{4}")] = None,
    order_id: Optional[str] = None,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
) -> Event.Read:
    """Complete a delivery event, automatically unreserves the device"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event: Event.Read = await controller.complete_delivery(
        code, order_id, user_code, current_org
    )
    await controller.broadcast_event(event.id, "update", current_org)

    return event


@router.patch(
    "/partner/events/delivery/complete/batch",
    response_model=list[BatchResponse],
    response_model_exclude_none=True,
)
async def delivery_complete_event_batch(
    codes: List[int],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Complete a delivery event, automatically unreserves the device"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    event = await controller.partner_complete_delivery_batch(codes, current_org)

    return event


@router.websocket("/events/listener/{orgId}")
async def websocket_endpoint(websocket: WebSocket, orgId: UUID):
    await websocket.accept()

    # Simply register the websocket connection.
    active_connections[orgId] = websocket

    try:
        while True:
            # Waiting for the data from the connected WebSocket.
            await websocket.receive_text()

    except WebSocketDisconnect:
        # If the connection is closed, remove it from the active connections.
        del active_connections[orgId]

from typing import List, Optional
from uuid import UUID

from auth.cognito import (
    get_current_org,
    get_locations,
    get_permission,
    get_current_username,
)
from auth.user import get_current_user, get_current_user_id_org
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import conint
from util.csv import process_csv_upload
from util.images import ImagesService

from util.response import BasicResponse

from ..groups.model import AssignmentType
from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from ..logger.controller import get_device_logs
from ..logger.model import Log
from .model import Device, HardwareType, Mode, PaginatedDevices, Status, LockStatus
from .connections import active_connections

router = APIRouter(tags=["devices"])


@router.websocket("/devices/listener/{orgId}")
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


@router.get("/mobile/devices", response_model=PaginatedDevices | Device.Read)
async def mobile_get_devices(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_device: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    by_status: Optional[Status] = None,
    by_mode: Optional[Mode] = None,
    by_type: Optional[HardwareType] = None,
    id_locker_wall: Optional[UUID] = None,
    id_location: Optional[UUID] = None,
    current_org: UUID = Depends(get_current_user_id_org),
    current_user: UUID = Depends(get_current_user),
):
    """
    # Usage:
    ### * Get all devices: `/mobile/devices?page=1&size=50`
    ### * Search devices: `/mobile/devices?search=Locker&by_status=available&by_mode=storage`
    ### * Get a single device: `/mobile/devices?id_device=UUID`
    ### * Get a single device by key: `/mobile/devices?key=name&value=Gantner%20Device`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_device | UUID | The unique ID of a device | Single |
    | key | str | Parameter to look for a single device | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | by_status | Status | Filter by status | List |
    | by_mode | Mode | Filter by mode | List |
    | by_type | HardwareType | Filter by hardware type | List |
    | id_locker_wall | UUID | Filter by locker wall | List |
    | id_location | UUID | Filter by location | List |
    """
    result = await controller.mobile_get_devices(
        page,
        size,
        current_org,
        current_user,
        id_device,
        key,
        value,
        search,
        by_status,
        by_mode,
        by_type,
        id_locker_wall,
        id_location,
    )

    return result


@router.get("/partner/devices", response_model=PaginatedDevices | Device.Read)
async def get_devices(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    from_user: Optional[UUID] = None,
    id_device: Optional[UUID] = None,
    search: Optional[str] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_status: Optional[Status] = None,
    by_mode: Optional[Mode] = None,
    by_type: Optional[HardwareType] = None,
    id_locker_wall: Optional[UUID] = None,
    id_location: Optional[UUID] = None,
    id_product: Optional[UUID] = None,
    current_org: UUID = Depends(get_current_org),
    locations: Optional[List[UUID]] = Depends(get_locations),
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all devices: `/partner/devices?page=1&size=50`
    ### * Search devices: `/partner/devices?search=Locker&by_status=available&by_mode=storage`
    ### * Get a single device: `/partner/devices?id_device=UUID`
    ### * Get a single device by key: `/partner/devices?key=name&value=Gantner%20Device`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | from_user | UUID | The ID of the user to view their assigned devices | List |
    | id_device | UUID | The unique ID of a device | Single |
    | key | str | Parameter to look for a single device | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | by_status | Status | Filter by status | List |
    | by_mode | Mode | Filter by mode | List |
    | by_type | HardwareType | Filter by hardware type | List |
    | id_locker_wall | UUID | Filter by locker wall | List |
    | id_location | UUID | Filter by location | List |
    """
    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org

    result = await controller.get_devices(
        page,
        size,
        current_org,
        from_user,
        id_device,
        search,
        key,
        value,
        by_status,
        by_mode,
        by_type,
        locations,
        id_locker_wall,
        id_location,
        id_product,
    )

    return result


@router.get("/partner/device-logs/{id_device}", response_model=list[Log.Read])
async def get_device_log_history(
    id_device: UUID,
    current_org: UUID = Depends(get_current_org),
):
    return await get_device_logs(id_device, current_org)


@router.post("/partner/devices", status_code=201, response_model=Device.Read)
async def create_device(
    device: Device.Write = Depends(Device.Write.as_form),
    image: Optional[UploadFile] = File(default=None),
    assignment_type: Optional[AssignmentType] = Form(None),
    assign_to: Optional[List[UUID]] = None,
    id_prices: Optional[List[UUID]] = None,
    current_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    device = await controller.create_device(
        current_org,
        device,
        assignment_type,
        assign_to,
        image,
        images_service,
        id_prices,
    )

    await controller.broadcast_event(device.id, "create", current_org)

    return device


@router.post("/partner/devices/csv")
async def upload_devices_csv(
    file: UploadFile = File(...),
    permission: RoleType = Depends(get_permission),
    id_org: UUID = Depends(get_current_org),
):
    """
    Endpoint to upload and process CSV files containing device data.
    """

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    if file.filename.split(".")[-1] != "csv":
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        id_org,
        file,
        Device.WriteCSV,
        controller.create_device_csv,
        controller.update_device_csv,
    )

    return result


@router.put("/partner/devices/{id_device}", response_model=Device.Read)
async def update_device(
    id_device: UUID,
    device: Device.Write = Depends(Device.Write.as_form),
    id_prices: Optional[List[UUID]] = None,
    image: Optional[UploadFile] = File(default=None),
    current_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
    member_name: Optional[str] = Depends(get_current_username),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )
    device = await controller.update_device(
        id_device, current_org, device, image, images_service, id_prices, member_name
    )

    await controller.broadcast_event(device.id, "update", current_org)

    return device


@router.patch("/partner/device/{id_device}", response_model=Device.Read)
async def patch_device(
    id_device: UUID,
    device: Device.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
    member_name: Optional[str] = Depends(get_current_username),
):
    """
    Update a device's parameters, such as name, description, etc. without requiring to send all the parameters.
    """

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    device = await controller.patch_device(
        id_device, current_org, device, False, member_name
    )

    await controller.broadcast_event(device.id, "update", current_org)

    return device


@router.patch("/partner/devices", response_model=BasicResponse)
async def patch_devices(
    id_devices: list[UUID],
    device: Device.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    Update multiple devices' parameters, such as name, description, etc. without requiring to send all the parameters.
    """
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.patch_devices(id_devices, device, current_org)
    return result


@router.delete("/partner/devices", response_model=BasicResponse)
async def delete_devices(
    devices: List[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_devices(devices, current_org)

    return result


@router.patch("/partner/devices/unlock", response_model=BasicResponse)
async def unlock_devices(
    device_list: List[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
    member_name: Optional[str] = Depends(get_current_username),
):
    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    result = await controller.partner_unlock_devices(
        device_list, current_org, member_name
    )

    return result


@router.patch("/mobile/device/state/{id_device}", response_model=Device.Read)
async def set_lock_state(
    id_device: UUID,
    status: LockStatus,
    current_org: UUID = Depends(get_current_user_id_org),
):
    result = await controller.set_lock_state(id_device, current_org, status)

    return result


@router.patch("/mobile/device/unlock/{id_event}", response_model=BasicResponse)
async def mobile_unlock_device(
    id_event: UUID,
    id_org: UUID = Depends(get_current_user_id_org),
    id_user: UUID = Depends(get_current_user),
):
    result = await controller.mobile_unlock_device(id_event, id_org, id_user)

    return result


@router.patch("/mobile/device/service-unlock/{id_device}", response_model=BasicResponse)
async def mobile_unlock_device_service(
    id_device: UUID,
    id_org: UUID = Depends(get_current_user_id_org),
    id_user: UUID = Depends(get_current_user),
):
    result = await controller.mobile_unlock_device_service(id_device, id_org)

    return result


@router.patch("/partner/devices/maintain-all", response_model=BasicResponse)
async def partner_repair_all_devices(
    device_list: List[UUID],
    disable: bool = False,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Sets all devices in the list to either available or maintenance mode, depending on the param"""

    if permission not in [RoleType.admin, RoleType.member, RoleType.operator]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin, member or operator",
        )
    result = await controller.partner_repair_all_devices(
        device_list, current_org, disable
    )

    return result

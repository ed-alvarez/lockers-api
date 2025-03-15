from typing import List, Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user, get_current_user_id_org
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload
from util.images import ImagesService

from util.response import BasicResponse

from ..device.model import Device, Mode, Status
from ..groups.model import AssignmentType
from ..member.model import RoleType
from ..organization.controller import is_sub_org
from ..organization.model import LinkOrgUser
from ..size.model import Size
from . import controller
from .model import Location, PaginatedLocations

router = APIRouter(tags=["locations"])


@router.get("/locations/{id_location}", response_model=Location.Read)
async def public_get_location(id_location: UUID):
    return await controller.get_public_location(id_location)


@router.get("/mobile/locations/last", response_model=Location.Read)
async def mobile_get_last_location(
    current_user=Depends(get_current_user),
):
    """Get last location for a mobile user"""

    location = await controller.get_last_location(current_user)

    return location


@router.get("/mobile/locations/recent", response_model=list[Location.Read])
async def mobile_get_recent_locations(
    current_user=Depends(get_current_user),
):
    """Get recent locations for a mobile user"""

    locations = await controller.get_recent_locations(current_user)

    return locations


@router.get(
    "/mobile/locations/favorite",
    response_model=LinkOrgUser.Read,
)
async def mobile_get_favorite_location(
    current_user=Depends(get_current_user),
):
    """Get favorite location for a mobile user"""

    location = await controller.get_favorite_location(current_user)

    return location


@router.patch(
    "/mobile/locations/favorite",
)
async def mobile_set_favorite_location(
    id_location: UUID,
    current_user=Depends(get_current_user),
):
    """Set favorite location for a mobile user"""

    location = await controller.set_favorite_location(current_user, id_location)

    return location


@router.get("/mobile/locations", response_model=PaginatedLocations | Location.Read)
async def mobile_get_locations(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_location: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    device_mode: Optional[Mode] = None,
    search: Optional[str] = None,
    expand: Optional[bool] = None,
    current_org: UUID = Depends(get_current_user_id_org),
):
    """
    # Usage:
    ### * Get all locations: `/mobile/locations?page=1&size=50`
    ### * Search locations: `/mobile/locations?search=Amsterdam&device_mode=rental`
    ### * Get a single location: `/mobile/locations?id_location=UUID`
    ### * Get a single location by key: `/mobile/locations?key=name&value=Amsterdam`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_location | UUID | The unique ID of a location | Single |
    | key | str | Parameter to look for a single location | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | device_mode | str | Filter by device mode | List |
    | expand | bool | Expand the location to inlcude sub-orgs | List |
    """

    locations = await controller.mobile_get_locations(
        page, size, current_org, id_location, key, value, device_mode, search, expand
    )

    return locations


@router.get("/mobile/geo-locations", response_model=list[Location.Read])
async def mobile_get_geo_locations(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: Optional[int] = None,
    expand: Optional[bool] = None,
    current_org: UUID = Depends(get_current_user_id_org),
):
    """
    # Usage:
    ### * Get all locations: `/mobile/geo-locations`
    ### * Get all locations, including sub-orgs: `/mobile/geo-locations?expand=true`
    ### * Get locations within a radius: `/mobile/geo-locations?lat=52.370216&lon=4.895168&radius=1000`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | lat | float | Latitude | List |
    | lon | float | Longitude | List |
    | radius | int | Radius in Km | List |
    | expand | bool | Expand the location to inlcude sub-orgs | List |
    """
    return await controller.mobile_get_geo_locations(
        current_org, lat, lon, radius, expand
    )


@router.get("/mobile/locations/{id_location}/devices", response_model=list[Device.Read])
async def mobile_get_devices_in_location(
    id_location: UUID,
    device_mode: Optional[Mode] = None,
    by_size: Optional[UUID] = None,
    current_org: UUID = Depends(get_current_user_id_org),
):
    """Get All Devices in a location"""

    devices = await controller.mobile_get_devices_in_location(
        id_location, device_mode, by_size, current_org
    )

    return devices


@router.get("/mobile/locations/{id_location}/sizes", response_model=list[Size.Read])
async def mobile_get_sizes_in_location(
    id_location: UUID,
    current_org: UUID = Depends(get_current_user_id_org),
    by_mode: Optional[Mode] = None,
    by_status: Optional[Status] = None,
):
    """Get All Sizes in a location"""

    # Logging at the start
    # Logging input objects

    # Call the actual function that retrieves sizes
    result = await controller.mobile_get_sizes_in_location(
        id_location, current_org, by_mode, by_status
    )

    # Logging result
    # Logging at the end

    return result


@router.get("/partner/locations", response_model=PaginatedLocations | Location.Read)
async def partner_get_locations(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_location: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    hidden: Optional[bool] = None,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all locations: `/partner/locations?page=1&size=50`
    ### * Search locations: `/partner/locations?search=Amsterdam&hidden=false`
    ### * Get a single location: `/partner/locations?id_location=UUID`
    ### * Get a single location by key: `/partner/locations?key=name&value=Amsterdam`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_location | UUID | The unique ID of a location | Single |
    | key | str | Parameter to look for a single location | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | hidden | bool | Filter by hidden | List |
    """

    # Logging at the start
    # Logging input objects
    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org
    # Call the actual function that does the work
    result = await controller.partner_get_locations(
        page, size, current_org, id_location, key, value, hidden, search
    )

    # Logging result
    # Logging at the end

    return result


@router.get(
    "/partner/locations/{id_location}/sizes", response_model=list[Size.ReadWithDevices]
)
async def partner_get_sizes_in_location(
    id_location: UUID,
    current_org: UUID = Depends(get_current_org),
    by_mode: Optional[Mode] = None,
    by_status: Optional[Status] = None,
):
    """Get All sizes in a location and groups available devices by size"""

    # Logging at the start
    # Logging input objects

    # Call the actual function that retrieves the sizes with devices
    result = await controller.partner_get_sizes_in_location(
        id_location, current_org, by_mode, by_status
    )

    # Logging result
    # Logging at the end

    return result


@router.get(
    "/partner/locations/{id_location}/devices", response_model=list[Device.Read]
)
async def partner_get_devices_in_location(
    id_location: UUID,
    from_user: Optional[UUID] = None,
    device_mode: Optional[Mode] = None,
    by_status: Optional[Status] = None,
    current_org: UUID = Depends(get_current_org),
):
    """Get All Devices in a location"""

    # Call the function that retrieves devices
    result = await controller.partner_get_devices_in_location(
        id_location, from_user, device_mode, by_status, current_org
    )

    # Logging result

    return result


@router.post("/partner/locations", status_code=201, response_model=Location.Read)
async def create_location(
    location: Location.Write = Depends(Location.Write.as_form),
    image: Optional[UploadFile] = File(default=None),
    assignment_type: Optional[AssignmentType] = Form(None),
    assign_to: Optional[list[UUID]] = Form(None),
    current_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    """Create a new location"""

    # Logging at the start
    # For security reasons, be cautious about logging sensitive information from the inputs

    # Check permission
    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    # Call the function that creates a location
    result = await controller.create_location(
        location,
        image,
        assignment_type,
        assign_to,
        current_org,
        images_service,
    )

    # Logging result
    # Logging at the end

    return result


@router.post("/partner/locations/csv")
async def upload_locations_csv(
    file: UploadFile = File(...),
    permission: RoleType = Depends(get_permission),
    id_org: UUID = Depends(get_current_org),
):
    """
    Endpoint to upload and process CSV files containing device data.
    """

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    if file.filename.split(".")[-1].lower() != "csv":
        # Logging of ERROR
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        id_org,
        file,
        Location.Write,
        controller.create_location_csv,
        controller.update_location_csv,
    )
    # Logging result
    # Logging at the end

    return result


@router.put("/partner/locations/{id_location}", response_model=Location.Read)
async def update_location(
    id_location: UUID,
    location: Location.Write = Depends(Location.Write.as_form),
    image: Optional[UploadFile] = File(default=None),
    current_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    """Update a location"""

    # Check permission
    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    # Call the function that updates the location
    result = await controller.update_location(
        id_location, current_org, location, image, images_service
    )

    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/location/{id_location}", response_model=Location.Read)
async def patch_location(
    id_location: UUID,
    location: Location.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Patch a location"""

    # Logging at the start

    # Check permission
    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    # Call the function that patches the location
    result = await controller.patch_location(
        id_location=id_location,
        location=location,
        id_org=current_org,
    )
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/locations", response_model=BasicResponse)
async def patch_locations(
    locations: list[UUID],
    location: Location.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Patch multiple locations"""

    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.patch_locations(locations, location, current_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/locations", response_model=BasicResponse)
async def delete_locations(
    locations: List[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete multiple locations"""

    # Logging at the start
    # Logging input objects

    # Check permission
    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Call the function that deletes the locations
    result = await controller.delete_locations(locations, current_org)

    # Logging at the end
    return result


@router.patch("/partner/location/{id_location}/unlock")
async def unlock_device_by_location(
    id_location: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Unlock all devices in a location"""

    # Logging at the start
    # Logging input objects

    # Check permission
    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Call the function that unlocks the devices
    result = await controller.unlock_device_by_location(id_location, current_org)

    # Logging at the end
    return result

from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload

from util.response import BasicResponse

from ..organization.controller import is_sub_org
from . import controller
from .model import PaginatedSizes, Size

router = APIRouter(tags=["sizes"])


@router.get("/mobile/sizes", response_model=PaginatedSizes | Size.Read)
async def mobile_get_sizes(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_size: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_user_id_org),
):
    """
    # Usage:
    ### * Get all sizes: `/mobile/sizes?page=1&size=50`
    ### * Search sizes: `/mobile/sizes?search=Locker`
    ### * Get a single size: `/mobile/sizes?id_size=UUID`
    ### * Get a single size by key: `/mobile/sizes?key=name&value=Small`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_size | UUID | The unique ID of a size | Single |
    | key | str | Parameter to look for a single size | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    """

    # Logging at the start
    # Logging input objects

    result = await controller.get_sizes(
        current_org,
        page,
        size,
        id_size,
        key,
        value,
        search,
    )
    # Logging result
    # Logging at the end

    return result


@router.get("/partner/sizes", response_model=PaginatedSizes | Size.Read)
async def partner_get_sizes(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_size: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all sizes: `/partner/sizes?page=1&size=50`
    ### * Search sizes: `/partner/sizes?search=Locker`
    ### * Get a single size: `/partner/sizes?id_size=UUID`
    ### * Get a single size by key: `/partner/sizes?key=name&value=Small`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_size | UUID | The unique ID of a size | Single |
    | key | str | Parameter to look for a single size | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
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
    result = await controller.get_sizes(
        current_org,
        page,
        size,
        id_size,
        key,
        value,
        search,
    )
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/sizes", status_code=201, response_model=Size.Read)
async def create_size(
    size: Size.Write,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.create_size(size, current_org)
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/sizes/csv")
async def upload_sizes_csv(
    file: UploadFile = File(...),
    id_org: UUID = Depends(get_current_org),
):
    """
    Endpoint to upload and process CSV files containing device data.
    """

    # Logging at the start
    # Logging input objects

    if file.filename.split(".")[-1].lower() != "csv":
        # Logging of ERROR
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        id_org, file, Size.Write, controller.create_size_csv, controller.update_size_csv
    )

    # Logging result
    # Logging at the end

    return result


@router.put("/partner/sizes/{id_size}", response_model=Size.Read)
async def update_size(
    id_size: UUID,
    size: Size.Write,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.update_size(id_size, size, current_org)
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/sizes/{id_size}", response_model=Size.Read)
async def patch_size(
    id_size: UUID,
    size: Size.Patch,
    current_org: UUID = Depends(get_current_org),
):
    """
    Updates a size's parameters such as name, width, etc. without requiring to send all the parameters.
    """

    # Logging at the start

    result = await controller.patch_size(id_size, size, current_org)
    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/sizes", response_model=BasicResponse)
async def patch_sizes(
    id_sizes: list[UUID],
    size: Size.Patch,
    current_org: UUID = Depends(get_current_org),
):
    """
    Updates a size's parameters such as name, width, etc. without requiring to send all the parameters.
    """

    # Logging at the start

    result = await controller.patch_sizes(id_sizes, size, current_org)

    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/sizes/{id_size}", response_model=Size.Read)
async def delete_size(
    id_size: UUID,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start
    # Logging input objects

    result = await controller.delete_size(id_size, current_org)
    # Logging at the end

    return result


@router.delete("/partner/sizes", response_model=BasicResponse)
async def delete_sizes(
    id_sizes: list[UUID],
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.delete_sizes(id_sizes, current_org)
    # Logging result
    # Logging at the end

    return result

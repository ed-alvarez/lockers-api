import json
from uuid import UUID

from auth.cognito import get_current_org
from fastapi import APIRouter, Depends, HTTPException


from . import controller
from .model import FilterType

router = APIRouter(tags=["filters"])


@router.get("/partner/filters/{filter_type}")
async def partner_get_filters(
    current_org: UUID = Depends(get_current_org),
    filter_type: FilterType = None,
):
    # Logging at the start
    # Logging input objects

    if not filter_type:
        # Logging of WARN
        raise HTTPException(status_code=400, detail="Filter type is required")

    filter_data = await controller.get_filter(
        current_org,
        filter_type,
    )
    # Logging result
    # Logging at the end

    return json.loads(filter_data)


@router.put("/partner/filters/{filter_type}")
async def partner_update_filters(
    payload: list,
    current_org: UUID = Depends(get_current_org),
    filter_type: FilterType = None,
):
    # Logging at the start

    if not filter_type:
        # Logging of WARN
        raise HTTPException(status_code=400, detail="Filter type is required")

    if not payload:
        # Logging of WARN
        raise HTTPException(status_code=400, detail="Payload is required")

    filter_data = await controller.update_filter(
        current_org,
        filter_type,
        payload,
    )
    # Logging result
    # Logging at the end

    return json.loads(filter_data)

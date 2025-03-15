from typing import List
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from fastapi import APIRouter, Depends, HTTPException

from util.response import BasicResponse

from ..member.model import RoleType
from . import controller
from .model import ApiKey

router = APIRouter(tags=["api-keys"])


@router.get("/partner/api-keys", response_model=list[ApiKey.Read])
async def get_api_keys(
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    # Koloni API Key

    ## Description
    API keys are used to authenticate with the Koloni API. They are used in place of a JWT token, currently
    supporting the same endpoints as the JWT token.

    ## Usage
    API keys are used in the `X-API-KEY` header of requests to the Koloni API. For example:
    ```
    curl -X GET https://<env>.api.koloni.com/v2/partner/locations
        -H "X-API-KEY: <api_key>"
    ```

    """

    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.get_api_keys(current_org)

    # Logging result
    # Logging at the end

    return result


@router.post("/partner/api-keys", response_model=ApiKey.Read)
async def create_api_key(
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Create an API key"""

    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.create_api_key(current_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/api-keys/{id_api_key}", response_model=ApiKey.Read)
async def delete_api_key(
    id_api_key: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete an API key"""

    # Logging at the start

    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_api_key(id_api_key, current_org)

    # Logging at the end

    return result


@router.delete("/partner/api-keys", response_model=BasicResponse)
async def delete_api_keys(
    id_api_keys: List[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete multiple API keys"""

    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_api_keys(id_api_keys, current_org)
    # Logging result
    # Logging at the end

    return result

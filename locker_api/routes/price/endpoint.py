from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload

from util.response import BasicResponse

from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import Currency, PaginatedPrices, Price, PriceType, Unit

router = APIRouter(tags=["prices"])


@router.get("/mobile/prices", response_model=PaginatedPrices | Price.Read)
async def mobile_get_prices(
    current_org: UUID = Depends(get_current_user_id_org),
    page: conint(ge=1) = 1,
    size: conint(ge=1) = 50,
    id_price: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    by_unit: Optional[Unit] = None,
    by_price_type: Optional[PriceType] = None,
    by_currency: Optional[Currency] = None,
):
    """
    # Usage:
    ### * Get all prices: `/mobile/prices?page=1&size=50`
    ### * Search prices: `/mobile/prices?search=Locker&by_unit=hour`
    ### * Get a single price: `/mobile/prices?id_price=UUID`
    ### * Get a single price by key: `/mobile/prices?key=name&value=Small`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_price | UUID | The unique ID of a price | Single |
    | key | str | Parameter to look for a single price | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | by_unit | Unit | Filter by unit | List |
    | by_price_type | PriceType | Filter by price type | List |
    | by_currency | Currency | Filter by currency | List |
    """
    result = await controller.get_prices(
        current_org,
        page,
        size,
        id_price,
        key,
        value,
        search,
        by_unit,
        by_price_type,
        by_currency,
    )

    return result


@router.get("/partner/prices", response_model=PaginatedPrices | Price.Read)
async def partner_get_prices(
    current_org: UUID = Depends(get_current_org),
    page: conint(ge=1) = 1,
    size: conint(ge=1) = 50,
    id_price: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    by_unit: Optional[Unit] = None,
    by_price_type: Optional[PriceType] = None,
    by_currency: Optional[Currency] = None,
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all prices: `/partner/prices?page=1&size=50`
    ### * Search prices: `/partner/prices?search=Locker&by_unit=hour`
    ### * Get a single price: `/partner/prices?id_price=UUID`
    ### * Get a single price by key: `/partner/prices?key=name&value=Small`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_price | UUID | The unique ID of a price | Single |
    | key | str | Parameter to look for a single price | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    | by_unit | Unit | Filter by unit | List |
    | by_price_type | PriceType | Filter by price type | List |
    | by_currency | Currency | Filter by currency | List |
    """
    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org

    result = await controller.get_prices(
        current_org,
        page,
        size,
        id_price,
        key,
        value,
        search,
        by_unit,
        by_price_type,
        by_currency,
    )

    return result


@router.post("/partner/prices", status_code=201, response_model=Price.Read)
async def create_price(
    price: Price.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.create_price(price, id_org)

    return result


@router.post("/partner/prices/csv")
async def upload_prices_csv(
    file: UploadFile = File(...),
    permission: RoleType = Depends(get_permission),
    id_org: UUID = Depends(get_current_org),
):
    """
    Endpoint to upload and process CSV files containing device data.
    """

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    if file.filename.split(".")[-1].lower() != "csv":
        # Logging of ERROR
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        id_org,
        file,
        Price.Write,
        controller.create_price_csv,
        controller.update_price_csv,
    )

    # Logging result
    # Logging at the end

    return result


@router.put("/partner/prices/{id_price}", response_model=Price.Read)
async def update_price(
    id_price: UUID,
    price: Price.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.update_price(id_price, price, id_org)

    return result


@router.patch("/partner/prices/{id_price}", response_model=Price.Read)
async def patch_price(
    id_price: UUID,
    price: Price.Patch,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    Updates a price's parameters such as name, amount, etc. without requiring to send all the parameters.
    """

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.patch_price(id_price, price, id_org)

    return result


@router.patch("/partner/prices", response_model=BasicResponse)
async def patch_prices(
    id_prices: list[UUID],
    price: Price.Patch,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    Updates multiple prices' parameters such as name, amount, etc. without requiring to send all the parameters.
    """

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging warning
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.patch_prices(id_prices, price, id_org)
    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/prices/{id_price}", response_model=Price.Read)
async def delete_price(
    id_price: UUID,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_price(id_price, id_org)

    return result


@router.delete("/partner/prices", response_model=BasicResponse)
async def delete_prices(
    id_prices: list[UUID],
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_prices(id_prices, id_org)
    # Logging result
    # Logging at the end

    return result

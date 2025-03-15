from typing import Optional
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user_id_org
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint
from util.csv import process_csv_upload
from util.images import ImagesService

from util.response import BasicResponse

from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import PaginatedProducts, Product

router = APIRouter(tags=["products"])


@router.get(
    "/mobile/products",
    response_model=PaginatedProducts | Product.Read,
    response_model_exclude_none=True,
)
async def mobile_get_products(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_product: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_group: Optional[UUID] = None,
    by_device: Optional[UUID] = None,
    by_location: Optional[UUID] = None,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_user_id_org),
):
    """
    # Usage:
    ### * Get all products: `/mobile/products?page=1&size=50`
    ### * Search products: `/mobile/products?search=Baseball`
    ### * Get a single product: `/mobile/products?id_product=UUID`
    ### * Get a single product by key: `/mobile/products?key=name&value=Bat`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_product | UUID | The unique ID of a product | Single |
    | key | str | Parameter to look for a single product | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    """

    return await controller.get_products(
        page,
        size,
        current_org,
        id_product,
        key,
        value,
        by_group,
        by_device,
        by_location,
        search,
    )


@router.get(
    "/partner/products",
    response_model=PaginatedProducts | Product.Read,
    response_model_exclude_none=True,
)
async def get_products(
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_product: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    by_group: Optional[UUID] = None,
    by_device: Optional[UUID] = None,
    by_location: Optional[UUID] = None,
    with_tracking: Optional[bool] = True,
    search: Optional[str] = None,
    current_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """
    # Usage:
    ### * Get all products: `/partner/products?page=1&size=50`
    ### * Search products: `/partner/products?search=Baseball`
    ### * Get a single product: `/partner/products?id_product=UUID`
    ### * Get a single product by key: `/partner/products?key=name&value=Bat`

    | param | type | description | return type
    | --- | --- | --- | --- |
    | id_product | UUID | The unique ID of an product | Single |
    | key | str | Parameter to look for a single product | Single |
    | value | str | Value of the "key" parameter | Single |
    | search | str | Search | List |
    """

    if target_org:
        if not await is_sub_org(target_org, current_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        current_org = target_org

    return await controller.get_products(
        page,
        size,
        current_org,
        id_product,
        key,
        value,
        by_group,
        by_device,
        by_location,
        search,
        with_tracking,
    )


@router.post("/partner/products", response_model=Product.Read)
async def create_product(
    image: Optional[UploadFile] = File(default=None),
    product: Product.Write = Depends(Product.Write.as_form),
    current_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    """Create a Product"""
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    # Your endpoint's core logic here...

    result = await controller.create_product(
        image, product, current_org, images_service
    )
    # Logging result
    # Logging at the end

    return result


@router.post("/partner/products/{id_product}/duplicate", response_model=Product.Read)
async def duplicate_product(
    id_product: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Update a Product"""
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.duplicate_product(id_product, current_org)

    return result


@router.put("/partner/products/{id_product}", response_model=Product.Read)
async def update_product(
    id_product: UUID,
    image: UploadFile = File(None),
    product: Product.Write = Depends(Product.Write.as_form),
    current_org: UUID = Depends(get_current_org),
    images_service: ImagesService = Depends(ImagesService),
    permission: RoleType = Depends(get_permission),
):
    """Update a Product"""
    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    result = await controller.update_product(
        id_product, image, product, current_org, images_service
    )

    return result


@router.patch("/partner/products/{id_product}", response_model=Product.Read)
async def patch_product(
    id_product: UUID,
    product: Product.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Patch a Product"""

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.patch_product(id_product, product, current_org)

    # Logging result
    # Logging at the end

    return result


@router.patch("/partner/products", response_model=BasicResponse)
async def patch_products(
    id_products: list[UUID],
    product: Product.Patch,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Patch multiple Products"""

    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    result = await controller.patch_products(id_products, product, current_org)

    # Logging result
    # Logging at the end

    return result


@router.post("/partner/products/csv")
async def upload_products_csv(
    file: UploadFile = File(...),
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    Endpoint to upload and process CSV files containing device data.
    """

    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    if file.filename.split(".")[-1].lower() != "csv":
        # Logging of WARN
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await process_csv_upload(
        id_org,
        file,
        Product.Write,
        controller.create_product_csv,
        controller.update_product_csv,
    )

    # Logging result
    # Logging at the end

    return result


@router.delete("/partner/products/{id_product}", response_model=Product.Read)
async def delete_product(
    id_product: UUID,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete a Product"""

    # Logging at the start

    if permission != RoleType.admin:
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Your endpoint's core logic here...

    result = await controller.delete_product(id_product, current_org)
    # Logging result

    return result


@router.delete("/partner/products", response_model=BasicResponse)
async def delete_products(
    id_products: list[UUID],
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Delete multiple Products"""

    # Logging at the start

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    result = await controller.delete_products(id_products, current_org)
    # Logging result
    # Logging at the end

    return result

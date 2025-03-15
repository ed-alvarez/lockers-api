from typing import List, Optional, Tuple
from uuid import UUID

from auth.cognito import get_current_org, get_permission
from auth.user import get_current_user, get_current_user_id_org
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import conint, constr

from util.response import BasicResponse

from ..login.model import Channel, VerificationMessage
from ..member.model import RoleType
from ..organization.controller import is_sub_org
from . import controller
from .model import (
    DefaultPaymentMethodResponse,
    PaginatedUsers,
    PaymentMethod,
    PaymentMethodResponse,
    User,
    VerifyResponse,
)

router = APIRouter(tags=["users"])


@router.get("/mobile/user", response_model=User.Read)
async def get_user(
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
):
    """Returns the current user's information"""
    # Logging at the start
    # Logging input objects

    user_info = await controller.get_user(id_user, id_org)

    # Logging the result
    # Logging at the end

    return user_info


@router.post("/mobile/user", response_model=VerificationMessage)
async def add_phone_or_email(
    to: str, channel: Channel, id_user: UUID = Depends(get_current_user)
):
    """Request to add a phone number or email address to the current user's account"""
    # Logging at the start
    # Logging input objects

    verification_message = await controller.add_phone_or_email(to, channel, id_user)

    # Logging the result
    # Logging at the end

    return verification_message


@router.patch("/mobile/user", response_model=User.Read)
async def verify_phone_or_email(
    to: str,
    channel: Channel,
    code: str,
    id_user: UUID = Depends(get_current_user),
):
    """Verify a phone number or email address for the current user's account"""
    # Logging at the start
    # Logging input objects

    user_info = await controller.verify_phone_or_email(to, channel, code, id_user)

    # Logging the result
    # Logging at the end

    return user_info


@router.put("/mobile/user", response_model=User.Read)
async def mobile_update_user(
    user: User.MobileWrite,
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
):
    return await controller.update_user(id_user, user, id_org)


@router.patch("/mobile/user/name", response_model=User.Read, deprecated=True)
async def update_user_name(
    name: str,
    id_user: UUID = Depends(get_current_user),
):
    """Change the current user's name"""
    # Logging at the start
    # Logging input objects

    updated_user_info = await controller.update_user_name(name, id_user)

    # Logging the result
    # Logging at the end

    return updated_user_info


@router.get(
    "/mobile/user/payment_methods",
    response_model_exclude_none=True,
    response_model=List[PaymentMethod],
)
async def get_payment_methods(
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
):
    """Request to retrieve the customer's payment methods from Stripe"""
    return await controller.get_payment_methods(id_org, id_user)


@router.post("/mobile/user/payment_methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
):
    """Request to add a payment method to the customer's account"""
    return await controller.add_payment_method(id_org, id_user)


@router.delete("/mobile/user/payment_methods/{pm_id}", response_model=BasicResponse)
async def delete_payment_method(
    pm_id: str,
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
):
    """Request to delete a payment method from the customer's account"""
    return await controller.delete_payment_method(id_org, id_user, pm_id)


@router.get("/mobile/user/payment_method", response_model=DefaultPaymentMethodResponse)
async def get_default_payment_method(
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
):
    """Request to retrieve the customer's default payment method id from Stripe"""
    # Logging at the start
    # Logging input objects

    default_payment_method = await controller.get_default_payment_method(
        id_org, id_user
    )

    # Logging the result
    # Logging at the end

    return default_payment_method


@router.post("/mobile/user/payment_method", response_model=PaymentMethodResponse)
async def setup_payment_method(
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
):
    """Request to setup a payment method for the current user's account"""
    # Logging at the start
    # Logging input objects

    payment_method_response = await controller.setup_default_payment_method(
        id_org, id_user
    )

    # Logging the result
    # Logging at the end

    return payment_method_response


@router.patch("/mobile/user/payment_method", response_model=BasicResponse)
async def confirm_payment_method(
    setup_intent: str,
    id_user: UUID = Depends(get_current_user),
    id_org: UUID = Depends(get_current_user_id_org),
):
    """Confirm a payment method for the current user's account, will charge the user $1.00 and refund it immediately"""
    # Logging at the start
    # Logging input objects

    confirmation_response = await controller.confirm_default_payment_method(
        id_org, id_user, setup_intent
    )

    # Logging the result
    # Logging at the end

    return confirmation_response


@router.get("/partner/users", response_model=PaginatedUsers)
async def get_users(
    search: Optional[str] = None,
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    by_phone: Optional[bool] = None,
    by_email: Optional[bool] = None,
    by_first_name: Optional[bool] = None,
    by_user_id: Optional[bool] = None,
    by_last_name: Optional[bool] = None,
    id_org: UUID = Depends(get_current_org),
    target_org: Optional[UUID] = None,
):
    """Returns a paginated list of users in the current organization"""
    if target_org:
        if not await is_sub_org(target_org, id_org):
            raise HTTPException(
                status_code=400,
                detail="Cannot access events from a non-sub organization",
            )
        id_org = target_org
    users = await controller.get_users(
        page,
        size,
        id_org,
        search,
        by_phone,
        by_email,
        by_first_name,
        by_user_id,
        by_last_name,
    )

    # Logging the result
    # Logging at the end

    return users


@router.get("/partner/users/code", response_model=User.Read, deprecated=True)
async def get_user_by_code(
    code: constr(regex=r"\d{4}", max_length=4),
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Return the user with the given code in the current organization""" ""
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    user = await controller.get_user_by_key("pin_code", code, id_org)
    if user is None:
        # Logging a warning when user is not found
        raise HTTPException(status_code=404, detail="User not found")

    # Logging the result
    # Logging at the end

    return user


@router.get("/partner/user", response_model=User.Read)
async def get_user_by_key(
    key: str,
    value: str,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """
    # Returns the user with the given key and value in the current organization
    ## Keys:
    - `phone_number`
    - `email`
    - `pin_code`
    - `id`
    """
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    user = await controller.get_user_by_key(key, value, id_org)

    if user is None:
        # Logging a warning when user is not found
        raise HTTPException(status_code=404, detail="User not found")

    # Logging the result
    # Logging at the end

    return user


@router.post("/partner/users/confirm", response_model=BasicResponse)
async def confirm_user(
    code: str,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Confirms a user in the current organization"""

    if permission not in [RoleType.admin, RoleType.member]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    response = await controller.get_and_verify_code(code, id_org)

    return response


@router.post("/partner/users/verify", response_model=VerifyResponse)
async def verify_user(
    id_user: UUID,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Sends an OTP message to a user in the current organization"""
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    response = await controller.verify_user(id_user, id_org)
    # Logging the result
    # Logging at the end

    return response


@router.post("/partner/users", response_model=List[User.Read])
async def add_users(
    users: List[User.Write],
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Creates one or a set of users in the current organization"""
    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    created_users = await controller.create_many_users(users, id_org)
    # Logging the result
    # Logging at the end

    return created_users


@router.post("/partner/users/csv", response_model=List[Tuple[Optional[User.Read], str]])
async def upload_users_csv(
    file: UploadFile = File(...),
    permission: RoleType = Depends(get_permission),
    id_org: UUID = Depends(get_current_org),
):
    """
    Endpoint to upload and process CSV files containing user data. Remember to separate the group UUIDS with a
    semicolon in the csv file, and also upload ONLY csv files.
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
        # Log invalid file type
        raise HTTPException(status_code=400, detail="File type must be CSV")

    result = await controller.process_csv_upload(file, id_org)
    # Logging result
    # Logging at the end

    return result


@router.put("/partner/users/{id_user}", response_model=User.Read)
async def partner_update_user(
    id_user: UUID,
    user: User.Write,
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Updates a user in the current organization"""
    # Logging at the start

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions, must be admin or member",
        )

    updated_user = await controller.update_user(id_user, user, id_org)
    # Logging result
    # Logging at the end

    return updated_user


@router.delete("/partner/users", response_model=BasicResponse)
async def delete_users(
    users: List[UUID],
    id_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    """Removes one or a set of users in the current organization"""
    # Logging at the start

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    deletion_result = await controller.delete_users(users, id_org)
    # Logging result
    # Logging at the end

    return deletion_result

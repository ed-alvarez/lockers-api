from uuid import UUID
from typing import Optional

from auth.models import PartnerLoginCredentials
from auth.user import get_current_user, get_current_user_id_org
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials


from ..organization.controller import is_sub_org
from . import controller
from .model import Channel, VerificationMessage

router = APIRouter(tags=["login"])
httpbasic_security = HTTPBasic()


@router.post("/mobile/login", response_model=VerificationMessage | str)
async def login_user(to: str, channel: Channel, id_org: Optional[UUID] = None):
    """to is the phone number or email address. channel is sms or email."""
    return await controller.send_otp_message(to, channel, id_org)


@router.post("/mobile/verify", response_model=str)
async def verify_user(to: str, channel: Channel, code: str, id_org: UUID):
    """to is the phone number or email address. channel is sms or email."""
    return await controller.verify_otp_message(to, code, channel, id_org)


@router.post("/mobile/transfer", response_model=str)
async def transfer_user(
    target_org: UUID,
    current_org: UUID = Depends(get_current_user_id_org),
    current_user: UUID = Depends(get_current_user),
):
    """this is to transfer a user from one org to another"""
    if not await is_sub_org(target_org, current_org):
        raise HTTPException(
            status_code=400,
            detail="You can only transfer users to sub organizations of your own organization",
        )
    return await controller.transfer_user(target_org, current_user)


@router.post("/partner/login")
async def login_partner(
    credentials: PartnerLoginCredentials = Depends(PartnerLoginCredentials.as_form),
):
    """this is the login endpoint for partners"""
    return await controller.login_partner(credentials)


@router.post("/kiosk/login")
async def login_kiosk(
    credentials: HTTPBasicCredentials = Depends(httpbasic_security),
):
    return await controller.login_kiosk(credentials)

import base64
import hashlib
import hmac
from typing import Optional
import re
from uuid import UUID

import aioboto3
from auth.models import PartnerLoginCredentials
from auth.user import create_access_token
from config import get_settings
from fastapi import HTTPException
from twilio.rest import Client
from fastapi.security import HTTPBasicCredentials

from ..organization.controller import get_org_by_user_pool, is_ojmar_org, is_ups_org
from ..user import controller
from ..organization import controller as org_controller
from .model import Channel


async def demo_login(phone_number: str):
    match phone_number:
        case "+1223334444":
            org = await get_org_by_user_pool("us-east-1_aSEeCaARi")

            jwt = await generate_token(phone_number, Channel.sms, org.id)
            return jwt

        case "+1234567890":
            org = await get_org_by_user_pool("us-east-1_jX5RBnJqq")

            jwt = await generate_token(phone_number, Channel.sms, org.id)
            return jwt

        case _:
            raise HTTPException(status_code=400, detail="Not a valid demo number")


async def send_otp_message(to: str, channel: Channel, id_org: Optional[UUID] = None):
    # Demo login
    if to == "+1223334444" or to == "+1234567890":
        return await demo_login(to)

    # Check if phone number is valid
    if not re.match(r"^\+[1-9]\d{1,14}$", to) and channel == Channel.sms:
        error_detail = "Invalid phone number format"

        raise HTTPException(status_code=400, detail=error_detail)

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    # Is Ojmar or UPS switch
    service_sid = get_settings().twilio_verification_sid
    if id_org:
        if await is_ojmar_org(id_org):
            print("SO TRUE!!!!!!")
            service_sid = get_settings().ojmar_verification_sid

        if await is_ups_org(id_org):
            print("SO TRUE!!!!!!")
            service_sid = get_settings().ups_verification_sid

    try:
        verification = client.verify.v2.services(service_sid).verifications.create(
            to=to, channel=channel.value
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "sid": verification.sid,
        "to": verification.to,
        "channel": verification.channel,
        "status": verification.status,
    }


async def verify_otp_message(to: str, code: str, channel: Channel, id_org: UUID):
    # Test login for Spherio app
    if (
        to == "appstoretest@koloni.me"
        and code == "123456"
        and channel == Channel.email
        and id_org == UUID("68bdc743-2ae6-4c1a-87b2-98514e0f4487")
    ):
        return await generate_token(to, channel, id_org)

    # Validate phone number
    if not re.match(r"^\+[1-9]\d{1,14}$", to) and channel == Channel.sms:
        error_detail = "Invalid phone number format"

        raise HTTPException(status_code=400, detail=error_detail)

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    # Is ojmar switch
    service_sid = get_settings().twilio_verification_sid
    if id_org:
        if await is_ojmar_org(id_org):
            service_sid = get_settings().ojmar_verification_sid

        if await is_ups_org(id_org):
            print("SO TRUE!!!!!!")
            service_sid = get_settings().ups_verification_sid

    try:
        check_instance = client.verify.v2.services(
            service_sid
        ).verification_checks.create(to=to, code=code)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if check_instance.status != "approved":
        raise HTTPException(status_code=400, detail="Invalid code")

    # User Validated, continue with login
    jwt = await generate_token(to, channel, id_org)

    return jwt


async def transfer_user(target_org: UUID, current_user: UUID):
    user = await controller.get_user(current_user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    target_channel = Channel.sms if user.phone_number else Channel.email
    target_to = user.phone_number if user.phone_number else user.email

    token = await generate_token(target_to, target_channel, target_org)

    return token


async def generate_token(to: str, channel: Channel, id_org: UUID):
    user = await controller.get_or_create_user(to, channel, id_org)

    if not user.active:
        raise HTTPException(status_code=400, detail="User inactive")

    token = create_access_token(user.id, id_org)

    return token


async def login_partner(credentials: PartnerLoginCredentials):
    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        region_name=get_settings().aws_region,
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
    ) as cognito:
        try:
            response = await cognito.admin_initiate_auth(
                UserPoolId=credentials.user_pool_id,
                ClientId=credentials.client_id,
                AuthFlow="ADMIN_NO_SRP_AUTH",
                AuthParameters={
                    "USERNAME": credentials.username,
                    "PASSWORD": credentials.password,
                },
            )

        except cognito.exceptions.NotAuthorizedException:
            error_detail = "Incorrect username or password"

            raise HTTPException(status_code=400, detail=error_detail)
        except cognito.exceptions.UserNotConfirmedException:
            error_detail = "User is not confirmed"

            raise HTTPException(status_code=400, detail=error_detail)
        except cognito.exceptions.UserNotFoundException:
            error_detail = "Incorrect username or password"

            raise HTTPException(status_code=400, detail=error_detail)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        try:
            return response["AuthenticationResult"]["IdToken"]
        except KeyError:
            raise HTTPException(
                status_code=400, detail="Error generating token, please try again"
            )


async def login_kiosk(credentials: HTTPBasicCredentials):
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    org_id = await org_controller.get_org_id_by_pin_code(
        credentials.username, credentials.password
    )

    if not org_id:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    token_str = f"{credentials.username}:{credentials.password}"
    token_bytes = token_str.encode("ascii")
    base64_bytes = base64.b64encode(token_bytes)
    base64_token = base64_bytes.decode("ascii")
    token = f"{base64_token}"

    return {"token": token, "authorization_type": "Basic"}


def create_secret_hash(username: str, app_client_id: str, app_client_secret: str):
    message = username + app_client_id
    dig = hmac.new(
        str(app_client_secret).encode("utf-8"),
        msg=str(message).encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()

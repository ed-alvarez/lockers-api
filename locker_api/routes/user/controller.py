import asyncio
import csv
import random
import re
import secrets
from math import ceil
from pathlib import Path
from random import randrange
from typing import List, Optional, Tuple, Union
from uuid import UUID

import qrcode
from async_stripe import stripe
from config import get_settings
from fastapi import HTTPException, UploadFile
from fastapi_async_sqlalchemy import db
from payments.stripe import create_ephemeral_key, get_stripe_account
from pydantic import conint, constr
from sqlalchemy import VARCHAR, and_, cast, delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError
from twilio.rest import Client
from util import email
from util.exception import format_error
from util.images import ImagesService
from util.validator import lookup_phone


from ..groups.controller import assign_user_to_group, get_group, get_groups_from_user
from ..groups.model import LinkGroupsUser
from ..login.model import Channel
from ..organization.model import LinkOrgUser, Org
from ..organization.controller import get_org_sendgrid_auth_sender, is_ups_org
from ..white_label.model import WhiteLabel
from .model import Codes, PaginatedUsers, User

stripe.api_key = get_settings().stripe_api_key


async def load_email_template(
    white_label: WhiteLabel.Read, id_org: str, org_name: str, user_obj: User.Write
):
    ROOT_DIR = Path(__file__).parent
    psub_file = ROOT_DIR / "user_signup.html"
    puser_pin_code_tpl = ROOT_DIR / "user_pin_code.html"

    # Open "user_pin_code.html" template and format
    # if user has a pin code assigned:
    with open(puser_pin_code_tpl) as user_pin_code_tpl:
        user_pin_code_tpl_str = ""

        if user_obj.pin_code:
            upc_tpl_contents = user_pin_code_tpl.read()
            upc_tpl_contents = upc_tpl_contents.replace(
                "{{user_pin_code}}", user_obj.pin_code
            )

            user_pin_code_tpl_str = upc_tpl_contents

        # Open main "user_signup.html" template and begin rune magic:
        with open(psub_file) as email_tpl:
            images_service = ImagesService()
            email_tpl_contents = email_tpl.read()
            default_logo = "https://assets.website-files.com/61f7e37730d06c4a05d2c4f3/62c640ed55a520a3d21d9b61_koloni-logo-black%207-p-500.png"

            qr_img_name = secrets.token_hex(nbytes=16)
            qr_img = qrcode.make(user_obj.json())
            qr_img.save(f"/tmp/{qr_img_name}", format="JPEG")

            # Generate and upload final user QR code and send email:
            with open(f"/tmp/{qr_img_name}", "rb") as image:
                image_upload_obj = UploadFile(
                    file=image,
                    filename=qr_img_name,
                    content_type="image/jpeg",
                )

                uploaded_image = await images_service.upload(id_org, image_upload_obj)

                return (
                    email_tpl_contents.replace(
                        "{{org_name}}",
                        white_label.app_name if white_label else org_name,
                    )
                    .replace(
                        "{{org_logo}}",
                        white_label.app_logo if white_label else default_logo,
                    )
                    .replace("{{org_url}}", f"https://{org_name}.koloni.io")
                    .replace(
                        "{{app_name}}",
                        white_label.app_name if white_label else org_name,
                    )
                    .replace("{{qr_code_image}}", uploaded_image["url"])
                    .replace("{{user_pin_code_tpl}}", user_pin_code_tpl_str)
                )


async def get_or_create_user(to: str, channel: Channel, id_org: UUID):
    query = (
        select(User)
        .where(
            or_(User.phone_number == to, User.email == to),
        )
        .order_by(User.created_at.desc())
    )
    data = await db.session.execute(query)
    user = data.scalars().first()

    if not user:
        new_user = await create_user(
            User(
                phone_number=to if channel == Channel.sms else None,
                email=to if channel == Channel.email else None,
            )
        )

    await create_user_link(id_org, user.id if user else new_user.id)

    return user if user else new_user


async def verify_user(id_user: UUID, id_org: UUID) -> dict[str, str]:
    query = select(User).where(User.id == id_user)
    data = await db.session.execute(query)

    user: User = data.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code = randrange(100000, 999999)

    if user.phone_number:
        client = Client(get_settings().twilio_sid, get_settings().twilio_secret)
        client.messages.create(
            to=user.phone_number,
            from_=get_settings().twilio_messaging_service_sid,
            body=f"Your OTP Code is: {code}",
        )
        return {
            "channel": Channel.sms,
            "code_sent": code,
        }

    if user.email:
        email_sender = await get_org_sendgrid_auth_sender(id_org)

        email.send(
            sender=email_sender,
            recipient=user.email,
            subject="Verify your email",
            html_content=f"Your OTP Code is: {code}",
            is_ups_org=await is_ups_org(id_org),
        )
        return {
            "channel": Channel.email,
            "code_sent": code,
        }

    raise HTTPException(status_code=400, detail="User has no phone number or email")


async def create_user(user: User) -> User.Read:
    query = insert(User).values(**user.dict()).returning(User)

    try:
        response = await db.session.execute(query)
        await db.session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail=f"Failed to create user, {format_error(e)}"
        )

    return response.all().pop()


async def set_random_access_code(
    id_user: UUID, id_org: UUID, depth: int = 0, max_depth: int = 25
) -> str:
    if depth > max_depth:
        raise HTTPException(
            status_code=400,
            detail="Failed to generate unique code for event",
        )

    code = "".join(random.choices("0123456789", k=6))
    query = (
        select(User)
        .join(LinkOrgUser)
        .where(
            and_(
                User.access_code == code,
                User.access_code != None,  # noqa: E711
                LinkOrgUser.id_org == id_org,
            ),  # noqa: E711
        )
    )
    response = await db.session.execute(query)
    user = response.unique().scalar_one_or_none()

    # if the code already exists, genereate a new one
    if user:
        return await set_random_access_code(
            id_user, id_org, depth=depth + 1, max_depth=max_depth
        )

    query = update(User).where(User.id == id_user).values(access_code=code)
    await db.session.execute(query)
    await db.session.commit()

    return code


async def create_many_users(users: List[User.Write], id_org: UUID) -> List[User.Read]:
    inserted_users = []

    phone_regex = re.compile(r"^\+?[1-9]\d{1,14}$")
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    for user in users:
        query = (
            select(User)
            .join(LinkOrgUser)
            .where(
                and_(
                    User.user_id == user.user_id,
                    User.user_id != None,  # noqa: E711
                    LinkOrgUser.id_org == id_org,
                )
            )
        )

        pin_query = (
            select(User)
            .join(LinkOrgUser)
            .where(
                and_(
                    User.pin_code == user.pin_code,
                    User.pin_code != None,  # noqa: E711
                    LinkOrgUser.id_org == id_org,
                ),  # noqa: E711
            )
        )

        data = await db.session.execute(query)
        pin_data = await db.session.execute(pin_query)

        user_id = data.scalar_one_or_none()
        user_pin_code = pin_data.all()

        if user_id:
            raise HTTPException(
                status_code=409,
                detail=f"User with ID '{user.user_id}' already exists",
            )

        if len(user_pin_code) > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Pin code '{user.pin_code}' already in use",
            )

        if not user.email and not user.phone_number:
            raise HTTPException(
                status_code=400,
                detail="Invalid data. Email or phone are required to create a new user.",
            )

        user_exists = None

        if user.email:
            if not email_regex.match(user.email):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid email for user.",
                )

            query = (
                select(User)
                .join(LinkOrgUser)
                .where(
                    User.email == user.email,
                    LinkOrgUser.id_org == id_org,
                )
            )

            response = await db.session.execute(query)
            user_exists = response.scalars().first()

            if user_exists:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data. An user with this email already exists.",
                )

        if user.phone_number:
            if not phone_regex.match(user.phone_number):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid phone number",
                )
            lookup_phone(user.phone_number)

            query = (
                select(User)
                .join(LinkOrgUser)
                .where(
                    User.phone_number == user.phone_number,
                    LinkOrgUser.id_org == id_org,
                )
            )

            response = await db.session.execute(query)
            user_exists = response.scalars().first()
            if user_exists:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data. An user with this phone number already exists.",
                )

        if len(user.groups) > 0:
            for id_group in user.groups:
                # Check if group UUID exists and belongs to this org
                await get_group(id_group, id_org)

        parsed_user = None

        if not user_exists:
            query = (
                insert(User)
                .values(
                    {
                        "name": user.name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "user_id": (
                            user.user_id
                            if user.user_id and user.user_id != ""
                            else None
                        ),
                        "pin_code": (
                            user.pin_code
                            if user.pin_code and user.pin_code != ""
                            else None
                        ),
                        "address": user.address,
                        "require_auth": (
                            user.require_auth if user.require_auth else False
                        ),
                    }
                )
                .returning(User)
            )

            response = await db.session.execute(query)
            await db.session.commit()

            new_user = response.all().pop()

            inserted_users.append(new_user)
            parsed_user = new_user
        else:
            query = (
                update(User)
                .where(User.id == user_exists.id)
                .values(
                    {
                        "phone_number": user.phone_number,
                        "user_id": (
                            user.user_id
                            if user.user_id and user.user_id != ""
                            else None
                        ),
                        "pin_code": (
                            user.pin_code
                            if user.pin_code and user.pin_code != ""
                            else None
                        ),
                        "require_auth": (
                            user.require_auth if user.require_auth else False
                        ),
                    }
                )
            )

            response = await db.session.execute(query)
            await db.session.commit()

            parsed_user = await db.session.execute(
                select(User).where(User.id == user_exists.id)
            )

            parsed_user = parsed_user.scalar_one()
            await create_user_link(id_org, parsed_user.id)
            inserted_users.append(parsed_user)

        await create_user_link(id_org, parsed_user.id)

        org_query = select(Org).where(Org.id == id_org)
        org_data = await db.session.execute(org_query)
        org = org_data.scalar_one_or_none()

        if user.email:
            new_user_signup_tpl = await load_email_template(
                white_label=org.white_label,
                id_org=id_org,
                org_name=org.name,
                user_obj=user,
            )

            email_sender = await get_org_sendgrid_auth_sender(id_org)

            email.send(
                sender=email_sender,
                recipient=parsed_user.email,
                subject=f"Welcome to {org.white_label.app_name if org.white_label else org.name}!",
                html_content=new_user_signup_tpl,
                is_ups_org=await is_ups_org(id_org),
            )

        if len(user.groups) > 0:
            for id_group in user.groups:
                await assign_user_to_group(id_group, parsed_user.id, id_org)

    return inserted_users


async def create_or_update_user(
    user: User.Write, id_org: UUID
) -> Tuple[Union[User.Read, None], str]:
    """
    Process and create or update a user based on the given data.
    Returns a tuple with the created/updated user and an error string.
    """

    phone_regex = re.compile(r"^\+?[1-9]\d{1,14}$")
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    error_msg = ""
    parsed_user = None

    query = select(User).where(
        and_(
            User.user_id == user.user_id,
            User.user_id != None,  # noqa: E711
        )
    )

    data = await db.session.execute(query)
    user_id = data.scalar_one_or_none()

    if user_id:
        error_msg = f"User with ID '{user.user_id}' already exists"
        return None, error_msg

    if not user.email and not user.phone_number:
        error_msg = "Invalid data. Email or phone are required to create a new user."
        return None, error_msg

    user_exists = None

    if user.email:
        if not email_regex.match(user.email):
            error_msg = "Invalid email for user."
            return None, error_msg

        query = (
            select(User)
            .join(LinkOrgUser)
            .where(
                User.email == user.email,
                LinkOrgUser.id_org == id_org,
            )
        )

        response = await db.session.execute(query)
        user_exists = response.unique().scalars().first()

        if user_exists:
            error_msg = "Invalid data. A user with this email already exists."
            return None, error_msg

    if user.phone_number:
        if not phone_regex.match(user.phone_number):
            error_msg = "Invalid phone number for user."
            return None, error_msg

        query = (
            select(User)
            .join(LinkOrgUser)
            .where(
                User.phone_number == user.phone_number,
                LinkOrgUser.id_org == id_org,
            )
        )

        response = await db.session.execute(query)
        user_exists = response.unique().scalars().first()

        if user_exists:
            error_msg = "Invalid data. A user with this phone number already exists."
            return None, error_msg

    # Assuming the existence of get_group and create_user_link functions

    if len(user.groups) > 0:
        for id_group in user.groups:
            # Check if group UUID exists and belongs to this org
            # (come back to this and check what is really going on here)
            await get_group(id_group, id_org)

    if not user_exists:
        query = (
            insert(User)
            .values(
                {
                    "name": user.name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "user_id": (
                        user.user_id if user.user_id and user.user_id != "" else None
                    ),
                    "pin_code": (
                        user.pin_code if user.pin_code and user.pin_code != "" else None
                    ),
                    "address": user.address,
                    "require_auth": user.require_auth if user.require_auth else False,
                }
            )
            .returning(User)
        )

        response = await db.session.execute(query)
        await db.session.commit()

        parsed_user = response.all().pop()

    else:
        query = (
            update(User)
            .where(User.id == user_exists.id)
            .values(
                {
                    "phone_number": user.phone_number,
                    "user_id": (
                        user.user_id if user.user_id and user.user_id != "" else None
                    ),
                    "pin_code": (
                        user.pin_code if user.pin_code and user.pin_code != "" else None
                    ),
                    "require_auth": user.require_auth if user.require_auth else False,
                }
            )
        )

        response = await db.session.execute(query)
        await db.session.commit()

        parsed_user = await db.session.execute(
            select(User).where(User.id == user_exists.id)
        )
        parsed_user = parsed_user.scalar_one()

    await create_user_link(id_org, parsed_user.id)

    org_query = select(Org).where(Org.id == id_org)
    org_data = await db.session.execute(org_query)
    org = org_data.scalar_one_or_none()

    # Assuming the existence of load_email_template and email.send functions
    if user.email:
        new_user_signup_tpl = load_email_template(
            white_label=org.white_label, id_org=id_org, org_name=org.name, user_obj=user
        )

        email_sender = await get_org_sendgrid_auth_sender(id_org)

        email.send(
            sender=email_sender,
            recipient=parsed_user.email,
            subject=f"Welcome to {org.white_label.app_name}!",
            html_content=new_user_signup_tpl,
            is_ups_org=await is_ups_org(id_org),
        )

    if len(user.groups) > 0:
        for id_group in user.groups:
            # Assuming the existence of assign_user_to_group function
            await assign_user_to_group(id_group, parsed_user.id, id_org)

    return parsed_user, error_msg


async def process_csv_upload(
    file: UploadFile, id_org: UUID
) -> List[Tuple[Optional[User.Read], str]]:
    """
    Process a CSV upload to create or update users.

    The CSV is expected to have headers and the following format:
    user_id, name, email, phone_number, pin_code, address, groups

    Returns a list of tuples, each containing the User and an error message string.
    If the User is None, it means there was an error for that entry.
    """

    results = []

    # Read and decode the CSV contents
    contents = await file.read()
    csv_content = contents.decode()

    # Use DictReader as it allows to directly map CSV headers to dictionary keys
    csv_reader = csv.DictReader(csv_content.splitlines())

    # Check for limits on the number of records
    if sum(1 for _ in csv_reader) > get_settings().MAX_CSV_RECORDS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many records. Limit is {get_settings().MAX_CSV_RECORDS} per upload.",
        )

    # Resetting the CSV reader cursor to the start after counting the rows
    csv_reader = csv.DictReader(csv_content.splitlines())

    for row in csv_reader:
        try:
            # Parsing each CSV row into User.Write type
            user_data = User.Write(
                user_id=row.get("user_id") or None,
                name=row.get("name") or None,
                email=row.get("email") or None,
                phone_number=row.get("phone_number") or None,
                pin_code=row.get("pin_code") or None,
                address=row.get("address") or None,
                groups=row.get("groups").split(";") if row.get("groups") else [],
                # Assuming groups are semicolon-separated
            )

            # Setting a timeout for processing each user
            user, error_msg = await asyncio.wait_for(
                create_or_update_user(user_data, id_org), get_settings().TIMEOUT_SECONDS
            )
            results.append((user, error_msg))
        except asyncio.TimeoutError:
            results.append(
                (
                    None,
                    f"Processing timeout for record with user_id={row.get('user_id')}",
                )
            )
        except Exception as e:
            # Append the error message and None for the user.
            results.append((None, str(e)))

    return results


async def get_user_subscription(id_user: UUID, id_org: UUID) -> Optional[LinkOrgUser]:
    query = (
        select(LinkOrgUser)
        .where(LinkOrgUser.id_user == id_user)
        .where(LinkOrgUser.id_org == id_org)
    )

    data = await db.session.execute(query)

    return data.unique().scalar_one_or_none()


async def get_default_payment_method(id_org: UUID, id_user: UUID):
    stripe_account = await get_stripe_account(id_org)
    # Here I'm trusting that the get_or_create won't do funky stuff
    # in certain scenarios. (just in case something fails in the future, look into this)

    customer_id = await get_or_create_stripe_customer(id_user, id_org)

    customer = await stripe.Customer.retrieve(
        customer_id,
        stripe_account=stripe_account,
    )

    if not customer.invoice_settings.default_payment_method:
        raise HTTPException(
            status_code=400, detail="You don't have a default payment method."
        )

    payment_method = await stripe.PaymentMethod.retrieve(
        customer.invoice_settings.default_payment_method, stripe_account=stripe_account
    )

    return {
        "default_payment_method": customer.invoice_settings.default_payment_method,
        "last4": payment_method.card.last4,
    }


async def setup_default_payment_method(id_org: UUID, id_user: UUID):
    stripe_account = await get_stripe_account(id_org)

    customer_id = await get_or_create_stripe_customer(id_user, id_org)

    customer = await stripe.Customer.retrieve(
        customer_id,
        stripe_account=stripe_account,
    )

    if customer.invoice_settings.default_payment_method:
        raise HTTPException(
            status_code=400, detail="user already has a default payment method"
        )

    setup_intent = await stripe.SetupIntent.create(
        customer=customer_id,
        stripe_account=stripe_account,
    )

    return {
        "client_secret": setup_intent.client_secret,
        "publishable_key": get_settings().stripe_pub_key,
        "stripe_account_id": stripe_account,
    }


async def confirm_default_payment_method(
    id_org: UUID, id_user: UUID, setup_intent: str
):
    stripe_account = await get_stripe_account(id_org)

    customer_id = await get_or_create_stripe_customer(id_user, id_org)

    setup = await stripe.SetupIntent.retrieve(
        setup_intent,
        stripe_account=stripe_account,
    )

    if setup.status != "succeeded":
        raise HTTPException(status_code=400, detail="payment method is still pending")

    # charge 1 dollar to confirm the payment method

    payment = await stripe.PaymentIntent.create(
        amount=100,
        currency="usd",
        customer=customer_id,
        payment_method=setup.payment_method,
        confirm=True,
        off_session=True,
        stripe_account=stripe_account,
    )

    if payment.status != "succeeded":
        raise HTTPException(status_code=400, detail="payment method is still pending")

        # refund the 1 dollar charge

    await stripe.Refund.create(
        payment_intent=payment.id,
        stripe_account=stripe_account,
    )

    await stripe.Customer.modify(
        customer_id,
        invoice_settings=(
            {"default_payment_method": setup.payment_method} if setup else None
        ),
        stripe_account=stripe_account,
    )

    return {"detail": "succeeded"}


async def get_payment_methods(id_org: UUID, id_user: UUID):
    stripe_account = await get_stripe_account(id_org)

    customer_id = await get_or_create_stripe_customer(id_user, id_org)

    payment_methods = await stripe.PaymentMethod.list(
        customer=customer_id,
        type="card",
        stripe_account=stripe_account,
    )

    return [
        {
            "id": payment_method.id,
            "card": (
                {
                    "brand": payment_method.card.brand,
                    "exp_month": payment_method.card.exp_month,
                    "exp_year": payment_method.card.exp_year,
                    "last4": payment_method.card.last4,
                }
                if payment_method.type == "card"
                else None
            ),
            "paypal": (
                {
                    "email": payment_method.paypal.email,
                }
                if payment_method.type == "paypal"
                else None
            ),
        }
        for payment_method in payment_methods
    ]


async def add_payment_method(id_org: UUID, id_user: UUID):
    stripe_account = await get_stripe_account(id_org)

    customer_id = await get_or_create_stripe_customer(id_user, id_org)

    setup_intent = await stripe.SetupIntent.create(
        customer=customer_id,
        stripe_account=stripe_account,
    )

    ephemeral_key = await create_ephemeral_key(customer_id, stripe_account)

    return {
        "client_secret": setup_intent.client_secret,
        "publishable_key": get_settings().stripe_pub_key,
        "ephemeral_key": ephemeral_key,
        "stripe_account_id": stripe_account,
        "customer_id": customer_id,
    }


async def delete_payment_method(id_org: UUID, id_user: UUID, pm_id: str):
    stripe_account = await get_stripe_account(id_org)

    customer_id = await get_or_create_stripe_customer(id_user, id_org)

    payment_method = await stripe.PaymentMethod.retrieve(
        pm_id,
        stripe_account=stripe_account,
    )

    if payment_method.customer != customer_id:
        raise HTTPException(
            status_code=400, detail="payment method does not belong to user"
        )

    await stripe.PaymentMethod.detach(
        pm_id,
        stripe_account=stripe_account,
    )

    return {"detail": "payment method deleted"}


async def get_user_payment_method(id_org: UUID, id_user: UUID) -> str:
    stripe_account = await get_stripe_account(id_org)

    customer_id = await get_or_create_stripe_customer(id_user, id_org)

    customer = await stripe.Customer.retrieve(
        customer_id,
        stripe_account=stripe_account,
    )

    if not customer.invoice_settings.default_payment_method:
        raise HTTPException(status_code=400, detail="user has no payment method")

    payment_method = await stripe.PaymentMethod.retrieve(
        customer.invoice_settings.default_payment_method,
        stripe_account=stripe_account,
    )

    return {
        "payment_method_id": payment_method.id,
    }


async def add_user_subscription(
    id_user: UUID, id_org: UUID, subscription_id: str, id_membership: UUID
) -> Optional[str]:
    query = (
        update(LinkOrgUser)
        .where(LinkOrgUser.id_user == id_user)
        .where(LinkOrgUser.id_org == id_org)
        .values(stripe_subscription_id=subscription_id, id_membership=id_membership)
        .returning(LinkOrgUser.stripe_subscription_id)
    )

    data = await db.session.execute(query)
    await db.session.commit()

    subscription_update = data.scalar_one_or_none()

    return subscription_update


async def remove_user_subscription(id_user: UUID, id_org: UUID) -> Optional[str]:
    query = (
        update(LinkOrgUser)
        .where(LinkOrgUser.id_user == id_user)
        .where(LinkOrgUser.id_org == id_org)
        .values(stripe_subscription_id=None, id_membership=None)
        .returning(LinkOrgUser.stripe_subscription_id)
    )

    data = await db.session.execute(query)

    await db.session.commit()

    subscription_removal = data.scalar_one_or_none()

    return subscription_removal


async def update_user(id_user: UUID, user: User.Write | User.MobileWrite, id_org: UUID):
    # Checking if the user exists

    query = select(LinkOrgUser).where(
        LinkOrgUser.id_user == id_user, LinkOrgUser.id_org == id_org
    )

    response = await db.session.execute(query)

    data = response.unique().scalar_one_or_none()

    if not data:
        raise HTTPException(status_code=404, detail=f"User '{id_user}' not found")

    phone_regex = re.compile(r"^\+?[1-9]\d{1,14}$")
    if user.phone_number:
        if not phone_regex.match(user.phone_number):
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number",
            )
        lookup_phone(user.phone_number)

    try:
        if user.pin_code:
            pin_query = (
                select(User)
                .join(LinkOrgUser)
                .where(
                    and_(
                        User.pin_code == user.pin_code,
                        User.pin_code != None,  # noqa: E711
                        User.id != id_user,
                        LinkOrgUser.id_org == id_org,
                    )
                )
            )
            pin_response = await db.session.execute(pin_query)

            # Using .all() for now due to existing records in our database with
            # the same pin code. This should be removed in the future.
            pin_data = pin_response.all()

            if len(pin_data) > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Pin code '{user.pin_code}' already in use",
                )

        if len(user.groups) > 0:
            for id_group in user.groups:
                # Check if group UUID exists and belongs to this org
                await get_group(id_group, id_org)
    except AttributeError:
        # If the user doesn't have a pin_code (update coming from Mobile), just ignore the exception
        pass

    if type(user) == User.Write:
        query = (
            update(User)
            .where(User.id == id_user)
            .values(
                name=user.name,
                email=user.email,
                phone_number=user.phone_number,
                user_id=user.user_id,
                pin_code=user.pin_code,
                address=user.address,
                active=user.active,
                require_auth=user.require_auth,
            )
            .returning(User)
        )
    else:
        query = (
            update(User)
            .where(User.id == id_user)
            .values(
                name=user.name,
                email=user.email,
                phone_number=user.phone_number,
                address=user.address,
            )
            .returning(User)
        )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        if len(user.groups) > 0:
            for id_group in user.groups:
                await assign_user_to_group(id_group, id_user, id_org)
    except AttributeError:
        # If the user doesn't have groups (update coming from Mobile), just ignore the exception
        pass

    try:
        updated_user = response.all().pop()

        return updated_user
    except IndexError:
        raise HTTPException(status_code=404, detail=f"User '{id_user}' not found")


async def get_or_create_stripe_customer(id_user: UUID, id_org: UUID):
    # Querying for existing Stripe customer

    query = (
        select(LinkOrgUser.stripe_customer_id)
        .where(LinkOrgUser.id_user == id_user)
        .where(LinkOrgUser.id_org == id_org)
    )

    data = await db.session.execute(query)

    stripe_customer = data.unique().scalars().first()

    if not stripe_customer:
        new_stripe_customer = await create_stripe_customer(id_user, id_org)

        return new_stripe_customer

    return stripe_customer


async def create_stripe_customer(id_user: UUID, id_org: UUID):
    # Retrieving the Stripe account

    stripe_account = await get_stripe_account(id_org)

    try:
        stripe_customer = await stripe.Customer.create(stripe_account=stripe_account)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create stripe customer, {e}",
        )

    update_query = (
        update(LinkOrgUser)
        .where(LinkOrgUser.id_user == id_user)
        .where(LinkOrgUser.id_org == id_org)
        .values(stripe_customer_id=stripe_customer["id"])
        .returning(LinkOrgUser.stripe_customer_id)
    )

    try:
        response = await db.session.execute(update_query)
        await db.session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Failed to create stripe customer, {format_error(e)}",
        )

    return response.scalars().first()


async def get_user_link(id_org: UUID, id_user: UUID):
    query = select(LinkOrgUser).where(
        LinkOrgUser.id_org == id_org, LinkOrgUser.id_user == id_user
    )

    data = await db.session.execute(query)

    link = data.unique().scalar_one_or_none()

    return link


async def create_user_link(id_org: UUID, id_user: UUID):
    # Checking if the link already exists

    link = await get_user_link(id_org, id_user)

    if link:
        return link

    query = (
        insert(LinkOrgUser)
        .values(id_org=id_org, id_user=id_user)
        .returning(LinkOrgUser)
    )

    try:
        response = await db.session.execute(query)
        await db.session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Failed to create user link, {format_error(e)}",
        )

    new_link = response.all().pop()

    return new_link


async def get_users(
    page: conint(gt=0),
    size: conint(gt=0),
    id_org: UUID,
    search: Optional[str],
    by_phone: Optional[bool] = None,
    by_email: Optional[bool] = None,
    by_first_name: Optional[bool] = None,
    by_user_id: Optional[bool] = None,
    by_last_name: Optional[bool] = None,
):
    query = select(User).join(LinkOrgUser).where(LinkOrgUser.id_org == id_org)

    if search:
        query = query.filter(
            or_(
                (
                    User.name.ilike(f"%{search}%")
                    if by_first_name or by_last_name
                    else None
                ),
                User.email.ilike(f"%{search}%") if by_email else None,
                User.phone_number.ilike(f"%{search}%") if by_phone else None,
                User.user_id.ilike(f"%{search}%") if by_user_id else None,
            )
        )

    count = query

    query = query.limit(size).offset((page - 1) * size).order_by(User.created_at.desc())

    data = await db.session.execute(query)
    counter = await db.session.execute(count)

    total_count = len(counter.all())

    total_pages = ceil(total_count / size)

    users = data.scalars().all()
    response: list[User.Read] = []
    for user in users:
        user = User.Read.parse_obj(user)
        user.groups = await get_groups_from_user(user.id, id_org)
        response.append(user)

    return PaginatedUsers(
        items=response,
        total=total_count,
        pages=total_pages,
    )


async def get_user(id_user: UUID, id_org: Optional[UUID] = None) -> User.Read:
    query = select(User).where(User.id == id_user)

    data = await db.session.execute(query)

    data = User.Read.parse_obj(data.scalar_one())

    if id_org:
        data.groups = await get_groups_from_user(id_user, id_org)

    return data


async def get_user_by_key(key: str, value: str, id_org: UUID) -> User.Read:
    query = select(User).join(LinkOrgUser).where(LinkOrgUser.id_org == id_org)

    if key not in User.__table__.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field: {key}",
        )
    query = query.filter(cast(User.__table__.columns[key], VARCHAR) == value)

    result = await db.session.execute(query)

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.require_auth:
        res = await verify_user(user.id, id_org)

        await save_code(str(res["code_sent"]), user.id, id_org)

    return user


async def save_code(code: str, id_user: UUID, id_org: UUID):
    query = select(Codes).where(Codes.id_user == id_user, Codes.id_org == id_org)

    result = await db.session.execute(query)

    code_exists = result.scalars().first()

    next_query = (
        insert(Codes).values(code=code, id_user=id_user, id_org=id_org).returning(Codes)
    )

    if code_exists:
        next_query = (
            update(Codes)
            .where(Codes.id_user == id_user, Codes.id_org == id_org)
            .values(code=code)
            .returning(Codes)
        )

    result = await db.session.execute(next_query)
    await db.session.commit()

    return result.scalars().first()


async def get_and_verify_code(code: str, id_org: UUID):
    query = select(Codes).where(Codes.code == code, Codes.id_org == id_org)

    result = await db.session.execute(query)

    code = result.scalars().first()

    if not code:
        raise HTTPException(
            status_code=404,
            detail="No code found",
        )

    query = delete(Codes).where(Codes.id == code.id)

    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Code verified successfully"}


async def get_user_by_code(
    code: constr(regex=r"\d{4}"), id_org: UUID
) -> Optional[User.Read]:
    query = (
        select(User)
        .join(LinkOrgUser)
        .where(User.pin_code == code, LinkOrgUser.id_org == id_org)
    )

    result = await db.session.execute(query)

    return result.scalars().first()


async def update_user_name(name: str, id_user: UUID):
    query = update(User).where(User.id == id_user).values(name=name).returning(User)

    try:
        response = await db.session.execute(query)
        await db.session.commit()

    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Failed to update user name, {format_error(e)}",
        )

    return response.all().pop()


async def add_phone_or_email(
    to: str,
    channel: Channel,
    id_user: UUID,
):
    if channel == Channel.sms and not re.match(r"^\+[1-9]\d{1,14}$", to):
        raise HTTPException(
            status_code=400,
            detail=f"phone number '{to}' is not valid",
        )

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    try:
        verification = client.verify.v2.services(
            get_settings().twilio_verification_sid
        ).verifications.create(to=to, channel=channel.value)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "sid": verification.sid,
        "to": verification.to,
        "channel": verification.channel,
        "status": verification.status,
    }


async def verify_phone_or_email(
    to: str,
    channel: Channel,
    code: str,
    id_user: UUID,
) -> User.Read:
    select_query = select(User).where(User.id == id_user)

    data = await db.session.execute(select_query)
    user = data.scalar_one()  # raises NoResultFound

    client = Client(get_settings().twilio_sid, get_settings().twilio_secret)

    try:
        verification = client.verify.v2.services(
            get_settings().twilio_verification_sid
        ).verification_checks.create(to=to, code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if verification.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Failed to verify phone or email, {verification.status}",
        )

    # Check if phone or email is already in use, if so remove it from the user

    query = select(User).where(or_(User.phone_number == to, User.email == to))
    response = await db.session.execute(query)
    data = response.scalars().first()

    if data:
        await remove_user_cred(data.id, channel)

    query = (
        update(User)
        .where(User.id == id_user)
        .values(
            phone_number=to if channel == Channel.sms else user.phone_number,
            email=to if channel == Channel.email else user.email,
        )
        .returning(User)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def remove_user_cred(id_user: UUID, channel: Channel):
    query = (
        update(User)
        .where(User.id == id_user)
        .values(
            phone_number=None if channel == Channel.sms else User.phone_number,
            email=None if channel == Channel.email else User.email,
        )
        .returning(User)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def delete_users(users: List[UUID], id_org: UUID):
    query = delete(LinkOrgUser).where(
        LinkOrgUser.id_org == id_org, LinkOrgUser.id_user.in_(users)
    )

    unlink_group_query = delete(LinkGroupsUser).where(LinkGroupsUser.id_user.in_(users))

    if len(users) == 0:
        raise HTTPException(400, detail="Insert a valid list of user UUIDs to delete")

    # Unlink from groups first
    response = await db.session.execute(unlink_group_query)
    await db.session.commit()
    # Unlink from organization
    response = await db.session.execute(query)
    await db.session.commit()

    return {
        "detail": f"Deleted {response.rowcount} user(s)",
    }

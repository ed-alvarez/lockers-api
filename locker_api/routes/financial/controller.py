from typing import Optional
from uuid import UUID

from async_stripe import stripe
from config import get_settings
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, NoResultFound


from ..organization.model import LinkOrgUser, Org
from .model import StripeCountry

stripe.api_key = get_settings().stripe_api_key


async def get_stripe_account(id_org: UUID):
    data = await db.session.execute(
        select(Org.stripe_account_id).where(Org.id == id_org)
    )
    stripe_account = data.scalar_one_or_none()

    if not stripe_account:
        error_detail = f"Org with id {id_org} does not have a Stripe Account"

        raise HTTPException(
            status_code=404,
            detail=error_detail,
        )

    account = await stripe.Account.retrieve(stripe_account)

    return account


async def delete_stripe_account(id_org: UUID):
    data = await db.session.execute(
        select(Org.stripe_account_id).where(Org.id == id_org)
    )
    stripe_account = data.scalar_one_or_none()

    if not stripe_account:
        error_detail = f"Org with id {id_org} does not have a Stripe Account"

        raise HTTPException(
            status_code=404,
            detail=error_detail,
        )

    await stripe.Account.delete(stripe_account)

    query = update(Org).where(Org.id == id_org).values(stripe_account_id=None)
    await db.session.execute(query)
    await db.session.commit()

    query = (
        update(LinkOrgUser)
        .where(LinkOrgUser.id_org == id_org)
        .values(stripe_customer_id=None)
    )
    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Stripe Account Deleted"}


async def create_stripe_account(
    email: str, id_org: UUID, country: Optional[StripeCountry] = StripeCountry.US
):
    # See if the org already has a stripe account

    data = await db.session.execute(
        select(Org.stripe_account_id).where(Org.id == id_org)
    )

    try:
        if data.scalar_one():
            error_detail = f"Org with id {id_org} already has a Stripe Account"

            raise HTTPException(
                status_code=400,
                detail=error_detail,
            )
    except NoResultFound:
        error_detail = f"Org with id {id_org} was not found"

        raise HTTPException(
            status_code=404,
            detail=error_detail,
        )

    # Create the stripe account
    try:
        stripe_account = await stripe.Account.create(
            country=country.value,
            type="express",
            email=email,
            capabilities={
                "transfers": {"requested": True},
                "card_payments": {"requested": True},
            },
            metadata={"id_org": str(id_org)},
        )

    except stripe.error.InvalidRequestError as e:
        error_detail = e.user_message

        raise HTTPException(status_code=400, detail=error_detail)

    # Update the org with the stripe account id

    query = (
        update(Org)
        .where(Org.id == id_org)
        .values(stripe_account_id=stripe_account.id)
        .returning(Org.stripe_account_id)
    )

    try:
        response = await db.session.execute(query)
        await db.session.commit()

    except IntegrityError:
        error_detail = "Org already has a Stripe Account"

        raise HTTPException(status_code=400, detail=error_detail)

    return response.scalar_one()


async def create_stripe_link(
    id_org: UUID, email: str, country: Optional[StripeCountry] = StripeCountry.US
):
    data = await db.session.execute(select(Org).where(Org.id == id_org))
    try:
        org = data.scalar_one()
    except NoResultFound:
        error_detail = f"Org with id {id_org} was not found"

        raise HTTPException(
            status_code=404,
            detail=error_detail,
        )

    if not org.stripe_account_id:
        stripe_account = await create_stripe_account(
            email=email, id_org=id_org, country=country
        )

    refresh_url = f"https://{org.name}.koloni.io/"

    try:
        account_link = await stripe.AccountLink.create(
            account=org.stripe_account_id or stripe_account,
            refresh_url=refresh_url,
            return_url=refresh_url,
            type="account_onboarding",
        )

        return account_link.url
    except stripe.error.InvalidRequestError as e:
        error_detail = e.user_message

        raise HTTPException(status_code=400, detail=error_detail)

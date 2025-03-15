from uuid import UUID

from async_stripe import stripe
from config import get_settings
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from routes.organization.model import Org
from sqlalchemy import select

stripe.api_key = get_settings().stripe_api_key


async def get_stripe_account(
    id_org: UUID,
):
    query = select(Org.stripe_account_id).where(Org.id == id_org)

    result = await db.session.execute(query)

    stripe_account = result.scalars().first()

    if not stripe_account:
        raise HTTPException(status_code=404, detail="Stripe account not found")

    return stripe_account


async def create_setup_intent(
    id_org: UUID,
    stripe_customer: str,
    stripe_account: str,
):
    setup_intent = await stripe.SetupIntent.create(
        payment_method_types=["card"],
        customer=stripe_customer,
        metadata=dict(
            id_org=id_org,
        ),
        stripe_account=stripe_account,
    )

    return setup_intent


async def create_ephemeral_key(
    stripe_customer: str,
    stripe_account: str,
):
    ephemeral_key = await stripe.EphemeralKey.create(
        customer=stripe_customer,
        stripe_account=stripe_account,
        stripe_version="2020-08-27",
    )

    return ephemeral_key

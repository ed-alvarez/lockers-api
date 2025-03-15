from datetime import datetime, timedelta
from math import ceil
from typing import Optional
from uuid import UUID

from async_stripe import stripe
from config import get_settings
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from payments.stripe import get_stripe_account
from pydantic import conint
from sqlalchemy import VARCHAR, cast, delete, insert, or_, select, update


from ..organization.model import LinkOrgUser
from ..user.controller import (
    add_user_subscription,
    get_or_create_stripe_customer,
    get_user_link,
    remove_user_subscription,
)
from .model import (
    BillingPeriod,
    BillingType,
    LinkMembershipLocation,
    Membership,
    MembershipType,
    PaginatedMemberships,
    SubscriptionResponse,
)

stripe.api_key = get_settings().stripe_api_key


async def get_user_membership(id_org: UUID, id_user: UUID) -> Optional[Membership.Read]:
    stripe_account = await get_stripe_account(id_org)

    link = await get_user_link(id_org, id_user)

    try:
        stripe_subscription = await stripe.Subscription.retrieve(
            link.stripe_subscription_id,
            stripe_account=stripe_account,
        )
    except Exception:
        return None

    if stripe_subscription.status != "active":
        return None

    return await get_membership(link.id_membership, id_org)


async def get_current_membership(id_org: UUID, id_user: UUID) -> Membership.Read:
    stripe_account = await get_stripe_account(id_org)

    link = await get_user_link(id_org, id_user)

    if not link.stripe_subscription_id:
        error_detail = "User is not subscribed to a membership in this organization"

        raise HTTPException(status_code=404, detail=error_detail)

    membership = await get_membership(link.id_membership, id_org)

    stripe_subscription = await stripe.Subscription.retrieve(
        link.stripe_subscription_id,
        stripe_account=stripe_account,
    )

    if stripe_subscription.status != "active":
        error_detail = (
            "User is subscribed to a membership but the subscription is not active"
        )

        raise HTTPException(status_code=400, detail=error_detail)

    return membership


async def subscribe(
    id_membership: UUID, id_org: UUID, id_user: UUID, payment_method: Optional[str]
) -> Membership.Read:
    link = await get_user_link(id_org, id_user)

    if link.stripe_subscription_id:
        error_detail = "User already subscribed to a membership in this organization"

        raise HTTPException(status_code=400, detail=error_detail)

    customer_id = await get_or_create_stripe_customer(id_user, id_org)

    membership = await get_membership(id_membership, id_org)

    if not membership.active:
        error_detail = "Membership is not active"

        raise HTTPException(status_code=400, detail=error_detail)

    # * This is to avoid a race condition

    await add_user_subscription(id_user, id_org, "Idempotency", id_membership)

    try:
        stripe_account = await get_stripe_account(id_org)
    except HTTPException:
        await remove_user_subscription(id_user, id_org)
        raise HTTPException(
            status_code=400,
            detail="Stripe account not found",
        )

    period = None

    match membership.billing_period:
        case BillingPeriod.day:
            period = 1

        case BillingPeriod.week:
            period = 7

        case BillingPeriod.month:
            period = 30

        case BillingPeriod.year:
            period = 365

        case _:
            error_detail = "Invalid billing period"

            raise HTTPException(status_code=400, detail=error_detail)

    cancel_at = (
        datetime.utcnow() + timedelta(days=membership.number_of_payments * period)
        if membership.number_of_payments > 0
        else None
    )

    try:
        stripe_subscription = await stripe.Subscription.create(
            customer=customer_id,
            items=[
                {
                    "price": membership.stripe_price_id,
                }
            ],
            cancel_at=cancel_at,
            stripe_account=stripe_account,
            default_payment_method=payment_method if payment_method else None,
        )
    except stripe.error.InvalidRequestError as e:
        await remove_user_subscription(id_user, id_org)
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    await add_user_subscription(id_user, id_org, stripe_subscription.id, membership.id)

    invoice = await stripe.Invoice.retrieve(
        stripe_subscription.latest_invoice,
        stripe_account=stripe_account,
    )

    return SubscriptionResponse(
        membership=membership,
        invoice_url=invoice.hosted_invoice_url,
    )


async def cancel_subscription(id_org: UUID, id_user: UUID) -> dict:
    link = await get_user_link(id_org, id_user)

    if not link.stripe_subscription_id:
        error_detail = "User is not subscribed to a membership in this organization"

        raise HTTPException(status_code=404, detail=error_detail)

    stripe_account = await get_stripe_account(id_org)

    try:
        await stripe.Subscription.delete(
            link.stripe_subscription_id,
            stripe_account=stripe_account,
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to cancel subscription in Stripe"
        )

    await remove_user_subscription(id_user, id_org)

    return {"detail": "Subscription cancelled"}


async def get_memberships(
    current_org: UUID,
    page: conint(gt=0) = 1,
    size: conint(gt=0) = 50,
    id_membership: Optional[UUID] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    search: Optional[str] = None,
    subscribed: bool = False,
    id_location: Optional[UUID] = None,
) -> PaginatedMemberships | Membership.Read:
    query = select(Membership).where(Membership.id_org == current_org)

    if id_membership:
        # * Early return if id_membership is provided

        query = query.where(Membership.id == id_membership)
        result = await db.session.execute(query)
        return result.unique().scalar_one()

    if key and value:
        # * Early return if key and value are provided

        if key not in Membership.__table__.columns:
            error_detail = f"Invalid field: {key}"

            raise HTTPException(status_code=400, detail=error_detail)

        query = query.where(cast(Membership.__table__.columns[key], VARCHAR) == value)

        result = await db.session.execute(query)
        return result.unique().scalar_one()

    if subscribed:
        query = query.join_from(
            Membership, LinkOrgUser, Membership.id == LinkOrgUser.id_membership
        )

    if search:
        query = query.where(
            or_(
                Membership.name.ilike(f"%{search}%"),
                Membership.description.ilike(f"%{search}%"),
            )
        )

    if id_location:
        query = query.join(LinkMembershipLocation).where(
            LinkMembershipLocation.id_location == id_location
        )

    count = query

    query = (
        query.limit(size)
        .offset((page - 1) * size)
        .order_by(Membership.created_at.desc())
    )

    data = await db.session.execute(query)
    total = await db.session.execute(count)

    total_count = len(total.unique().all())

    return PaginatedMemberships(
        items=data.unique().scalars().all(),
        total=total_count,
        pages=ceil(total_count / size),
    )


async def get_membership(id_membership: UUID, current_org: UUID) -> Membership.Read:
    query = select(Membership).where(
        Membership.id == id_membership, Membership.id_org == current_org
    )

    data = await db.session.execute(query)

    return data.unique().scalar_one()


async def partner_create_membership(
    membership: Membership.Write, current_org: UUID
) -> Membership.Read:
    if (
        membership.billing_type == BillingType.one_time
        and membership.number_of_payments <= 0
    ):
        error_detail = (
            "Number of payments must be greater than 0 for one-time memberships"
        )

        raise HTTPException(status_code=400, detail=error_detail)
    if (
        membership.membership_type == MembershipType.limited
        and not float(membership.value).is_integer()
    ):
        error_detail = "Value must be an integer for limited memberships"

        raise HTTPException(status_code=400, detail=error_detail)

    stripe_account = await get_stripe_account(current_org)

    product = await stripe.Product.create(
        name=membership.name,
        description=membership.description,
        metadata={"id_org": str(current_org)},
        stripe_account=stripe_account,
    )

    price = await stripe.Price.create(
        unit_amount=int(membership.amount * 100),
        currency=membership.currency.value,
        recurring={
            "interval": membership.billing_period.value,
            "interval_count": membership.number_of_payments
            if membership.number_of_payments > 0
            else None,
        },
        product=product.id,
        stripe_account=stripe_account,
    )

    new_membership = Membership(
        name=membership.name,
        description=membership.description,
        currency=membership.currency,
        amount=membership.amount,
        active=membership.active,
        billing_type=membership.billing_type,
        billing_period=membership.billing_period,
        number_of_payments=membership.number_of_payments,
        membership_type=membership.membership_type,
        value=membership.value,
        stripe_product_id=product.id,
        stripe_price_id=price.id,
        id_org=current_org,
    )

    query = insert(Membership).values(new_membership.dict()).returning(Membership)

    data = await db.session.execute(query)
    await db.session.commit()

    inserted_membership = data.unique().all().pop()

    if membership.locations:
        query = insert(LinkMembershipLocation).values(
            [
                {"id_membership": inserted_membership.id, "id_location": location}
                for location in membership.locations
            ]
        )

        await db.session.execute(query)
        await db.session.commit()

    return inserted_membership


async def create_membership_csv(id_org: UUID, membership: Membership.Write):
    try:
        await partner_create_membership(membership, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def update_membership_csv(
    id_org: UUID, membership: Membership.Write, id_membership: UUID
):
    try:
        await partner_update_membership(id_membership, membership, id_org)

        return True
    except HTTPException as e:
        return e.detail


async def partner_delete_membership(
    id_membership: UUID, current_org: UUID
) -> Membership.Read:
    stripe_account = await get_stripe_account(current_org)

    query = select(Membership).where(
        Membership.id == id_membership, Membership.id_org == current_org
    )
    data = await db.session.execute(query)
    membership = data.unique().scalar_one()

    try:
        await stripe.Price.modify(
            membership.stripe_price_id, active=False, stripe_account=stripe_account
        )
        await stripe.Product.modify(
            membership.stripe_product_id,
            active=False,
            stripe_account=stripe_account,
        )
    except stripe.error.InvalidRequestError:
        pass

    query = select(LinkOrgUser).where(
        LinkOrgUser.id_membership == id_membership, LinkOrgUser.id_org == current_org
    )
    data = await db.session.execute(query)
    subscriptions = data.unique().scalars().all()

    for subscription in subscriptions:
        try:
            await cancel_subscription(current_org, subscription.id_user)
        except stripe.error.InvalidRequestError:
            pass

    query = delete(Membership).where(
        Membership.id == id_membership, Membership.id_org == current_org
    )

    await db.session.execute(query)
    await db.session.commit()

    query = delete(LinkMembershipLocation).where(
        LinkMembershipLocation.id_membership == id_membership
    )

    await db.session.execute(query)
    await db.session.commit()

    return membership


async def partner_delete_memberships(id_memberships: list[UUID], current_org: UUID):
    stripe_account = await get_stripe_account(current_org)

    query = select(Membership).where(
        Membership.id_org == current_org, Membership.id.in_(id_memberships)
    )

    data = await db.session.execute(query)
    memberships = data.unique().scalars().all()

    for membership in memberships:
        try:
            await stripe.Price.modify(
                membership.stripe_price_id, active=False, stripe_account=stripe_account
            )
            await stripe.Product.modify(
                membership.stripe_product_id,
                active=False,
                stripe_account=stripe_account,
            )
        except stripe.error.InvalidRequestError:
            pass

        query = select(LinkOrgUser).where(
            LinkOrgUser.id_membership == membership.id,
            LinkOrgUser.id_org == current_org,
        )

        data = await db.session.execute(query)
        subscriptions = data.unique().scalars().all()

        for subscription in subscriptions:
            try:
                await cancel_subscription(current_org, subscription.id_user)
            except stripe.error.InvalidRequestError:
                pass

    query = delete(Membership).where(
        Membership.id_org == current_org, Membership.id.in_(id_memberships)
    )

    await db.session.execute(query)
    await db.session.commit()

    query = delete(LinkMembershipLocation).where(
        LinkMembershipLocation.id_membership.in_(id_memberships)
    )
    await db.session.execute(query)
    await db.session.commit()

    return {"detail": "Memberships deleted"}


async def partner_update_membership(
    id_membership: UUID, membership: Membership.Write, current_org: UUID
) -> Membership.Read:
    if (
        membership.billing_type == BillingType.one_time
        and membership.number_of_payments <= 0
    ):
        error_detail = (
            "Number of payments must be greater than 0 for one-time memberships"
        )

        raise HTTPException(status_code=400, detail=error_detail)
    if (
        membership.membership_type == MembershipType.limited
        and not float(membership.value).is_integer()
    ):
        error_detail = "Value must be an integer for limited memberships"

        raise HTTPException(status_code=400, detail=error_detail)

    stripe_account = await get_stripe_account(current_org)

    query = select(Membership).where(
        Membership.id == id_membership, Membership.id_org == current_org
    )
    data = await db.session.execute(query)
    old_membership = data.unique().scalar_one()

    try:
        await stripe.Price.modify(
            old_membership.stripe_price_id,
            active=False,
            stripe_account=stripe_account,
        )
    except stripe.error.InvalidRequestError:
        pass

    price = await stripe.Price.create(
        unit_amount=int(membership.amount * 100),
        currency=membership.currency.value,
        recurring={
            "interval": membership.billing_period.value,
            "interval_count": membership.number_of_payments
            if membership.number_of_payments > 0
            else None,
        },
        product=old_membership.stripe_product_id,
        stripe_account=stripe_account,
    )

    product = None

    try:
        product = await stripe.Product.modify(
            old_membership.stripe_product_id,
            name=membership.name,
            description=membership.description,
            stripe_account=stripe_account,
        )
    except stripe.error.InvalidRequestError:
        product = await stripe.Product.create(
            name=membership.name,
            description=membership.description,
            metadata={"id_org": str(current_org)},
            stripe_account=stripe_account,
        )

    new_membership = Membership(
        name=membership.name,
        description=membership.description,
        currency=membership.currency,
        amount=membership.amount,
        active=membership.active,
        billing_type=membership.billing_type,
        billing_period=membership.billing_period,
        number_of_payments=membership.number_of_payments,
        membership_type=membership.membership_type,
        value=membership.value,
        stripe_product_id=product.id,
        stripe_price_id=price.id,
        id_org=current_org,
    )

    query = (
        update(Membership)
        .where(Membership.id == id_membership, Membership.id_org == current_org)
        .values(new_membership.dict())
        .returning(Membership)
    )

    data = await db.session.execute(query)
    await db.session.commit()

    if membership.locations:
        query = delete(LinkMembershipLocation).where(
            LinkMembershipLocation.id_membership == id_membership
        )

        await db.session.execute(query)
        await db.session.commit()

        query = insert(LinkMembershipLocation).values(
            [
                {"id_membership": id_membership, "id_location": location}
                for location in membership.locations
            ]
        )

        await db.session.execute(query)
        await db.session.commit()

    if len(membership.locations) == 0:
        query = delete(LinkMembershipLocation).where(
            LinkMembershipLocation.id_membership == id_membership
        )

        await db.session.execute(query)
        await db.session.commit()

    return data.unique().all().pop()


async def partner_switch_membership(
    id_membership: UUID, current_org: UUID
) -> Membership.Read:
    query = select(Membership).where(
        Membership.id == id_membership, Membership.id_org == current_org
    )

    data = await db.session.execute(query)
    membership = data.unique().scalar_one()

    query = (
        update(Membership)
        .where(Membership.id_org == current_org, Membership.id == id_membership)
        .values(active=True if membership.active is False else False)
        .returning(Membership)
    )

    data = await db.session.execute(query)
    await db.session.commit()

    updated_membership = data.unique().all().pop()

    return updated_membership

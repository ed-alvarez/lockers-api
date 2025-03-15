from typing import Optional
from uuid import UUID

from auth.cognito import get_current_email, get_current_org, get_permission
from fastapi import APIRouter, Depends, HTTPException


from ..member.model import RoleType
from . import controller
from .model import DetailModel, StripeAccount, StripeCountry

router = APIRouter(tags=["financial"])


@router.get("/partner/stripe/account", response_model=StripeAccount)
async def get_stripe_account(
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission not in [RoleType.admin, RoleType.member]:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin or member"
        )

    account_info = await controller.get_stripe_account(current_org)
    # Logging result
    # Logging at the end

    return account_info


@router.post("/partner/stripe")
async def create_stripe_link(
    current_email: str = Depends(get_current_email),
    current_org: UUID = Depends(get_current_org),
    country: Optional[StripeCountry] = StripeCountry.US,
    permission: RoleType = Depends(get_permission),
):
    """
    Create a Stripe account link for the current user, these are the supported countries:

    | Code | Country | Currency |
    | ---- | ------- | -------- |
    | AT   | Austria | Euro     |
    | BE   | Belgium | Euro     |
    | FI   | Finland | Euro     |
    | FR   | France  | Euro     |
    | DE   | Germany | Euro     |
    | IE   | Ireland | Euro     |
    | IT   | Italy   | Euro     |
    | NL   | Netherlands | Euro |
    | PT   | Portugal | Euro    |
    | ES   | Spain   | Euro     |
    | GB   | United Kingdom / Great Britain | GBP |
    | AU   | Australia | Dollar   |
    | CA   | Canada   | Dollar   |
    | US   | United States | Dollar |

    if no country is provided, the default is US

    """

    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    stripe_link = await controller.create_stripe_link(
        current_org, current_email, country
    )
    # Logging result

    return stripe_link


@router.delete("/partner/stripe", response_model=DetailModel)
async def delete_stripe_account(
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    delete_result = await controller.delete_stripe_account(current_org)
    # Logging result
    # Logging at the end

    return delete_result

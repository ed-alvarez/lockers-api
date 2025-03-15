from uuid import UUID

from auth.cognito import get_current_org, get_permission
from fastapi import APIRouter, Depends, HTTPException


from ..member.model import RoleType
from . import controller
from .model import EventChange, Webhook

router = APIRouter(tags=["webhook"])


@router.get("/partner/webhook", response_model=Webhook.Read)
async def get_webhook(
    current_org: UUID = Depends(get_current_org),
):
    """
    A header called *Koloni-Signature* is sent with each webhook request.
    This header contains a SHA256 of the organization's webhook signature key and the body of the request, converted to a HEX string.

    To validate each request, you can follow these steps:

    1. Get the secret (signature_key) from your organization's webhook
    3. Get the body of the request
    4. Do a SHA256 of the secret (signature_key) and the body (encoding: UTF-8), respecting the order (secret + body)
    5. Convert the result of step 4 into a HEX string

    If the result is equal to the *Koloni-Signature* header, then the request is valid.

    * The webhook object:
    ```json
    {
        "id_event": "3c138c9e-8340-4e6e-b4ce-7094c83fe7fd",
        "id_org": "fec27db7-466a-48a1-956b-cbfd7c9eb9d9",
        "event_status": "awating_payment_confirmation" | "awaiting_service_pickup" | "awaiting_service_dropoff" | "awaiting_user_pickup" | "finished" | "canceled" | "in_progress" | "refund" | "test",
        "event_obj": {
            "id": "3c138c9e-8340-4e6e-b4ce-7094c83fe7fd",
            "invoice_id": "DMR000006",
            "created_at": "2023-04-26T19:13:56.437255+00:00",

        }
    }
    ```
    * *event_obj* shortened for brevity, see [events] for full object
    """

    # Logging at the start
    # Logging input objects

    # Attempt to get the webhook for the current organization
    webhook = await controller.get_webhook(current_org)

    # Logging at the end
    return webhook


@router.post("/partner/webhook", response_model=Webhook.Read)
async def create_webhook(
    webhook: Webhook.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    # Check permission
    if permission != RoleType.admin:
        # Logging of WARN
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Create webhook
    created_webhook = await controller.create_webhook(webhook, current_org)
    # Logging result
    # Logging at the end
    return created_webhook


@router.put("/partner/webhook", response_model=Webhook.Read)
async def update_webhook(
    webhook: Webhook.Write,
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start

    # Check permission
    if permission != RoleType.admin:
        # Logging warning
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Update webhook
    updated_webhook = await controller.update_webhook(webhook, current_org)
    # Logging result
    # Logging at the end
    return updated_webhook


@router.delete("/partner/webhook", response_model=Webhook.Read)
async def delete_webhook(
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    # Check permission
    if permission != RoleType.admin:
        # Logging warning
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Delete webhook
    deleted_webhook = await controller.delete_webhook(current_org)
    # Logging result
    # Logging at the end
    return deleted_webhook


@router.post("/partner/webhook/test", response_model=bool)
async def test_webhook(
    current_org: UUID = Depends(get_current_org),
    permission: RoleType = Depends(get_permission),
):
    # Logging at the start
    # Logging input objects

    # Check permission
    if permission != RoleType.admin:
        # Logging warning
        raise HTTPException(
            status_code=403, detail="Not enough permissions, must be admin"
        )

    # Send dummy payload
    success = await controller.send_payload(
        current_org,
        EventChange(
            id_event=UUID("00000000-0000-0000-0000-000000000000"),
            id_org=current_org,
            event_status="test",
            event_obj=None,
        ),
    )
    # Logging result
    # Logging at the end
    return success

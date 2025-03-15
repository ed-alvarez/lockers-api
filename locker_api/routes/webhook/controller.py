import hashlib
import secrets
from uuid import UUID

import httpx
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import delete, insert, select, update


from ..event.model import Event
from .model import EventChange, Webhook, WebhookStatus


async def get_webhook(
    id_org: UUID,
):
    query = select(Webhook).where(Webhook.id_org == id_org)

    response = await db.session.execute(query)

    webhook = response.scalar_one()

    return webhook


async def send_payload(
    id_org: UUID,
    payload: EventChange,
) -> bool:
    if not id_org:
        return False

    try:
        webhook: Webhook.Read = await get_webhook(id_org)
    except Exception:
        return False

    query = select(Event).where(
        Event.id == payload.id_event,
        Event.id_org == id_org,
    )
    response = await db.session.execute(query)

    event: Event = response.unique().scalar_one_or_none()
    if event:
        payload.event_obj = event.Read.parse_obj(event)

    secret = webhook.signature_key
    payload_json = payload.json(exclude_none=True)

    signature = hashlib.sha256(secret.encode() + payload_json.encode()).hexdigest()

    headers = {
        "Koloni-Signature": signature,
        "Content-Type": "application/json",
    }

    query = update(Webhook).where(Webhook.id_org == id_org)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                webhook.url, data=payload_json, headers=headers
            )
        except httpx.ConnectError:
            return False

        match response.status_code:
            case 200:
                query = query.values(status=WebhookStatus.ok)
            case 500:
                query = query.values(status=WebhookStatus.error)
            case 404:
                query = query.values(status=WebhookStatus.error)
            case _:
                query = query.values(status=WebhookStatus.inactive)

    await db.session.execute(query)
    await db.session.commit()

    return True


async def create_webhook(
    webhook: Webhook.Write,
    id_org: UUID,
):
    query = select(Webhook).where(
        Webhook.id_org == id_org,
    )

    response = await db.session.execute(query)

    if len(response.scalars().all()) > 0:
        raise HTTPException(
            status_code=400,
            detail="Only one webhook per organization is allowed",
        )

    webhook = Webhook(
        **webhook.dict(),
        id_org=id_org,
        status=WebhookStatus.inactive,
        signature_key=secrets.token_hex(32),
    )

    query = (
        insert(Webhook)
        .values(
            webhook.dict(),
        )
        .returning(Webhook)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.all().pop()


async def update_webhook(
    webhook: Webhook.Write,
    id_org: UUID,
):
    query = (
        update(Webhook)
        .where(
            Webhook.id_org == id_org,
        )
        .values(url=webhook.url, status=WebhookStatus.inactive)
        .returning(Webhook)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        updated_webhook = response.all().pop()

        return updated_webhook
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail="Webhook not found",
        )


async def delete_webhook(
    id_org: UUID,
):
    query = (
        delete(Webhook)
        .where(
            Webhook.id_org == id_org,
        )
        .returning(Webhook)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    try:
        deleted_webhook = response.all().pop()

        return deleted_webhook
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail="Webhook not found",
        )

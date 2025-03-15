import base64
import hmac
import random
import secrets
from uuid import UUID

from config import get_settings
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import and_, delete, insert, select


from .model import ApiKey


async def create_api_key(current_org: UUID) -> ApiKey.Read:
    # Generate a random string to sign, from 32 to 64 characters
    rand_str = secrets.token_hex(random.randint(32, 64))

    # Sign the random string with the JWT secret key
    signed_str = hmac.new(
        get_settings().jwt_secret_key.encode("utf-8"),
        rand_str.encode("utf-8"),
        "sha256",
    ).hexdigest()

    # Encode the signed string in base64, and remove the padding
    key = base64.b64encode(signed_str.encode("utf-8")).decode("utf-8").replace("=", "")

    # Create the API key
    api_key = ApiKey(active=True, key=key, id_org=current_org)

    query = insert(ApiKey).values(api_key.dict()).returning(ApiKey)

    response = await db.session.execute(query)
    await db.session.commit()  # raises IntegrityError

    created_api_key = response.fetchone()
    created_api_key = ApiKey.Read(**created_api_key)
    return created_api_key


async def get_api_keys(current_org: UUID) -> list[ApiKey.Read]:
    """
    Controller function to fetch all API keys for a given organization.
    """
    query = select(ApiKey).where(ApiKey.id_org == current_org)

    response = await db.session.execute(query)
    api_keys = response.scalars().all()

    return api_keys


async def delete_api_key(id_api_key: UUID, current_org: UUID) -> ApiKey.Read:
    """Controller function to delete an API key."""
    # Prepare and execute the deletion query

    query = (
        delete(ApiKey)
        .where(
            and_(
                ApiKey.id_org == current_org,
                ApiKey.id == id_api_key,
            )
        )
        .returning(ApiKey)
    )
    response = await db.session.execute(query)
    await db.session.commit()

    # Check if the API key was actually deleted
    deleted_api_key = response.fetchone()

    if deleted_api_key is None:
        # Raising HTTPException here is fine since it's a specific case that the controller can handle
        raise HTTPException(
            status_code=404,
            detail="API key not found.",
        )

    deleted_api_key = ApiKey.Read(**deleted_api_key)

    return deleted_api_key


async def delete_api_keys(id_api_keys: list[UUID], id_org: UUID):
    query = (
        delete(ApiKey)
        .where(
            and_(
                ApiKey.id_org == id_org,
                ApiKey.id.in_(id_api_keys),
            )
        )
        .returning(ApiKey)
    )

    result = await db.session.execute(query)
    await db.session.commit()

    # Check if the API keys were actually deleted by looking at result.rowcount or result.fetchall()
    deleted_keys_count = result.rowcount
    if deleted_keys_count == 0:
        raise HTTPException(status_code=404, detail="No API keys found for deletion.")

    return {"detail": f"Deleted {deleted_keys_count} API keys."}

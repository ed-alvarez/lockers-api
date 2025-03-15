from datetime import datetime, timedelta
from uuid import UUID

from config import get_settings
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pydantic import ValidationError
from routes.user.controller import get_user

auth = HTTPBearer()


async def get_current_user_id_org(
    credentials: HTTPAuthorizationCredentials = Depends(auth),
) -> UUID:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret_key,
            algorithms=["HS256"],
            audience="mobile",
            issuer="mobile_api",
        )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
    user = await get_user(payload["sub"])
    if not user.active:
        raise HTTPException(status_code=403, detail="User inactive")

    return payload["id_org"]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth),
) -> UUID:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret_key,
            algorithms=["HS256"],
            audience="mobile",
            issuer="mobile_api",
        )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
    user = await get_user(payload["sub"])
    if not user.active:
        raise HTTPException(status_code=403, detail="User inactive")

    return payload["sub"]


def create_access_token(id_user: UUID, id_org: UUID) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=get_settings().access_token_expire_minutes
    )
    to_encode = {
        "aud": "mobile",
        "iss": "mobile_api",
        "exp": expire,
        "sub": str(id_user),
        "type": "access",
        "id_org": str(id_org),
    }
    encoded_jwt = jwt.encode(
        to_encode, get_settings().jwt_secret_key, algorithm="HS256"
    )
    return encoded_jwt

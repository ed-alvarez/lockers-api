from typing import List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.security.http import HTTPBasic
from routes.member.controller import (
    get_member_locations,
    get_role,
    get_roles_permissions,
    get_user_roles,
)
from routes.member.model import PermissionType, RoleType
from routes.organization import controller

from .models import JWTAuthorizationCredentials, JWTBearer

auth = JWTBearer()
key_auth = APIKeyHeader(name="X-API-KEY", auto_error=False)
pin_code = HTTPBasic(auto_error=False)


def get_current_user(
    credentials: JWTAuthorizationCredentials = Depends(auth),
) -> str:
    if not credentials:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated, or attempted to use API key",
        )
    try:
        return credentials.claims["cognito:username"]
    except KeyError:
        raise HTTPException(status_code=403, detail="Username missing")


def get_current_username(
    credentials: JWTAuthorizationCredentials = Depends(auth),
) -> Optional[str]:
    if not credentials:
        return None
    try:
        return credentials.claims["name"]
    except KeyError:
        return None


async def get_current_org(
    credentials: JWTAuthorizationCredentials = Depends(auth),
    key: str = Depends(key_auth),
    pin_code: HTTPBasic = Depends(pin_code),
):
    if pin_code and pin_code.username and pin_code.password:
        return await controller.get_org_id_by_pin_code(
            pin_code.username, pin_code.password
        )

    if not (key or credentials):
        raise HTTPException(status_code=403, detail="Not authenticated")

    if credentials:
        try:
            user_pool = credentials.claims["iss"].split("/")[-1]
            return await controller.get_org_id_by_user_pool(user_pool)
        except KeyError:
            raise HTTPException(status_code=403, detail="User pool id missing")
    else:
        return await controller.get_org_id_by_api_key(key)


async def get_org_applications(
    credentials: JWTAuthorizationCredentials = Depends(auth),
    key: str = Depends(key_auth),
    pin_code: str = Depends(pin_code),
):
    if pin_code and pin_code.username and pin_code.password:
        return await controller.get_org_id_by_pin_code(
            pin_code.username, pin_code.password
        )

    if not (key or credentials):
        raise HTTPException(status_code=403, detail="Not authenticated")

    org = None

    if credentials:
        try:
            user_pool = credentials.claims["iss"].split("/")[-1]
            org = await controller.get_org_id_by_user_pool(user_pool)
        except KeyError:
            raise HTTPException(status_code=403, detail="User pool id missing")
    else:
        org = await controller.get_org_id_by_api_key(key)

    organization = await controller.get_org(org)

    return [
        "rental" if organization.rental_mode else None,
        "storage" if organization.storage_mode else None,
        "delivery" if organization.delivery_mode else None,
        "service" if organization.service_mode else None,
    ]


async def get_current_user_pool(
    credentials: JWTAuthorizationCredentials = Depends(auth),
    key: str = Depends(key_auth),
    pin_code: str = Depends(pin_code),
):
    if pin_code and pin_code.username and pin_code.password:
        return await controller.get_org_id_by_pin_code(
            pin_code.username, pin_code.password
        )

    if not (key or credentials):
        raise HTTPException(status_code=403, detail="Not authenticated")
    if credentials:
        try:
            return credentials.claims["iss"].split("/")[-1]
        except KeyError:
            raise HTTPException(status_code=403, detail="User pool id missing")
    else:
        return await controller.get_user_pool_by_api_key(key)


def get_current_email(
    credentials: JWTAuthorizationCredentials = Depends(auth),
):
    try:
        return credentials.claims["email"]
    except KeyError:
        raise HTTPException(status_code=403, detail="Email missing")


async def get_permission(
    credentials: JWTAuthorizationCredentials = Depends(auth),
    key: str = Depends(key_auth),
    pin_code: str = Depends(pin_code),
) -> RoleType:
    if pin_code and pin_code.username and pin_code.password:
        return await controller.get_org_id_by_pin_code(
            pin_code.username,
            pin_code.password,
            with_le_role=True,
        )

    if not (key or credentials):
        raise HTTPException(status_code=403, detail="Not authenticated")

    if credentials:
        try:
            user_id = credentials.claims["cognito:username"]
            user_pool = credentials.claims["iss"].split("/")[-1]
            user_role = await get_role(user_id, user_pool)
            return user_role
        except KeyError:
            raise HTTPException(status_code=403, detail="JWT malformed")

    return RoleType.admin


def permission_dependency_factory(required_permission: PermissionType):
    async def get_permission_new(
        credentials: JWTAuthorizationCredentials = Depends(auth),
        key: str = Depends(key_auth),
        pin_code: str = Depends(pin_code),
    ) -> List[PermissionType]:
        if pin_code and pin_code.username and pin_code.password:
            return await controller.get_org_id_by_pin_code(
                pin_code.username, pin_code.password
            )

        if not (key or credentials):
            raise HTTPException(status_code=403, detail="Not authenticated")

        try:
            user_id = credentials.claims["cognito:username"]
            roles = await get_user_roles(user_id)
            permissions = await get_roles_permissions(roles)

            if required_permission not in permissions:
                raise HTTPException(status_code=403, detail="Not enough permissions")

            return permissions
        except KeyError:
            raise HTTPException(status_code=403, detail="JWT malformed")

    return get_permission_new


async def get_locations(
    credentials: JWTAuthorizationCredentials = Depends(auth),
    key: str = Depends(key_auth),
    pin_code: str = Depends(pin_code),
) -> Optional[List[UUID]]:
    # If login by pin_code, return None as in conditional:
    # "if user_role == RoleType.operator" since this is for Kiosk
    # access only:
    if pin_code and pin_code.username and pin_code.password:
        return None

    if not (key or credentials):
        raise HTTPException(status_code=403, detail="Not authenticated")

    if credentials:
        try:
            user_id = credentials.claims["cognito:username"]
            user_pool = credentials.claims["iss"].split("/")[-1]
            user_role = await get_role(user_id, user_pool)
            if user_role == RoleType.operator:
                return await get_member_locations(user_id)
            return None
        except KeyError:
            raise HTTPException(status_code=403, detail="JWT malformed")

    return None


async def get_api_key_from_ws(request: Request):
    return request.query_params.get("api_key")


async def get_current_org_for_ws(
    api_key: str = Depends(get_api_key_from_ws),
    credentials: JWTAuthorizationCredentials = Depends(auth),
):
    if api_key:
        return await controller.get_org_id_by_api_key(api_key)
    elif credentials:
        try:
            user_pool = credentials.claims["iss"].split("/")[-1]
            return await controller.get_org_id_by_user_pool(user_pool)
        except KeyError:
            raise HTTPException(status_code=403, detail="User pool id missing")
    else:
        raise HTTPException(status_code=403, detail="Not authenticated")

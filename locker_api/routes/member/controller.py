from math import ceil
from typing import List, Optional
from uuid import UUID

import aioboto3
from config import get_settings
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import delete, insert, select, update


from ..organization.model import Org
from .model import (
    CognitoMembersRoleLink,
    LinkMemberLocation,
    Member,
    MemberUpdate,
    MemberPatch,
    PaginatedMembers,
    PermissionType,
    Role,
    RolePermission,
    RoleType,
)


async def get_self(user_pool_id: str, user_id: str):
    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        try:
            response = await client.admin_get_user(
                UserPoolId=user_pool_id, Username=user_id
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return Member(
            user_id=user_id,
            name=await get_attribute(response["UserAttributes"], "name"),
            email=await get_attribute(response["UserAttributes"], "email"),
            first_name=await get_attribute(response["UserAttributes"], "given_name"),
            last_name=await get_attribute(response["UserAttributes"], "family_name"),
            phone_number=await get_attribute(
                response["UserAttributes"], "phone_number"
            ),
            enabled=response["Enabled"],
            user_status=response["UserStatus"],
            role=await get_role(user_id, user_pool_id),
            id_locations=await get_member_locations(user_id),
            created_at=response["UserCreateDate"],
        )


async def get_users(
    page: int,
    size: int,
    user_id: Optional[str],
    search: Optional[str],
    user_pool_id: str,
):
    if user_id:
        return await get_user(user_pool_id, user_id)

    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        try:
            response = await client.list_users(UserPoolId=user_pool_id)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        items = [
            Member(
                user_id=user["Username"],
                name=await get_attribute(user["Attributes"], "name"),
                email=await get_attribute(user["Attributes"], "email"),
                first_name=await get_attribute(user["Attributes"], "given_name"),
                last_name=await get_attribute(user["Attributes"], "family_name"),
                phone_number=await get_attribute(user["Attributes"], "phone_number"),
                enabled=user["Enabled"],
                user_status=user["UserStatus"],
                role=await get_role(user["Username"], user_pool_id),
                pin_code=await get_pin_code(user["Username"], user_pool_id),
                id_locations=await get_member_locations(user["Username"]),
                created_at=user["UserCreateDate"],
            )
            for user in response["Users"]
        ]

        if search:
            items = [
                item
                for item in items
                if search.lower() in str(item.name).lower()
                or search in item.email
                or search.lower() in str(item.first_name).lower()
                or search.lower() in str(item.last_name).lower()
            ]

        page = items[(page - 1) * size : page * size]

        total = len(items)
        pages = ceil(total / size)

        return PaginatedMembers(
            items=page,
            total=total,
            pages=pages,
        )


async def get_user(user_pool_id: str, user_id: str):
    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        try:
            response = await client.admin_get_user(
                UserPoolId=user_pool_id, Username=user_id
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return Member(
            user_id=response["Username"],
            name=await get_attribute(response["UserAttributes"], "name"),
            email=await get_attribute(response["UserAttributes"], "email"),
            first_name=await get_attribute(response["UserAttributes"], "given_name"),
            last_name=await get_attribute(response["UserAttributes"], "family_name"),
            phone_number=await get_attribute(
                response["UserAttributes"], "phone_number"
            ),
            enabled=response["Enabled"],
            user_status=response["UserStatus"],
            role=await get_role(response["Username"], user_pool_id),
            id_locations=await get_member_locations(response["Username"]),
            created_at=response["UserCreateDate"],
        )


async def get_email(response: list):
    for attr in response:
        if attr["Name"] == "email":
            return attr["Value"]


async def get_attribute(response: list, name: str):
    for attr in response:
        if attr["Name"] == name:
            return attr["Value"]


async def get_role(user_id: str, user_pool: str) -> Optional[RoleType]:
    query = select(Role.role).where(Role.user_id == user_id)

    response = await db.session.execute(query)

    data = response.scalars().first()

    if data:
        return data

    query = select(Org.id).where(Org.user_pool == user_pool)

    response = await db.session.execute(query)

    org_id = response.scalar_one_or_none()

    if not org_id:
        return None

    query = (
        insert(Role)
        .values(user_id=user_id, role=RoleType.admin, id_org=org_id)
        .returning(Role.role)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.scalar_one()


async def get_pin_code(user_id: str, user_pool: str) -> Optional[RoleType]:
    query = select(Role.pin_code).where(Role.user_id == user_id)

    response = await db.session.execute(query)

    data = response.scalars().first()

    if data:
        return data

    query = select(Org.id).where(Org.user_pool == user_pool)

    response = await db.session.execute(query)

    org_id = response.scalar_one_or_none()

    if not org_id:
        return None

    query = (
        insert(Role)
        .values(user_id=user_id, role=RoleType.admin, pin_code=None, id_org=org_id)
        .returning(Role.pin_code)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    return response.scalar_one()


async def get_user_roles(user_id: UUID) -> List[UUID]:
    query = select(CognitoMembersRoleLink.role_id).where(
        CognitoMembersRoleLink.user_id == user_id
    )
    result = await db.session.execute(query)
    role_ids = result.scalars().all()
    return role_ids


async def get_roles_permissions(role_ids: List[UUID]) -> List[PermissionType]:
    permissions = []
    for role_id in role_ids:
        query = select(RolePermission.permission).where(
            RolePermission.role_id == role_id
        )
        result = await db.session.execute(query)
        permissions.extend(result.scalars().all())
    return list(set(permissions))  # Removing duplicates


async def get_member_locations(user_id: str) -> List[UUID]:
    query = select(LinkMemberLocation.id_location).where(
        LinkMemberLocation.user_id == user_id
    )

    response = await db.session.execute(query)

    return response.scalars().all()


async def create_user(
    user_pool_id: str, id_org: UUID, email: str, member: MemberUpdate
):
    if member.pin_code:
        await check_pincode_unique(member.pin_code, id_org)

    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        user_attr = [
            {"Name": "email", "Value": email},
            {"Name": "name", "Value": member.name},
            {"Name": "given_name", "Value": member.first_name},
            {
                "Name": "family_name",
                "Value": member.last_name if member.last_name else "",
            },
            {"Name": "email_verified", "Value": "true"},
        ]

        if member.phone_number:
            user_attr.append(
                {"Name": "phone_number", "Value": str(member.phone_number)},
            )

        response = await client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=user_attr,
        )

        query = (
            insert(Role)
            .values(
                user_id=response["User"]["Username"],
                role=member.role,
                pin_code=member.pin_code,
                id_org=id_org,
            )
            .returning(Role)
        )

        res = await db.session.execute(query)
        await db.session.commit()
        data = res.all().pop()

        if member.id_locations:
            for id_location in member.id_locations:
                query = insert(LinkMemberLocation).values(
                    user_id=response["User"]["Username"],
                    id_location=id_location,
                )
                await db.session.execute(query)
                await db.session.commit()

        return Member(
            user_id=response["User"]["Username"],
            name=await get_attribute(response["User"]["Attributes"], "name"),
            email=await get_attribute(response["User"]["Attributes"], "email"),
            first_name=await get_attribute(
                response["User"]["Attributes"], "given_name"
            ),
            last_name=await get_attribute(
                response["User"]["Attributes"], "family_name"
            ),
            enabled=response["User"]["Enabled"],
            phone_number=await get_attribute(
                response["User"]["Attributes"], "phone_number"
            ),
            user_status=response["User"]["UserStatus"],
            role=data.role,
            pin_code=data.pin_code,
            id_locations=await get_member_locations(response["User"]["Username"]),
            created_at=response["User"]["UserCreateDate"],
        )


async def update_user(
    user_pool_id: str, id_org: UUID, user_id: str, member: MemberUpdate
):
    if member.pin_code:
        await check_pincode_unique(member.pin_code, id_org, user_id)
    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        user_attr = [
            {"Name": "name", "Value": member.name},
            {"Name": "given_name", "Value": member.first_name},
            {
                "Name": "family_name",
                "Value": member.last_name if member.last_name else "",
            },
            {"Name": "email_verified", "Value": "true"},
        ]

        if member.phone_number:
            user_attr.append(
                {"Name": "phone_number", "Value": str(member.phone_number)},
            )

        await client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=user_id,
            UserAttributes=user_attr,
        )

        query = (
            update(Role)
            .where(
                Role.user_id == user_id,
                Role.id_org == id_org,
            )
            .values(role=member.role, pin_code=member.pin_code)
            .returning(Role)
        )

        if member.id_locations:
            del_query = delete(LinkMemberLocation).where(
                LinkMemberLocation.user_id == user_id
            )
            await db.session.execute(del_query)
            await db.session.commit()

            for id_location in member.id_locations:
                ins_query = insert(LinkMemberLocation).values(
                    user_id=user_id,
                    id_location=id_location,
                )
                await db.session.execute(ins_query)
                await db.session.commit()

        else:
            del_query = delete(LinkMemberLocation).where(
                LinkMemberLocation.user_id == user_id
            )
            await db.session.execute(del_query)
            await db.session.commit()

        response = await db.session.execute(query)
        await db.session.commit()

        data = response.all()

        if len(data) == 0:
            query = (
                insert(Role)
                .values(
                    user_id=user_id,
                    role=member.role,
                    pin_code=member.pin_code,
                    id_org=id_org,
                )
                .returning(Role)
            )

            response = await db.session.execute(query)
            await db.session.commit()

        return {"detail": "User updated"}


async def patch_user(
    user_pool_id: str, id_org: UUID, user_id: str, member: MemberPatch
):
    selected_member = await get_user(user_pool_id, user_id)

    if member.name:
        selected_member.name = member.name
    if member.first_name:
        selected_member.first_name = member.first_name
    if member.last_name:
        selected_member.last_name = member.last_name
    if member.role:
        selected_member.role = member.role
    if member.id_locations:
        selected_member.id_locations = member.id_locations
    if member.phone_number:
        selected_member.phone_number = member.phone_number
    if member.pin_code:
        await check_pincode_unique(member.pin_code, id_org, user_id)
        selected_member.pin_code = member.pin_code

    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        user_attr = [
            {"Name": "name", "Value": selected_member.name},
            {"Name": "given_name", "Value": selected_member.first_name},
            {
                "Name": "family_name",
                "Value": selected_member.last_name if selected_member.last_name else "",
            },
        ]

        if selected_member.phone_number:
            user_attr.append(
                {"Name": "phone_number", "Value": str(selected_member.phone_number)},
            )

        await client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=user_id,
            UserAttributes=user_attr,
        )

        query = (
            update(Role)
            .where(
                Role.user_id == user_id,
                Role.id_org == id_org,
            )
            .values(role=selected_member.role, pin_code=selected_member.pin_code)
            .returning(Role)
        )

        if member.id_locations:
            del_query = delete(LinkMemberLocation).where(
                LinkMemberLocation.user_id == user_id
            )
            await db.session.execute(del_query)
            await db.session.commit()

            for id_location in member.id_locations:
                ins_query = insert(LinkMemberLocation).values(
                    user_id=user_id,
                    id_location=id_location,
                )
                await db.session.execute(ins_query)
                await db.session.commit()

        else:
            del_query = delete(LinkMemberLocation).where(
                LinkMemberLocation.user_id == user_id
            )
            await db.session.execute(del_query)
            await db.session.commit()

        response = await db.session.execute(query)
        await db.session.commit()

        data = response.all()

        if len(data) == 0:
            query = (
                insert(Role)
                .values(
                    user_id=user_id,
                    role=selected_member.role,
                    pin_code=selected_member.pin_code,
                    id_org=id_org,
                )
                .returning(Role)
            )

            response = await db.session.execute(query)
            await db.session.commit()

        return {"detail": "User patched"}


async def patch_users(
    user_pool_id: str, id_org: UUID, user_ids: List[UUID], member: MemberPatch
):
    for user_id in user_ids:
        await patch_user(user_pool_id, id_org, str(user_id), member)

    return {"detail": "Users patched"}


async def create_members_csv(id_org: UUID, member: Member):
    try:
        query = select(Org.user_pool).where(Org.id == id_org)
        response = await db.session.execute(query)
        user_pool = response.scalar_one_or_none()
        if not user_pool:
            error_detail = f"No user pool found for organization ID: {id_org}"

            return error_detail

        await create_user(user_pool, id_org, member.email, member)
    except HTTPException as e:
        return e.detail

    return True


async def update_members_csv(id_org: UUID, member: Member, id_user: str):
    try:
        query = select(Org.user_pool).where(Org.id == id_org)
        response = await db.session.execute(query)
        user_pool = response.scalar_one_or_none()
        await update_user(user_pool, id_org, str(id_user), member)
    except HTTPException as e:
        return e.detail
    return True


async def delete_user(user_pool_id: str, user_id: str):
    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        try:
            await client.admin_delete_user(UserPoolId=user_pool_id, Username=user_id)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        query = delete(Role).where(Role.user_id == user_id)
        await db.session.execute(query)
        await db.session.commit()

        return {"detail": "User deleted"}


async def delete_users(user_pool_id: str, user_ids: List[str]):
    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        for user_id in user_ids:
            try:
                await client.admin_delete_user(
                    UserPoolId=user_pool_id, Username=user_id
                )

            except Exception:
                # Continue with the next user instead of stopping the whole process
                continue

            query = delete(Role).where(Role.user_id == user_id)
            await db.session.execute(query)
            await db.session.commit()

        return {"detail": "Users deleted"}


async def verify_email(user_pool_id: str, user_id: str):
    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        try:
            await client.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=user_id,
                UserAttributes=[{"Name": "email_verified", "Value": "True"}],
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"detail": "Email verified"}


async def switch_member_status(user_pool_id: str, user_id: str, enabled: bool):
    session = aioboto3.Session()
    async with session.client(
        "cognito-idp",
        aws_access_key_id=get_settings().aws_access_key_id,
        aws_secret_access_key=get_settings().aws_secret_access_key,
        region_name=get_settings().aws_region,
    ) as client:
        match enabled:
            case True:
                await client.admin_enable_user(
                    UserPoolId=user_pool_id,
                    Username=user_id,
                )
            case False:
                await client.admin_disable_user(
                    UserPoolId=user_pool_id,
                    Username=user_id,
                )

        return {"detail": "User activated" if enabled else "User deactivated"}


async def check_pincode_unique(
    pin_code: str, id_org: UUID, user_id: Optional[str] = None
):
    query = select(Role).where(Role.id_org == id_org, Role.pin_code == pin_code)

    if user_id:
        query = query.where(Role.user_id != user_id)

    response = await db.session.execute(query)

    data = response.scalars().all()

    if len(data) > 0:
        raise HTTPException(status_code=409, detail="Pin code is already in use")

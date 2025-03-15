from typing import List
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from sqlalchemy import delete, insert, select, update


from ..member.model import CognitoMembersRoleLink, PermissionType, Role, RolePermission
from .model import RoleCreate, RolePermissionAssignment, RoleUpdate, UserRoleAssignment


# Define default permissions for each role type
default_permissions = {
    "admin": [
        PermissionType.create,
        PermissionType.read,
        PermissionType.update,
        PermissionType.delete,
    ],
    "member": [PermissionType.create, PermissionType.read, PermissionType.update],
    "operator": [PermissionType.create, PermissionType.read, PermissionType.update],
    "viewer": [PermissionType.read],
}


async def create_role(role_data: RoleCreate) -> Role:
    query = insert(Role).values(role_data.dict()).returning(Role)
    try:
        response = await db.session.execute(query)
        await db.session.commit()
        created_role = response.fetchone()

        # Assign default permissions to the newly created role
        for perm in default_permissions.get(role_data.role.value, []):
            perm_query = insert(RolePermission).values(
                {"role_id": created_role.id, "permission": perm}
            )
            await db.session.execute(perm_query)

        await db.session.commit()

        return Role(**created_role)

    except Exception:
        await db.session.rollback()
        raise


async def get_roles(current_org: UUID) -> List[Role]:
    query = select(Role).where(Role.id_org == current_org)
    response = await db.session.execute(query)
    role_records = response.scalars().all()

    return role_records


async def update_role(role_id: UUID, role_data: RoleUpdate, current_org: UUID) -> Role:
    query = (
        update(Role)
        .where(
            Role.id == role_id, Role.id_org == current_org
        )  # Assuming roles are scoped to organizations
        .values(role_data.dict())
        .returning(Role)
    )

    response = await db.session.execute(query)
    await db.session.commit()

    updated_role = response.fetchone()

    if updated_role:
        return Role(**updated_role)
    else:
        raise HTTPException(status_code=404, detail=f"Role with ID {role_id} not found")


async def delete_role(role_id: UUID, current_org: UUID) -> bool:
    query = delete(Role).where(
        Role.id == role_id, Role.id_org == current_org
    )  # Assuming roles are scoped to organizations
    response = await db.session.execute(query)
    await db.session.commit()

    return response.rowcount > 0  # True if a row was deleted, False otherwise


async def assign_role_to_user(
    user_role_data: UserRoleAssignment,
) -> CognitoMembersRoleLink:
    query = insert(CognitoMembersRoleLink).values(user_role_data.dict())

    try:
        await db.session.execute(query)
        await db.session.commit()

        # Perform a query to retrieve the inserted data
        query = select(CognitoMembersRoleLink).where(
            CognitoMembersRoleLink.user_id == user_role_data.user_id,
            CognitoMembersRoleLink.role_id == user_role_data.role_id,
        )
        response = await db.session.execute(query)

        assigned_role_link = response.scalar_one()

        return assigned_role_link

    except Exception:
        await (
            db.session.rollback()
        )  # Rollback the transaction before propagating the exception
        raise  # This will be caught by the global exception handler


async def assign_permission_to_role(
    role_perm_data: RolePermissionAssignment,
) -> RolePermission:
    query = insert(RolePermission).values(role_perm_data.dict())

    try:
        await db.session.execute(query)
        await db.session.commit()

        # Perform a query to retrieve the inserted data
        query = select(RolePermission).where(
            RolePermission.role_id == role_perm_data.role_id,
            RolePermission.permission == role_perm_data.permission,
        )
        response = await db.session.execute(query)

        assigned_role_permission = response.scalar_one()

        return assigned_role_permission

    except Exception:
        await (
            db.session.rollback()
        )  # Rollback the transaction before propagating the exception
        raise  # This will be caught by the global exception handler


async def get_role_permissions(role_id: UUID) -> List[RolePermission]:
    query = select(RolePermission).where(RolePermission.role_id == role_id)
    response = await db.session.execute(query)
    permissions = response.scalars().all()

    return permissions


async def delete_role_permission(role_permission_id: UUID) -> bool:
    query = delete(RolePermission).where(RolePermission.id == role_permission_id)
    response = await db.session.execute(query)
    await db.session.commit()

    return response.rowcount > 0  # True if a row was deleted, False otherwise


async def get_user_roles(
    user_email: str, current_org: UUID
) -> List[CognitoMembersRoleLink]:
    query = select(CognitoMembersRoleLink).where(
        CognitoMembersRoleLink.user_id == user_email
    )
    response = await db.session.execute(query)
    user_roles = response.scalars().all()

    return user_roles


async def delete_user_role(user_email: str, role_id: UUID, current_org: UUID) -> bool:
    query = delete(CognitoMembersRoleLink).where(
        CognitoMembersRoleLink.user_id == user_email,
        CognitoMembersRoleLink.role_id == role_id,
    )
    response = await db.session.execute(query)
    await db.session.commit()

    return response.rowcount > 0

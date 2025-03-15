from typing import List
from uuid import UUID

from auth.cognito import get_current_org
from fastapi import APIRouter, Depends, HTTPException


from ..member.model import CognitoMembersRoleLink, Role, RolePermission
from . import controller
from .model import RoleCreate, RolePermissionAssignment, RoleUpdate, UserRoleAssignment

router = APIRouter(tags=["roles"])


@router.post("/roles", response_model=Role)
async def create_role_endpoint(
    role_data: RoleCreate,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.create_role(
        role_data
    )  # Assuming your create_role function needs current_org
    # Logging result
    # Logging at the end
    return result


@router.get("/roles", response_model=List[Role])
async def get_roles_endpoint(
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.get_roles(current_org)
    # Logging result
    # Logging at the end
    return result


@router.put("/roles/{role_id}", response_model=Role)
async def update_role_endpoint(
    role_id: UUID,
    role_data: RoleUpdate,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.update_role(role_id, role_data, current_org)
    # Logging result
    # Logging at the end
    return result


@router.delete("/roles/{role_id}", response_model=dict)
async def delete_role_endpoint(
    role_id: UUID,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    success = await controller.delete_role(role_id, current_org)
    if success:
        # Logging at the end
        return {"message": "Role deleted successfully"}
    else:
        raise HTTPException(
            status_code=404, detail="Role not found or could not be deleted"
        )


@router.post("/role-permission-assignments", response_model=RolePermissionAssignment)
async def assign_permission_endpoint(
    role_perm_data: RolePermissionAssignment,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.assign_permission_to_role(role_perm_data)
    # Logging result
    # Logging at the end
    return result


@router.get("/role-permissions", response_model=List[RolePermission])
async def get_role_permissions_endpoint(
    role_id: UUID,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.get_role_permissions(role_id)
    # Logging result
    # Logging at the end
    return result


@router.delete("/role-permissions/{role_permission_id}", response_model=dict)
async def delete_role_permission_endpoint(
    role_permission_id: UUID,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    success = await controller.delete_role_permission(role_permission_id)
    if success:
        # Logging at the end
        return {"message": "Role permission deleted successfully"}
    else:
        raise HTTPException(
            status_code=404, detail="Role permission not found or could not be deleted"
        )


@router.post("/user-role-assignments", response_model=UserRoleAssignment)
async def assign_role_endpoint(
    user_role_data: UserRoleAssignment,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    result = await controller.assign_role_to_user(user_role_data)
    # Logging result
    # Logging at the end
    return result


@router.get(
    "/user-role-assignments/{user_id}", response_model=List[CognitoMembersRoleLink]
)
async def get_user_roles_endpoint(
    user_email: str,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    roles = await controller.get_user_roles(user_email, current_org)
    # Logging result
    # Logging at the end
    return roles


@router.delete("/user-role-assignments/{user_email}/{role_id}", response_model=dict)
async def delete_user_role_endpoint(
    user_email: str,
    role_id: UUID,
    current_org: UUID = Depends(get_current_org),
):
    # Logging at the start

    success = await controller.delete_user_role(user_email, role_id, current_org)
    if success:
        # Logging at the end
        return {"message": "User role assignment deleted successfully"}
    else:
        raise HTTPException(
            status_code=404,
            detail="User role assignment not found or could not be deleted",
        )

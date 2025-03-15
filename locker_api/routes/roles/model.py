from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from ..member.model import PermissionType, RoleType


class RoleCreate(BaseModel):
    role: RoleType
    id_org: UUID


class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_id: UUID


class RolePermissionAssignment(BaseModel):
    role_id: UUID
    permission: PermissionType


class RoleUpdate(BaseModel):
    role: Optional[RoleType]


class RolePermissionUpdate(BaseModel):
    permission: PermissionType

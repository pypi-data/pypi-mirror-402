"""Authentication models - current user profile with permissions."""

from enum import StrEnum
from typing import Any

from pydantic import Field

from ._base import BaseModel

__all__ = (
    'GlobalPermissions',
    'Profile',
)


class GlobalPermissions(StrEnum):
    """Global permission types.

    System-wide permissions that users can have (not project-specific).
    """

    PROJECT_CREATE = 'global:project_create'


class Profile(BaseModel):
    """Current user profile with permissions.

    Extended user model returned for the authenticated user,
    including UI settings and access control information.
    """

    id: str = Field(description='Unique user identifier')
    name: str = Field(description='User display name')
    email: str = Field(description='User email address')
    is_active: bool = Field(description='Whether user account is active')
    is_bot: bool = Field(description='Whether this is a bot account')
    is_admin: bool = Field(description='Whether user has admin privileges')
    ui_settings: dict[str, Any] = Field(description='User interface settings')
    access_claims: list[GlobalPermissions] = Field(
        description='Global permission claims'
    )
    avatar: str = Field(description='Avatar URL or identifier')

"""User models - core user entity and CRUD operations."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from ._base import BaseModel


class UserAvatarType(str, Enum):
    """User avatar source type."""

    EXTERNAL = 'external'
    LOCAL = 'local'
    DEFAULT = 'default'


class UserOriginType(str, Enum):
    """User account origin type."""

    LOCAL = 'local'
    WB = 'wb'


class User(BaseModel):
    """User model returned from API.

    Represents a user account in the system. This is a core entity
    referenced throughout the system (issue authors, assignees, etc.).

    Note: This client library provides read-only access to users.
    User management (create/update/delete) requires admin access and
    should be done through the admin interface.
    """

    id: str = Field(
        description='Unique user identifier', examples=['5eb7cf5a86d9755df3a6c593']
    )
    name: str = Field(description='User display name')
    email: str = Field(description='User email address')
    is_active: bool = Field(description='Whether user account is active')
    is_bot: bool = Field(description='Whether this is a bot account')
    avatar: str = Field(description='Avatar URL or identifier')


class UserLinkField(BaseModel):
    """Reference to a user (link field).

    Used in other models to reference users without embedding full user data.
    Commonly used in issue authors, assignees, created_by fields, etc.
    """

    id: str = Field(description='User ID', examples=['5eb7cf5a86d9755df3a6c593'])
    name: str = Field(description='User display name')
    email: str = Field(description='User email address')
    avatar: str = Field(description='Avatar URL or identifier')


__all__ = [
    'UserAvatarType',
    'UserOriginType',
    'User',
    'UserLinkField',
]

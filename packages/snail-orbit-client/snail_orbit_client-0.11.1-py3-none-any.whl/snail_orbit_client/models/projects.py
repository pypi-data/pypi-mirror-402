"""Project models and permissions."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from ._base import BaseModel
from ._types import MongoId


class ProjectAvatarType(str, Enum):
    """Project avatar source type."""

    LOCAL = 'local'
    DEFAULT = 'default'


class ProjectPermissions(str, Enum):
    """Project-scoped permissions for collaborative entities within projects."""

    # Project permissions
    PROJECT_READ = 'project:read'
    PROJECT_UPDATE = 'project:update'
    PROJECT_DELETE = 'project:delete'
    PROJECT_MANAGE_PERMISSIONS = 'project:manage_permissions'

    # Issue permissions
    ISSUE_CREATE = 'issue:create'
    ISSUE_READ = 'issue:read'
    ISSUE_UPDATE = 'issue:update'
    ISSUE_DELETE = 'issue:delete'
    ISSUE_MANAGE_PERMISSIONS = 'issue:manage_permissions'

    # Comment permissions
    COMMENT_CREATE = 'comment:create'
    COMMENT_READ = 'comment:read'
    COMMENT_UPDATE = 'comment:update'
    COMMENT_DELETE_OWN = 'comment:delete_own'
    COMMENT_DELETE = 'comment:delete'
    COMMENT_HIDE = 'comment:hide'
    COMMENT_RESTORE = 'comment:restore'

    # History permissions
    HISTORY_HIDE = 'history:hide'
    HISTORY_RESTORE = 'history:restore'


class PermissionTargetType(str, Enum):
    """Type of permission target (user or group)."""

    GROUP = 'group'
    USER = 'user'


class PermissionType(str, Enum):
    """Permission level types."""

    VIEW = 'view'
    EDIT = 'edit'
    ADMIN = 'admin'


class EncryptionSettings(BaseModel):
    """Project encryption settings.

    References encryption configuration for encrypted projects.
    Read-only in client library - encryption setup requires admin access.
    """

    encryption_keys: list[dict[str, Any]] = Field(
        default_factory=list, description='Encryption keys'
    )
    users: list[MongoId] = Field(
        default_factory=list, description='Users with encryption access'
    )
    encrypt_attachments: bool = Field(
        default=True, description='Encrypt issue attachments'
    )
    encrypt_comments: bool = Field(default=True, description='Encrypt issue comments')
    encrypt_description: bool = Field(
        default=True, description='Encrypt issue descriptions'
    )


class Project(BaseModel):
    """Project model returned from API.

    Represents a project workspace with issues, boards, and workflows.

    Note: This client library provides read-only access to projects.
    Project management (create/update/delete) requires admin access and
    should be done through the admin interface.
    """

    id: MongoId = Field(description='Unique project identifier')
    name: str = Field(description='Project name')
    slug: str = Field(description='Project URL slug')
    description: str | None = Field(description='Project description')
    ai_description: str | None = Field(description='AI-generated project description')
    is_active: bool = Field(description='Whether project is active')
    custom_fields: list[Any] = Field(
        default_factory=list, description='Project custom field definitions'
    )
    card_fields: list[str] = Field(
        default_factory=list, description='Custom field IDs shown on cards'
    )
    workflows: list[dict[str, Any]] = Field(
        default_factory=list, description='Project workflow configurations'
    )
    is_subscribed: bool = Field(
        default=False, description='Whether current user is subscribed'
    )
    is_favorite: bool = Field(
        default=False, description='Whether current user favorited project'
    )
    avatar_type: ProjectAvatarType = Field(description='Avatar source type')
    encryption_settings: EncryptionSettings | None = Field(
        default=None, description='Encryption configuration if encrypted'
    )
    access_claims: list[ProjectPermissions] = Field(
        default_factory=list, description='Permissions for current user'
    )
    is_encrypted: bool = Field(description='Whether project uses encryption')
    members: list[dict[str, Any]] = Field(
        default_factory=list, description='Project members with their roles'
    )
    avatar: str | None = Field(description='Avatar URL or identifier')


class ProjectShortOutput(BaseModel):
    """Abbreviated project information.

    Used in lists and references where full project data is not needed.
    """

    id: MongoId = Field(description='Project ID')
    name: str = Field(description='Project name')
    slug: str = Field(description='Project slug')
    avatar: str | None = Field(description='Avatar URL')


class ProjectLinkField(BaseModel):
    """Reference to a project (link field).

    Used in other models to reference projects without embedding full project data.
    """

    id: MongoId = Field(description='Project ID')
    name: str = Field(description='Project name')
    slug: str = Field(description='Project slug')


class ProjectRoleLinkField(BaseModel):
    """Reference to a project role."""

    id: UUID = Field(description='Role UUID')
    name: str = Field(description='Role name')


# Aliases for backward compatibility
ProjectListItemOutput = ProjectShortOutput

__all__ = [
    'ProjectAvatarType',
    'ProjectPermissions',
    'PermissionTargetType',
    'PermissionType',
    'EncryptionSettings',
    'Project',
    'ProjectShortOutput',
    'ProjectListItemOutput',
    'ProjectLinkField',
    'ProjectRoleLinkField',
]

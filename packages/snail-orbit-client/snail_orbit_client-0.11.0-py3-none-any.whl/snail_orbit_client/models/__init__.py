"""Pydantic models for Snail Orbit API.

Hand-written models with Pydantic validation only (no business logic).
Custom fields use discriminated unions via Annotated[Union[...], Field(discriminator='type')].

Modules:
- users: User entity
- auth: Profile with permissions
- projects: Project management
- issues: Issue tracking with custom fields
- custom_fields: Extensible field system
- activity: Activity tracking
"""

from ._base import BaseModel, InputModel, OutputModel, PaginatedResponse
from .activity import Activity, ActivityRecord, ActivityType
from .auth import (
    GlobalPermissions,
    Profile,
)
from .custom_fields import (
    BooleanCustomFieldValue,
    CustomField,
    CustomFieldGroup,
    CustomFieldType,
    CustomFieldValue,
    DateCustomFieldValue,
    DateTimeCustomFieldValue,
    DurationCustomFieldValue,
    EnumCustomFieldValue,
    EnumMultiCustomFieldValue,
    EnumOption,
    FloatCustomFieldValue,
    IntegerCustomFieldValue,
    OwnedCustomFieldValue,
    OwnedMultiCustomFieldValue,
    OwnedOption,
    SprintCustomFieldValue,
    SprintMultiCustomFieldValue,
    SprintOption,
    StateCustomFieldValue,
    StateOption,
    StringCustomFieldValue,
    UserCustomFieldValue,
    UserMultiCustomFieldValue,
    VersionCustomFieldValue,
    VersionMultiCustomFieldValue,
    VersionOption,
)
from .issues import (
    EncryptedObject,
    EncryptedObjectInput,
    Issue,
    IssueAttachment,
    IssueAttachmentInput,
    IssueComment,
    IssueCommentCreate,
    IssueCommentOutput,
    IssueCommentUpdate,
    IssueCreate,
    IssueInterlink,
    IssueInterlinkCreate,
    IssueInterlinkType,
    IssueLinkField,
    IssueListItem,
    IssueUpdate,
    ProjectField,
    TagLink,
)
from .projects import (
    EncryptionSettings,
    PermissionTargetType,
    PermissionType,
    Project,
    ProjectAvatarType,
    ProjectLinkField,
    ProjectListItemOutput,
    ProjectPermissions,
    ProjectRoleLinkField,
    ProjectShortOutput,
)
from .system import Version
from .users import (
    User,
    UserAvatarType,
    UserLinkField,
    UserOriginType,
)

__all__ = [
    # Base classes
    'BaseModel',
    'InputModel',
    'OutputModel',
    'PaginatedResponse',
    # Activity
    'ActivityType',
    'ActivityRecord',
    'Activity',
    # Users
    'User',
    'UserLinkField',
    'UserAvatarType',
    'UserOriginType',
    # Auth
    'Profile',
    'GlobalPermissions',
    # Custom Fields (discriminated union types)
    'CustomField',
    'CustomFieldGroup',
    'CustomFieldType',
    'CustomFieldValue',
    'BooleanCustomFieldValue',
    'StringCustomFieldValue',
    'IntegerCustomFieldValue',
    'FloatCustomFieldValue',
    'DateCustomFieldValue',
    'DateTimeCustomFieldValue',
    'DurationCustomFieldValue',
    'EnumCustomFieldValue',
    'EnumMultiCustomFieldValue',
    'StateCustomFieldValue',
    'VersionCustomFieldValue',
    'VersionMultiCustomFieldValue',
    'UserCustomFieldValue',
    'UserMultiCustomFieldValue',
    'OwnedCustomFieldValue',
    'OwnedMultiCustomFieldValue',
    'SprintCustomFieldValue',
    'SprintMultiCustomFieldValue',
    # Custom Field Options
    'EnumOption',
    'StateOption',
    'VersionOption',
    'SprintOption',
    'OwnedOption',
    # Issues
    'Issue',
    'IssueCreate',
    'IssueUpdate',
    'IssueListItem',
    'IssueComment',
    'IssueCommentCreate',
    'IssueCommentUpdate',
    'IssueCommentOutput',
    'IssueAttachment',
    'IssueAttachmentInput',
    'IssueInterlink',
    'IssueInterlinkCreate',
    'IssueInterlinkType',
    'IssueLinkField',
    'EncryptedObject',
    'EncryptedObjectInput',
    'ProjectField',
    'TagLink',
    # Projects
    'Project',
    'ProjectShortOutput',
    'ProjectListItemOutput',
    'ProjectLinkField',
    'ProjectRoleLinkField',
    'ProjectAvatarType',
    'ProjectPermissions',
    'PermissionTargetType',
    'PermissionType',
    'EncryptionSettings',
    # System
    'Version',
]

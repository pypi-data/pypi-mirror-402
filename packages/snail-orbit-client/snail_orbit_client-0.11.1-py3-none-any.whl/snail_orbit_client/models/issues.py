from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from ._base import BaseModel, InputModel
from ._types import MongoId
from .custom_fields import CustomFieldValue


class IssueInterlinkType(str, Enum):
    """Types of relationships between issues."""

    RELATED = 'related'
    REQUIRED_FOR = 'required_for'
    DEPENDS_ON = 'depends_on'
    DUPLICATED_BY = 'duplicated_by'
    DUPLICATES = 'duplicates'
    SUBTASK_OF = 'subtask_of'
    PARENT_OF = 'parent_of'
    BLOCKS = 'blocks'
    BLOCKED_BY = 'blocked_by'


class EncryptedObject(BaseModel):
    """Encrypted text object."""

    value: str = Field(description='Encrypted or plain text content')
    encryption: list[dict[str, Any]] | None = Field(
        default=None, description='Encryption metadata'
    )


class EncryptedObjectInput(InputModel):
    """Input for encrypted text."""

    value: str = Field(description='Text content')
    encryption: list[dict[str, Any]] | None = Field(
        default=None, description='Encryption metadata'
    )


class ProjectField(BaseModel):
    """Project reference in issue."""

    id: MongoId = Field(description='Project ID')
    name: str = Field(description='Project name')
    slug: str = Field(description='Project slug')


class TagLink(BaseModel):
    """Tag reference."""

    id: MongoId = Field(description='Tag ID')
    name: str = Field(description='Tag name')
    color: str | None = Field(description='Tag color')


class IssueAttachment(BaseModel):
    """Issue attachment."""

    id: UUID = Field(description='Attachment UUID')
    name: str = Field(description='File name')
    size: int = Field(description='File size in bytes')
    content_type: str = Field(description='MIME type')
    author: dict[str, Any] = Field(description='User who uploaded')
    created_at: datetime = Field(description='Upload timestamp')
    ocr_text: str | None = Field(description='OCR extracted text')
    encryption: list[dict[str, Any]] | None = Field(
        default=None, description='Encryption metadata'
    )
    url: str = Field(description='Download URL')


class IssueAttachmentInput(InputModel):
    """Input for attachment."""

    name: str = Field(description='File name')
    content_type: str = Field(description='MIME type')
    data: bytes | str = Field(description='File content')


class IssueLinkField(BaseModel):
    """Minimal issue reference."""

    id: MongoId = Field(description='Issue ID')
    id_readable: str = Field(description='Readable ID (PROJ-123)')
    subject: str = Field(description='Issue title')
    project: ProjectField = Field(description='Project')


class IssueInterlink(BaseModel):
    """Link between issues."""

    id: UUID = Field(description='Link UUID')
    issue: IssueLinkField = Field(description='Linked issue')
    type: IssueInterlinkType = Field(description='Relationship type')


class IssueInterlinkCreate(InputModel):
    """Input for creating issue link."""

    issue_id: MongoId = Field(description='Target issue ID')
    type: IssueInterlinkType = Field(description='Relationship type')


class Issue(BaseModel):
    """Complete issue model."""

    id: MongoId = Field(description='Issue ID')
    aliases: list[str] = Field(default_factory=list, description='Alternative IDs')
    project: ProjectField = Field(description='Parent project')
    subject: str = Field(description='Issue title')
    text: EncryptedObject | None = Field(description='Description')
    fields: dict[str, CustomFieldValue] = Field(
        default_factory=dict, description='Custom fields'
    )
    attachments: list[IssueAttachment] = Field(
        default_factory=list, description='Attachments'
    )
    is_subscribed: bool = Field(description='User subscribed')
    id_readable: str = Field(description='Readable ID (PROJ-123)')
    created_by: dict[str, Any] = Field(description='Creator')
    created_at: datetime = Field(description='Creation time')
    updated_by: dict[str, Any] = Field(description='Last updater')
    updated_at: datetime = Field(description='Last update time')
    is_resolved: bool = Field(description='Is resolved')
    resolved_at: datetime | None = Field(description='Resolution time')
    is_closed: bool = Field(description='Is closed')
    closed_at: datetime | None = Field(description='Close time')
    interlinks: list[IssueInterlink] = Field(
        default_factory=list, description='Links to other issues'
    )
    tags: list[TagLink] = Field(default_factory=list, description='Tags')
    permissions: list[dict[str, Any]] = Field(
        default_factory=list, description='Custom permissions'
    )
    disable_project_permissions_inheritance: bool = Field(
        description='Ignore project permissions'
    )
    has_custom_permissions: bool = Field(description='Has custom permissions')
    access_claims: list[str] = Field(
        default_factory=list, description='User permissions'
    )


class IssueCreate(InputModel):
    """Input for creating issue."""

    project_id: MongoId = Field(description='Project ID')
    subject: str = Field(description='Issue title')
    text: EncryptedObjectInput | None = Field(default=None, description='Description')
    fields: dict[str, Any] | None = Field(default=None, description='Custom fields')
    attachments: list[IssueAttachmentInput] | None = Field(
        default=None, description='Attachments'
    )


class IssueUpdate(InputModel):
    """Input for updating issue."""

    project_id: MongoId | None = Field(default=None, description='Move to project')
    subject: str | None = Field(default=None, description='Update title')
    text: EncryptedObjectInput | None = Field(
        default=None, description='Update description'
    )
    fields: dict[str, Any] | None = Field(default=None, description='Update fields')
    attachments: list[IssueAttachmentInput] | None = Field(
        default=None, description='Update attachments'
    )


class IssueComment(BaseModel):
    """Issue comment."""

    id: UUID = Field(description='Comment UUID')
    text: EncryptedObject | None = Field(description='Comment text')
    author: dict[str, Any] = Field(description='Author')
    created_at: datetime = Field(description='Creation time')
    updated_at: datetime = Field(description='Update time')
    attachments: list[IssueAttachment] = Field(
        default_factory=list, description='Attachments'
    )
    is_hidden: bool = Field(description='Is hidden')
    spent_time: int = Field(description='Time spent in seconds')


class IssueCommentCreate(InputModel):
    """Input for creating comment."""

    text: EncryptedObjectInput | None = Field(description='Comment text')
    attachments: list[IssueAttachmentInput] | None = Field(
        default=None, description='Attachments'
    )
    spent_time: int = Field(default=0, ge=0, description='Time spent in seconds')


class IssueCommentUpdate(InputModel):
    """Input for updating comment."""

    text: EncryptedObjectInput | None = Field(default=None, description='Updated text')
    attachments: list[IssueAttachmentInput] | None = Field(
        default=None, description='Updated attachments'
    )
    spent_time: int | None = Field(default=None, ge=0, description='Updated time')


# Aliases for backward compatibility
IssueCommentOutput = IssueComment
IssueListItem = Issue

__all__ = [
    'IssueInterlinkType',
    'EncryptedObject',
    'EncryptedObjectInput',
    'ProjectField',
    'TagLink',
    'IssueAttachment',
    'IssueAttachmentInput',
    'IssueLinkField',
    'IssueInterlink',
    'IssueInterlinkCreate',
    'Issue',
    'IssueCreate',
    'IssueUpdate',
    'IssueComment',
    'IssueCommentCreate',
    'IssueCommentUpdate',
    'IssueCommentOutput',
    'IssueListItem',
]

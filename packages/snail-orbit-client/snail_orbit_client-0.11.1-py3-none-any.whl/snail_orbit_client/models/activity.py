"""Activity and history tracking models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from ._base import BaseModel


class ActivityType(str, Enum):
    """Type of activity/change."""

    CREATED = 'created'
    UPDATED = 'updated'
    DELETED = 'deleted'
    COMMENTED = 'commented'
    ASSIGNED = 'assigned'
    STATE_CHANGED = 'state_changed'
    FIELD_CHANGED = 'field_changed'


class ActivityRecord(BaseModel):
    """Activity/change record for audit trail."""

    id: str = Field(description='Activity record ID')
    issue_id: str = Field(description='Related issue ID')
    type: ActivityType = Field(description='Type of activity')
    user: dict[str, Any] = Field(description='User who performed action')
    timestamp: datetime = Field(description='When action occurred')
    field_name: str | None = Field(default=None, description='Changed field name')
    old_value: Any = Field(default=None, description='Previous value')
    new_value: Any = Field(default=None, description='New value')
    comment: str | None = Field(
        default=None, description='Activity comment/description'
    )


# Alias for backward compatibility
Activity = ActivityRecord

__all__ = ['ActivityType', 'ActivityRecord', 'Activity']

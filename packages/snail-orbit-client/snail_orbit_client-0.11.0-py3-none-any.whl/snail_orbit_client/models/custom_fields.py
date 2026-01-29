"""Custom field models using Pydantic v2 discriminated unions.

Uses Annotated[Union[...], Field(discriminator='type')] for type-safe field access.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import Field

from ._base import BaseModel
from ._types import MongoId
from .users import User


class CustomFieldType(str, Enum):
    """Custom field type discriminator."""

    BOOLEAN = 'boolean'
    STRING = 'string'
    INTEGER = 'integer'
    FLOAT = 'float'
    DATE = 'date'
    DATETIME = 'datetime'
    DURATION = 'duration'
    ENUM = 'enum'
    ENUM_MULTI = 'enum_multi'
    STATE = 'state'
    VERSION = 'version'
    VERSION_MULTI = 'version_multi'
    USER = 'user'
    USER_MULTI = 'user_multi'
    OWNED = 'owned'
    OWNED_MULTI = 'owned_multi'
    SPRINT = 'sprint'
    SPRINT_MULTI = 'sprint_multi'


# Primitive value wrappers for OpenAPI schema compatibility


class IntegerValue(BaseModel):
    """Integer value wrapper for OpenAPI schema."""

    type: Literal['integer'] | None = Field(
        default=None, description='Value type discriminator'
    )
    value: int | None = Field(description='Integer value')


class FloatValue(BaseModel):
    """Float value wrapper for OpenAPI schema."""

    type: Literal['float'] | None = Field(
        default=None, description='Value type discriminator'
    )
    value: float | None = Field(description='Float value')


class BooleanValue(BaseModel):
    """Boolean value wrapper for OpenAPI schema."""

    type: Literal['boolean'] | None = Field(
        default=None, description='Value type discriminator'
    )
    value: bool | None = Field(description='Boolean value')


class StringValue(BaseModel):
    """String value wrapper for OpenAPI schema."""

    type: Literal['string'] | None = Field(
        default=None, description='Value type discriminator'
    )
    value: str | None = Field(description='String value')


class DateValue(BaseModel):
    """Date value wrapper for OpenAPI schema."""

    type: Literal['date'] | None = Field(
        default=None, description='Value type discriminator'
    )
    value: date | None = Field(description='Date value')


class DateTimeValue(BaseModel):
    """DateTime value wrapper for OpenAPI schema."""

    type: Literal['datetime'] | None = Field(
        default=None, description='Value type discriminator'
    )
    value: datetime | None = Field(description='DateTime value')


class DurationValue(BaseModel):
    """Duration value wrapper for OpenAPI schema."""

    type: Literal['duration'] | None = Field(
        default=None, description='Value type discriminator'
    )
    value: int | None = Field(description='Duration in seconds')


# Option types for complex custom fields


class EnumOption(BaseModel):
    """Enum option metadata."""

    type: Literal['enum'] | None = Field(
        default=None, description='Value type discriminator'
    )
    uuid: str = Field(description='Option UUID')
    value: str | None = Field(default=None, description='Option value')
    color: str | None = Field(default=None, description='Display color')
    is_archived: bool = Field(default=False, description='Whether option is archived')


class StateOption(BaseModel):
    """State option metadata for workflow states."""

    type: Literal['state'] | None = Field(
        default=None, description='Value type discriminator'
    )
    uuid: str = Field(description='State UUID')
    value: str = Field(description='State name')
    color: str | None = Field(default=None, description='Display color')
    is_resolved: bool = Field(
        default=False, description='Whether state marks issue as resolved'
    )
    is_closed: bool = Field(
        default=False, description='Whether state marks issue as closed'
    )
    is_archived: bool = Field(default=False, description='Whether state is archived')


class VersionOption(BaseModel):
    """Version option metadata."""

    type: Literal['version'] | None = Field(
        default=None, description='Value type discriminator'
    )
    id: str = Field(description='Version ID')
    value: str = Field(description='Version name')
    is_archived: bool = Field(default=False, description='Whether version is archived')
    color: str | None = Field(default=None, description='Display color')


class SprintOption(BaseModel):
    """Sprint option metadata."""

    type: Literal['sprint'] | None = Field(
        default=None, description='Value type discriminator'
    )
    uuid: str = Field(description='Sprint UUID')
    value: str | None = Field(default=None, description='Sprint name')
    is_completed: bool = Field(default=False, description='Whether sprint is completed')
    is_archived: bool = Field(default=False, description='Whether sprint is archived')
    color: str | None = Field(default=None, description='Display color')
    start_date: date | None = Field(default=None, description='Sprint start date')
    end_date: date | None = Field(default=None, description='Sprint end date')
    description: str | None = Field(default=None, description='Sprint description')


class OwnedOption(BaseModel):
    """Owned option metadata with owner assignment."""

    type: Literal['owned'] | None = Field(
        default=None, description='Value type discriminator'
    )
    uuid: str = Field(description='Option UUID')
    value: str | None = Field(default=None, description='Option value')
    owner: User | None = Field(default=None, description='Owner user object')
    color: str | None = Field(default=None, description='Display color')
    is_archived: bool = Field(default=False, description='Whether option is archived')


# Base class for all custom field values


class CustomFieldValueBase(BaseModel):
    """Base for all custom field value types.

    Provides common fields shared by all custom field values.
    """

    id: MongoId = Field(description='Custom field ID')
    gid: str = Field(description='Custom field group ID')
    name: str = Field(description='Field name')
    type: str = Field(description='Field type discriminator')


# Specific custom field value types


class BooleanCustomFieldValue(CustomFieldValueBase):
    """Boolean custom field value."""

    type: Literal[CustomFieldType.BOOLEAN] = CustomFieldType.BOOLEAN
    value: BooleanValue = Field(description='Boolean value wrapper')


class StringCustomFieldValue(CustomFieldValueBase):
    """String custom field value."""

    type: Literal[CustomFieldType.STRING] = CustomFieldType.STRING
    value: StringValue = Field(description='String value wrapper')


class IntegerCustomFieldValue(CustomFieldValueBase):
    """Integer custom field value."""

    type: Literal[CustomFieldType.INTEGER] = CustomFieldType.INTEGER
    value: IntegerValue = Field(description='Integer value wrapper')


class FloatCustomFieldValue(CustomFieldValueBase):
    """Float custom field value."""

    type: Literal[CustomFieldType.FLOAT] = CustomFieldType.FLOAT
    value: FloatValue = Field(description='Float value wrapper')


class DateCustomFieldValue(CustomFieldValueBase):
    """Date custom field value."""

    type: Literal[CustomFieldType.DATE] = CustomFieldType.DATE
    value: DateValue = Field(description='Date value wrapper')


class DateTimeCustomFieldValue(CustomFieldValueBase):
    """DateTime custom field value."""

    type: Literal[CustomFieldType.DATETIME] = CustomFieldType.DATETIME
    value: DateTimeValue = Field(description='DateTime value wrapper')


class DurationCustomFieldValue(CustomFieldValueBase):
    """Duration custom field value (in seconds)."""

    type: Literal[CustomFieldType.DURATION] = CustomFieldType.DURATION
    value: DurationValue = Field(description='Duration value wrapper')


class EnumCustomFieldValue(CustomFieldValueBase):
    """Enum custom field with single selection."""

    type: Literal[CustomFieldType.ENUM] = CustomFieldType.ENUM
    value: EnumOption | None = Field(description='Selected enum option')


class EnumMultiCustomFieldValue(CustomFieldValueBase):
    """Enum custom field with multiple selections."""

    type: Literal[CustomFieldType.ENUM_MULTI] = CustomFieldType.ENUM_MULTI
    value: list[EnumOption] = Field(
        default_factory=list, description='Selected enum options'
    )


class StateCustomFieldValue(CustomFieldValueBase):
    """State custom field for workflow states."""

    type: Literal[CustomFieldType.STATE] = CustomFieldType.STATE
    value: StateOption | None = Field(description='Selected state option')


class VersionCustomFieldValue(CustomFieldValueBase):
    """Version custom field with single selection."""

    type: Literal[CustomFieldType.VERSION] = CustomFieldType.VERSION
    value: VersionOption | None = Field(description='Selected version')


class VersionMultiCustomFieldValue(CustomFieldValueBase):
    """Version custom field with multiple selections."""

    type: Literal[CustomFieldType.VERSION_MULTI] = CustomFieldType.VERSION_MULTI
    value: list[VersionOption] = Field(
        default_factory=list, description='Selected versions'
    )


class UserCustomFieldValue(CustomFieldValueBase):
    """User custom field with single selection."""

    type: Literal[CustomFieldType.USER] = CustomFieldType.USER
    value: dict[str, Any] | None = Field(description='Selected user (UserLinkField)')


class UserMultiCustomFieldValue(CustomFieldValueBase):
    """User custom field with multiple selections."""

    type: Literal[CustomFieldType.USER_MULTI] = CustomFieldType.USER_MULTI
    value: list[dict[str, Any]] = Field(
        default_factory=list, description='Selected users (UserLinkField)'
    )


class OwnedCustomFieldValue(CustomFieldValueBase):
    """Owned custom field with single selection."""

    type: Literal[CustomFieldType.OWNED] = CustomFieldType.OWNED
    value: OwnedOption | None = Field(description='Selected owned option')


class OwnedMultiCustomFieldValue(CustomFieldValueBase):
    """Owned custom field with multiple selections."""

    type: Literal[CustomFieldType.OWNED_MULTI] = CustomFieldType.OWNED_MULTI
    value: list[OwnedOption] = Field(
        default_factory=list, description='Selected owned options'
    )


class SprintCustomFieldValue(CustomFieldValueBase):
    """Sprint custom field with single selection."""

    type: Literal[CustomFieldType.SPRINT] = CustomFieldType.SPRINT
    value: SprintOption | None = Field(description='Selected sprint')


class SprintMultiCustomFieldValue(CustomFieldValueBase):
    """Sprint custom field with multiple selections."""

    type: Literal[CustomFieldType.SPRINT_MULTI] = CustomFieldType.SPRINT_MULTI
    value: list[SprintOption] = Field(
        default_factory=list, description='Selected sprints'
    )


# The discriminated union - NO RootModel wrapper needed!
# This is the key innovation: clean type-safe discriminated unions

CustomFieldValue = Annotated[
    BooleanCustomFieldValue
    | StringCustomFieldValue
    | IntegerCustomFieldValue
    | FloatCustomFieldValue
    | DateCustomFieldValue
    | DateTimeCustomFieldValue
    | DurationCustomFieldValue
    | EnumCustomFieldValue
    | EnumMultiCustomFieldValue
    | StateCustomFieldValue
    | VersionCustomFieldValue
    | VersionMultiCustomFieldValue
    | UserCustomFieldValue
    | UserMultiCustomFieldValue
    | OwnedCustomFieldValue
    | OwnedMultiCustomFieldValue
    | SprintCustomFieldValue
    | SprintMultiCustomFieldValue,
    Field(discriminator='type'),
]


# Helper functions for type-safe custom field access


# Custom field definition models (for fetching field metadata)


class CustomField(BaseModel):
    """Custom field definition (metadata about the field itself)."""

    id: MongoId = Field(description='Unique field identifier')
    gid: str = Field(description='Group identifier')
    name: str = Field(description='Field name')
    type: CustomFieldType = Field(description='Field type')
    label: str | None = Field(default=None, description='Display label')
    description: str | None = Field(default=None, description='Field description')
    is_required: bool = Field(default=False, description='Whether field is required')
    is_archived: bool = Field(default=False, description='Whether field is archived')
    options: list[dict[str, Any]] | None = Field(
        default=None, description='Field options (for enum, state, etc.)'
    )


class CustomFieldGroup(BaseModel):
    """Custom field group (collection of related fields)."""

    gid: str = Field(description='Group identifier')
    name: str = Field(description='Group name')
    type: CustomFieldType = Field(description='Field type for this group')
    description: str | None = Field(default=None, description='Group description')
    ai_description: str | None = Field(
        default=None, description='AI-generated description'
    )
    fields: list[dict[str, Any]] = Field(
        default_factory=list, description='Fields in this group'
    )


__all__ = [
    'CustomFieldType',
    'EnumOption',
    'StateOption',
    'VersionOption',
    'SprintOption',
    'OwnedOption',
    'CustomFieldValueBase',
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
    'CustomFieldValue',
    'CustomField',
    'CustomFieldGroup',
]

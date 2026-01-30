"""Base model classes for all Snail Orbit models."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field


class BaseModel(PydanticBaseModel):
    """Base class for all Snail Orbit API response models.

    Designed for API outputs with:
    - frozen=True: Immutable - represents server state
    - extra='ignore': Tolerant of new API fields (forward compatibility)
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        extra='ignore',
        str_strip_whitespace=True,
        validate_default=True,
        frozen=True,
    )


class InputModel(PydanticBaseModel):
    """Base class for API input models (create/update requests).

    Designed for API inputs with:
    - frozen=False: Mutable - we're building these objects
    - extra='forbid': Strict - catch typos in field names
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra='forbid',
        str_strip_whitespace=True,
        frozen=False,
    )


class OutputModel(BaseModel):
    """Base class for API output models with common audit fields.

    All models returned from the API inherit from this class.
    """

    id: str = Field(description='Unique object identifier')
    created_at: datetime = Field(description='Creation timestamp')
    updated_at: datetime | None = Field(
        default=None, description='Last update timestamp'
    )


T = TypeVar('T', bound=BaseModel)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response wrapper.

    Wraps lists of items with pagination metadata.
    """

    count: int = Field(description='Total items matching query')
    limit: int = Field(description='Page size limit')
    offset: int = Field(description='Number of items skipped')
    items: list[T] = Field(description='Items in current page')

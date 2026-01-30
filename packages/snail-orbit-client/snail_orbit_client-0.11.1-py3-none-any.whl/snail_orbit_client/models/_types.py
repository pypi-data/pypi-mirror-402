"""Common type aliases and utility types."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

# MongoDB ObjectId type - 24 character hex string
MongoId = Annotated[str, Field(pattern=r'^[0-9a-f]{24}$', min_length=24, max_length=24)]

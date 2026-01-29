"""System models for Snail Orbit API."""

from ._base import BaseModel


class Version(BaseModel):
    """System version information."""

    version: str
    build: str | None = None

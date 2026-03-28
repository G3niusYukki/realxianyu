"""Shared Pydantic models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        validate_assignment=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str = Field(default="ok", description="Service status")
    version: str = Field(default="0.1.0", description="Service version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Check timestamp",
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    code: str = Field(description="Error code")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details",
    )

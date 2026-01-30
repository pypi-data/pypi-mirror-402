"""
Companion (member) schemas

Schema hierarchy:
- CompanionBase: Mutable fields (used in Create/Update)
- CompanionCreate: Base + system_prompt (mutable, but sensitive)
- CompanionUpdate: Base + system_prompt (mutable, but sensitive)
- Companion: Response with all fields including system_prompt (internal use)
- CompanionPublic: Response without sensitive fields (API use)
"""

from datetime import datetime

from humps import camelize
from pydantic import BaseModel, ConfigDict, Field


class CompanionBase(BaseModel):
    """Base companion model with common mutable fields.

    Contains fields that can be modified after creation.
    Excludes system_prompt (sensitive, requires explicit inclusion).
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    aidol_id: str | None = Field(default=None, description="AIdol group ID")
    name: str = Field(..., description="Companion name")
    biography: str | None = Field(default=None, description="Companion biography")
    profile_picture_url: str | None = Field(
        default=None, description="Profile picture URL"
    )


class CompanionCreate(CompanionBase):
    """Schema for creating a companion (no id).

    Includes system_prompt for creation (excluded from response for security).
    """

    system_prompt: str | None = Field(
        default=None, description="AI system prompt (not exposed in responses)"
    )


class CompanionUpdate(BaseModel):
    """Schema for updating a companion (all fields optional)."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    aidol_id: str | None = Field(default=None, description="AIdol group ID")
    name: str | None = Field(default=None, description="Companion name")
    biography: str | None = Field(default=None, description="Companion biography")
    profile_picture_url: str | None = Field(
        default=None, description="Profile picture URL"
    )
    system_prompt: str | None = Field(
        default=None, description="AI system prompt (not exposed in responses)"
    )


class Companion(CompanionBase):
    """Companion response schema with id and timestamps.

    Includes system_prompt for internal use (Service layer).
    Use CompanionPublic for API responses to exclude sensitive fields.
    """

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, alias_generator=camelize
    )

    id: str = Field(..., description="Companion ID")
    system_prompt: str | None = Field(
        default=None, description="AI system prompt (sensitive, internal use only)"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CompanionPublic(CompanionBase):
    """Public companion response schema without sensitive fields.

    Excludes system_prompt for API responses.
    """

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, alias_generator=camelize
    )

    id: str = Field(..., description="Companion ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

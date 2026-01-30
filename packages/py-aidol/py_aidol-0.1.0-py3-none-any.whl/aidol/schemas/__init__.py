"""
AIdol Pydantic schemas
"""

from aidol.schemas.aidol import (
    AIdol,
    AIdolBase,
    AIdolCreate,
    AIdolPublic,
    AIdolUpdate,
    ImageGenerationData,
    ImageGenerationRequest,
    ImageGenerationResponse,
)
from aidol.schemas.companion import (
    Companion,
    CompanionBase,
    CompanionCreate,
    CompanionPublic,
    CompanionUpdate,
)

__all__ = [
    "AIdol",
    "AIdolBase",
    "AIdolCreate",
    "AIdolPublic",
    "AIdolUpdate",
    "ImageGenerationData",
    "ImageGenerationRequest",
    "ImageGenerationResponse",
    "Companion",
    "CompanionBase",
    "CompanionCreate",
    "CompanionPublic",
    "CompanionUpdate",
]

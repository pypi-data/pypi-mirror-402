"""
Companion repository

Implements BaseRepository pattern for BaseCrudRouter compatibility.
"""

from datetime import timezone

from aioia_core.repositories import BaseRepository
from sqlalchemy.orm import Session

from aidol.models import DBCompanion
from aidol.schemas import Companion, CompanionCreate, CompanionUpdate


def _convert_db_companion_to_model(db_companion: DBCompanion) -> Companion:
    """Convert DB Companion to Pydantic model.

    Includes system_prompt for internal use (Service layer).
    Router should convert to CompanionPublic for API responses.
    """
    return Companion(
        id=db_companion.id,
        aidol_id=db_companion.aidol_id,
        name=db_companion.name,
        biography=db_companion.biography,
        profile_picture_url=db_companion.profile_picture_url,
        system_prompt=db_companion.system_prompt,
        created_at=db_companion.created_at.replace(tzinfo=timezone.utc),
        updated_at=db_companion.updated_at.replace(tzinfo=timezone.utc),
    )


def _convert_companion_create_to_db(schema: CompanionCreate) -> dict:
    """Convert CompanionCreate schema to DB model data dict.

    Includes system_prompt for AI configuration.
    """
    return schema.model_dump(exclude_unset=True)


class CompanionRepository(
    BaseRepository[Companion, DBCompanion, CompanionCreate, CompanionUpdate]
):
    """
    Database-backed Companion repository.

    Extends BaseRepository for CRUD operations compatible with BaseCrudRouter.
    """

    def __init__(self, db_session: Session):
        super().__init__(
            db_session=db_session,
            db_model=DBCompanion,
            convert_to_model=_convert_db_companion_to_model,
            convert_to_db_model=_convert_companion_create_to_db,
        )

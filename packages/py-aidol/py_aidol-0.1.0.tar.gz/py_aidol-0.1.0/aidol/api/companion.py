"""
Companion API router

Public endpoints for Companion creation and retrieval.
Public access pattern: no authentication required.
"""

from aioia_core.auth import UserInfoProvider
from aioia_core.errors import ErrorResponse
from aioia_core.fastapi import BaseCrudRouter
from aioia_core.settings import JWTSettings
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

from aidol.protocols import (
    CompanionRepositoryFactoryProtocol,
    CompanionRepositoryProtocol,
)
from aidol.schemas import Companion, CompanionCreate, CompanionPublic, CompanionUpdate


class CompanionSingleItemResponse(BaseModel):
    """Single item response for Companion (public)."""

    data: CompanionPublic


class CompanionPaginatedResponse(BaseModel):
    """Paginated response for Companion (public)."""

    data: list[CompanionPublic]
    total: int


class CompanionRouter(
    BaseCrudRouter[
        Companion, CompanionCreate, CompanionUpdate, CompanionRepositoryProtocol
    ]
):
    """
    Companion router with public endpoints.

    Public CRUD pattern: no authentication required.
    Returns CompanionPublic (excludes system_prompt) for all responses.
    """

    def _register_routes(self) -> None:
        """Register routes (public CRUD)"""
        self._register_public_list_route()
        self._register_public_create_route()
        self._register_public_get_route()

    def _register_public_list_route(self) -> None:
        """GET /{resource_name} - List Companions (public)"""

        @self.router.get(
            f"/{self.resource_name}",
            response_model=CompanionPaginatedResponse,
            status_code=status.HTTP_200_OK,
            summary="List Companions",
            description="List all Companions with optional filtering (public endpoint)",
        )
        async def list_companions(
            current: int = Query(1, ge=1, description="Current page number"),
            page_size: int = Query(10, ge=1, le=100, description="Items per page"),
            sort_param: str | None = Query(
                None,
                alias="sort",
                description='Sorting criteria in JSON format. Example: [["createdAt","desc"]]',
            ),
            filters_param: str | None = Query(
                None,
                alias="filters",
                description="Filter conditions (JSON format)",
            ),
            repository: CompanionRepositoryProtocol = Depends(self.get_repository_dep),
        ):
            """List Companions with pagination, sorting, and filtering."""
            sort_list, filter_list = self._parse_query_params(sort_param, filters_param)
            items, total = repository.get_all(
                current=current,
                page_size=page_size,
                sort=sort_list,
                filters=filter_list,
            )
            # Convert to Public schema (exclude system_prompt)
            public_items = [CompanionPublic(**c.model_dump()) for c in items]
            return CompanionPaginatedResponse(data=public_items, total=total)

    def _register_public_create_route(self) -> None:
        """POST /{resource_name} - Create a Companion (public)"""

        @self.router.post(
            f"/{self.resource_name}",
            response_model=CompanionSingleItemResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create Companion",
            description="Create a new Companion (public endpoint)",
        )
        async def create_companion(
            request: CompanionCreate,
            repository: CompanionRepositoryProtocol = Depends(self.get_repository_dep),
        ):
            """Create a new Companion."""
            created = repository.create(request)
            # Convert to Public schema (exclude system_prompt)
            public_companion = CompanionPublic(**created.model_dump())
            return CompanionSingleItemResponse(data=public_companion)

    def _register_public_get_route(self) -> None:
        """GET /{resource_name}/{id} - Get a Companion (public)"""

        @self.router.get(
            f"/{self.resource_name}/{{item_id}}",
            response_model=CompanionSingleItemResponse,
            status_code=status.HTTP_200_OK,
            summary="Get Companion",
            description="Get Companion by ID (public endpoint)",
            responses={
                404: {"model": ErrorResponse, "description": "Companion not found"},
            },
        )
        async def get_companion(
            item_id: str,
            repository: CompanionRepositoryProtocol = Depends(self.get_repository_dep),
        ):
            """Get Companion by ID."""
            companion = self._get_item_or_404(repository, item_id)
            # Convert to Public schema (exclude system_prompt)
            public_companion = CompanionPublic(**companion.model_dump())
            return CompanionSingleItemResponse(data=public_companion)


def create_companion_router(
    db_session_factory: sessionmaker,
    repository_factory: CompanionRepositoryFactoryProtocol,
    jwt_settings: JWTSettings | None = None,
    user_info_provider: UserInfoProvider | None = None,
    resource_name: str = "companions",
    tags: list[str] | None = None,
) -> APIRouter:
    """
    Create Companion router with dependency injection.

    Args:
        db_session_factory: Database session factory
        repository_factory: Factory implementing CompanionRepositoryFactoryProtocol
        jwt_settings: Optional JWT settings for authentication
        user_info_provider: Optional user info provider
        resource_name: Resource name for routes (default: "companions")
        tags: Optional OpenAPI tags

    Returns:
        FastAPI APIRouter instance
    """
    router = CompanionRouter(
        model_class=Companion,
        create_schema=CompanionCreate,
        update_schema=CompanionUpdate,
        db_session_factory=db_session_factory,
        repository_factory=repository_factory,
        user_info_provider=user_info_provider,
        jwt_secret_key=jwt_settings.secret_key if jwt_settings else None,
        resource_name=resource_name,
        tags=tags or ["Companion"],
    )
    return router.get_router()

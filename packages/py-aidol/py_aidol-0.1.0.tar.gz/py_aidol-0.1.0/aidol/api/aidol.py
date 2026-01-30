"""
AIdol API router

Public endpoints for AIdol group creation and retrieval.
Public access pattern: no authentication required.
"""

from aioia_core.auth import UserInfoProvider
from aioia_core.errors import ErrorResponse
from aioia_core.fastapi import BaseCrudRouter
from aioia_core.settings import JWTSettings, OpenAIAPISettings
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

from aidol.protocols import (
    AIdolRepositoryFactoryProtocol,
    AIdolRepositoryProtocol,
    ImageStorageProtocol,
)
from aidol.schemas import (
    AIdol,
    AIdolCreate,
    AIdolPublic,
    AIdolUpdate,
    ImageGenerationData,
    ImageGenerationRequest,
    ImageGenerationResponse,
)
from aidol.services import ImageGenerationService


class AIdolSingleItemResponse(BaseModel):
    """Single item response for AIdol (public)."""

    data: AIdolPublic


class AIdolRouter(
    BaseCrudRouter[AIdol, AIdolCreate, AIdolUpdate, AIdolRepositoryProtocol]
):
    """
    AIdol router with public endpoints.

    Public CRUD pattern: no authentication required.
    Returns AIdolPublic (excludes claim_token) for all responses.
    """

    def __init__(
        self,
        openai_settings: OpenAIAPISettings,
        image_storage: ImageStorageProtocol,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.openai_settings = openai_settings
        self.image_storage = image_storage

    def _register_routes(self) -> None:
        """Register routes (public CRUD + image generation)"""
        self._register_image_generation_route()
        self._register_public_create_route()
        self._register_public_get_route()

    def _register_public_create_route(self) -> None:
        """POST /{resource_name} - Create an AIdol group (public)"""

        @self.router.post(
            f"/{self.resource_name}",
            response_model=AIdolSingleItemResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create AIdol group",
            description="Create a new AIdol group (public endpoint)",
        )
        async def create_aidol(
            request: AIdolCreate,
            repository: AIdolRepositoryProtocol = Depends(self.get_repository_dep),
        ):
            """Create a new AIdol group."""
            created = repository.create(request)
            # Convert to Public schema (exclude claim_token)
            public_aidol = AIdolPublic(**created.model_dump())
            return AIdolSingleItemResponse(data=public_aidol)

    def _register_public_get_route(self) -> None:
        """GET /{resource_name}/{id} - Get an AIdol group (public)"""

        @self.router.get(
            f"/{self.resource_name}/{{item_id}}",
            response_model=AIdolSingleItemResponse,
            status_code=status.HTTP_200_OK,
            summary="Get AIdol group",
            description="Get AIdol group by ID (public endpoint)",
            responses={
                404: {"model": ErrorResponse, "description": "AIdol group not found"},
            },
        )
        async def get_aidol(
            item_id: str,
            repository: AIdolRepositoryProtocol = Depends(self.get_repository_dep),
        ):
            """Get AIdol group by ID."""
            aidol = self._get_item_or_404(repository, item_id)
            # Convert to Public schema (exclude claim_token)
            public_aidol = AIdolPublic(**aidol.model_dump())
            return AIdolSingleItemResponse(data=public_aidol)

    def _register_image_generation_route(self) -> None:
        """POST /{resource_name}/images - Generate image for AIdol or Companion"""

        @self.router.post(
            f"/{self.resource_name}/images",
            response_model=ImageGenerationResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Generate image",
            description="Generate image for AIdol emblem or Companion profile",
            responses={
                500: {"model": ErrorResponse, "description": "Image generation failed"},
            },
        )
        async def generate_image(request: ImageGenerationRequest):
            """Generate image from prompt."""
            # Generate and download image (TTS pattern: service returns data)
            service = ImageGenerationService(self.openai_settings)
            image = service.generate_and_download_image(
                prompt=request.prompt,
                size="1024x1024",
                quality="standard",
            )

            if image is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Image generation failed",
                )

            # Upload to permanent storage (TTS pattern: API layer orchestrates)
            image_url = self.image_storage.upload_image(image)

            return ImageGenerationResponse(
                data=ImageGenerationData(
                    image_url=image_url,
                    width=1024,
                    height=1024,
                    format="png",
                )
            )


def create_aidol_router(
    openai_settings: OpenAIAPISettings,
    db_session_factory: sessionmaker,
    repository_factory: AIdolRepositoryFactoryProtocol,
    image_storage: ImageStorageProtocol,
    jwt_settings: JWTSettings | None = None,
    user_info_provider: UserInfoProvider | None = None,
    resource_name: str = "aidols",
    tags: list[str] | None = None,
) -> APIRouter:
    """
    Create AIdol router with dependency injection.

    Args:
        openai_settings: OpenAI API settings for image generation
        db_session_factory: Database session factory
        repository_factory: Factory implementing AIdolRepositoryFactoryProtocol
        image_storage: Image storage for permanent URLs
        jwt_settings: Optional JWT settings for authentication
        user_info_provider: Optional user info provider
        resource_name: Resource name for routes (default: "aidols")
        tags: Optional OpenAPI tags

    Returns:
        FastAPI APIRouter instance
    """
    router = AIdolRouter(
        openai_settings=openai_settings,
        image_storage=image_storage,
        model_class=AIdol,
        create_schema=AIdolCreate,
        update_schema=AIdolUpdate,
        db_session_factory=db_session_factory,
        repository_factory=repository_factory,
        user_info_provider=user_info_provider,
        jwt_secret_key=jwt_settings.secret_key if jwt_settings else None,
        resource_name=resource_name,
        tags=tags or ["AIdol"],
    )
    return router.get_router()

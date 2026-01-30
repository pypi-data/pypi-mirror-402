"""
Image generation service for AIdol

Generates images using OpenAI DALL-E 3 for AIdol emblems and Companion profiles.
"""

import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Literal

import httpx
import openai
import PIL.Image
from aioia_core.settings import OpenAIAPISettings

logger = logging.getLogger(__name__)


@dataclass
class ImageGenerationResponse:
    """Structured response from the Image Generation service"""

    url: str
    revised_prompt: str | None


class ImageGenerationService:
    """Service for generating images using OpenAI DALL-E 3"""

    def __init__(self, openai_settings: OpenAIAPISettings):
        """
        Initialize the Image Generation service with OpenAI settings.

        Args:
            openai_settings: OpenAI settings containing required API key
        """
        self.settings = openai_settings
        self.client = openai.OpenAI(api_key=self.settings.api_key)

    def generate_image(
        self,
        prompt: str,
        size: Literal[
            "1024x1024",
            "1792x1024",
            "1024x1792",
        ] = "1024x1024",
        quality: Literal["standard", "hd"] = "standard",
    ) -> ImageGenerationResponse | None:
        """
        Generate an image from a text prompt using OpenAI DALL-E 3.

        Args:
            prompt: Text description of the image to generate
            size: Image size (default: "1024x1024")
            quality: Image quality "standard" or "hd" (default: "standard")

        Returns:
            An ImageGenerationResponse object containing the image URL and revised prompt,
            or None if generation fails.

        Raises:
            openai.OpenAIError: If OpenAI API call fails.
        """
        try:
            logger.info("Generating image with OpenAI DALL-E 3...")
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )

            if not response.data or len(response.data) == 0:
                logger.error("No image data returned from OpenAI")
                return None

            image_data = response.data[0]
            url = image_data.url

            if not url:
                logger.error("No URL found in image response")
                return None

            revised_prompt = image_data.revised_prompt

            logger.info("Successfully generated image: %s", url[:100])
            return ImageGenerationResponse(
                url=url,
                revised_prompt=revised_prompt,
            )

        except openai.OpenAIError as e:
            logger.error("OpenAI API error: %s", e)
            raise

    def _download_image(self, url: str) -> PIL.Image.Image:
        """Download image from URL and return as PIL Image.

        Args:
            url: URL of the image to download.

        Raises:
            httpx.HTTPError: If download fails.
        """
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return PIL.Image.open(BytesIO(response.content))

    def generate_and_download_image(
        self,
        prompt: str,
        size: Literal[
            "1024x1024",
            "1792x1024",
            "1024x1792",
        ] = "1024x1024",
        quality: Literal["standard", "hd"] = "standard",
    ) -> PIL.Image.Image | None:
        """Generate an image and download as PIL Image.

        DALL-E returns temporary URLs that expire in 1-2 hours.
        Use this method to download the image immediately after generation.

        Args:
            prompt: Text description of the image to generate.
            size: Image size (default: "1024x1024").
            quality: Image quality "standard" or "hd" (default: "standard").

        Returns:
            PIL Image object, or None if generation fails.

        Raises:
            openai.OpenAIError: If OpenAI API call fails.
            httpx.HTTPError: If image download fails.
        """
        result = self.generate_image(prompt, size, quality)
        if result is None:
            return None

        logger.info("Downloading image from DALL-E temporary URL...")
        return self._download_image(result.url)

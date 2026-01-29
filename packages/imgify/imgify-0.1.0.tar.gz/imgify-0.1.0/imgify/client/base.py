from abc import ABC, abstractmethod
from typing import Self

from dotenv import load_dotenv
from openai import AsyncOpenAI, AsyncAzureOpenAI
from openai.types import ImagesResponse

from imgify.models import (
    ImageResponse,
    ImageGenerationConfig,
    ImageModelApiName,
    ImageQuality,
    ImageSize,
    ResponseFormat,
)

load_dotenv(override=True)


class BaseImgifyClient(ABC):
    _client: AsyncOpenAI | AsyncAzureOpenAI

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout

    @abstractmethod
    def _initialize_client(self) -> None:
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._client.close()

    async def generate_image(
        self,
        prompt: str,
        *,
        model: ImageModelApiName = ImageModelApiName.GPT_IMAGE_1,
        size: ImageSize = ImageSize.SQUARE_1024,
        quality: ImageQuality | None = None,
    ) -> ImageResponse:
        config = ImageGenerationConfig(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            response_format=ResponseFormat.B64_JSON,
        )
        params = config.model_dump()
        response: ImagesResponse = await self._client.images.generate(**params)
        image_data = response.data[0]
        return ImageResponse(b64_json=image_data.b64_json)
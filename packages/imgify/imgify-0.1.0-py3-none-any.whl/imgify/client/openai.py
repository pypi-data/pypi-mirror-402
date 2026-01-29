import os

from openai import AsyncOpenAI

from imgify.client.base import BaseImgifyClient
from imgify.exceptions import DallifyAuthenticationException


class ImgifyOpenAI(BaseImgifyClient):
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        super().__init__(api_key=api_key, timeout=timeout)
        self._api_key = self._api_key or os.getenv("OPENAI_API_KEY")
        self._initialize_client()

    def _initialize_client(self) -> None:
        if not self._api_key:
            error_msg = (
                "No OpenAI API key provided. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
            raise DallifyAuthenticationException(error_msg)

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            timeout=self._timeout,
        )
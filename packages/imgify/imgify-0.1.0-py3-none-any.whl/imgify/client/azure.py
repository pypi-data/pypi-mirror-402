import os

from openai import AsyncAzureOpenAI

from imgify.client.base import BaseImgifyClient
from imgify.exceptions import DallifyAuthenticationException

_AZURE_API_VERSION = "2024-02-01"

class ImgifyAzure(BaseImgifyClient):
    def __init__(
        self,
        api_key: str | None = None,
        azure_endpoint: str | None = None,
        api_version: str = _AZURE_API_VERSION,
        timeout: float = 60.0,
    ) -> None:
        super().__init__(api_key=api_key, timeout=timeout)
        self._api_key = self._api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self._azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self._api_version = api_version
        self._initialize_client()

    def _initialize_client(self) -> None:
        if not self._api_key:
            error_msg = (
                "No Azure OpenAI API key provided. "
                "Set AZURE_OPENAI_API_KEY environment variable or pass api_key parameter."
            )
            raise DallifyAuthenticationException(error_msg)

        if not self._azure_endpoint:
            error_msg = (
                "No Azure OpenAI endpoint provided. "
                "Set AZURE_OPENAI_ENDPOINT environment variable or pass azure_endpoint parameter."
            )
            raise DallifyAuthenticationException(error_msg)

        self._client = AsyncAzureOpenAI(
            api_key=self._api_key,
            azure_endpoint=self._azure_endpoint,
            api_version=self._api_version,
            timeout=self._timeout,
        )
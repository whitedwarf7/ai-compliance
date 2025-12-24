import httpx
from typing import Any

from .base import BaseProvider


class AzureOpenAIProvider(BaseProvider):
    """Azure OpenAI API provider."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str = "2024-02-15-preview",
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version
        self.client = httpx.AsyncClient(
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def chat_completion(self, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """Send a chat completion request to Azure OpenAI."""
        url = (
            f"{self.endpoint}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )
        response = await self.client.post(url, json=payload)
        return response.json(), response.status_code

    def get_provider_name(self) -> str:
        return "azure"

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()



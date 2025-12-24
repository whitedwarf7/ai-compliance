import httpx
from typing import Any

from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    BASE_URL = "https://api.openai.com/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def chat_completion(self, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """Send a chat completion request to OpenAI."""
        response = await self.client.post("/chat/completions", json=payload)
        return response.json(), response.status_code

    def get_provider_name(self) -> str:
        return "openai"

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()



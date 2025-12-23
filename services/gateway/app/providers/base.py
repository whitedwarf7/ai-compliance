from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    async def chat_completion(self, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """
        Send a chat completion request to the provider.

        Args:
            payload: The request payload (OpenAI-compatible format)

        Returns:
            Tuple of (response_data, status_code)
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name for logging."""
        pass


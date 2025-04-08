import httpx
from typing import Dict, Any, List, Optional
from .base import BaseLLMService, LLMResponse
from ...core.config import get_settings

settings = get_settings()

class AnthropicService(BaseLLMService):
    """Service for Anthropic Claude models"""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1"
        self.default_model = "claude-3-sonnet-20240229"

    async def generate_response(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """
        Generate a response from an Anthropic Claude model

        Args:
            prompt: The user prompt to send to the model
            options: Optional configuration parameters
                - model: Model name (defaults to claude-3-sonnet-20240229)
                - max_tokens: Maximum tokens to generate (default: 1024)
                - temperature: Sampling temperature (default: 0.7)

        Returns:
            A standardized LLMResponse object
        """
        options = options or {}
        model = options.get("model", self.default_model)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": options.get("max_tokens", 1024),
                    "temperature": options.get("temperature", 0.7)
                },
                timeout=30.0
            )

            response.raise_for_status()
            result = response.json()

            return LLMResponse(
                text=result["content"][0]["text"],
                model_info={
                    "provider": "anthropic",
                    "model": model,
                    "version": "latest"
                },
                metadata={
                    "usage": {
                        "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": result.get("usage", {}).get("output_tokens", 0)
                    },
                    "id": result.get("id", "")
                },
                raw=result
            )

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available Anthropic models"""
        return [
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "provider": "anthropic", "description": "Fastest and most compact Claude model"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "provider": "anthropic", "description": "Balanced model for most tasks"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic", "description": "Most powerful Claude model for complex tasks"}
        ]
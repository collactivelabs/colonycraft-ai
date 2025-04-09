import httpx
from typing import Dict, Any, List, Optional
from .base import BaseLLMService, LLMResponse
from ...core.config import get_settings

settings = get_settings()

class OpenAIService(BaseLLMService):
    """Service for OpenAI models"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.default_model = "gpt-4o"

    async def generate_response(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """
        Generate a response from an OpenAI model

        Args:
            prompt: The user prompt to send to the model
            options: Optional configuration parameters
                - model: Model name (defaults to gpt-4o)
                - max_tokens: Maximum tokens to generate (default: 1024)
                - temperature: Sampling temperature (default: 0.7)

        Returns:
            A standardized LLMResponse object
        """
        options = options or {}
        model = options.get("model", self.default_model)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
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
                text=result["choices"][0]["message"]["content"],
                model_info={
                    "provider": "openai",
                    "model": model,
                    "version": "latest"
                },
                metadata={
                    "usage": result.get("usage", {}),
                    "id": result.get("id", "")
                },
                raw=result
            )

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available OpenAI models"""
        return [
            {"id": "gpt-4", "name": "GPT-4", "provider": "openai", "description": "Most capable GPT-4 model"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "description": "Most capable GPT-4o model"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai", "description": "More efficient version of GPT-4"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai", "description": "Efficient model balancing cost and capability"}
        ]
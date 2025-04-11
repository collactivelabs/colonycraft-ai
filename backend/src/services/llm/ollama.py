import httpx
from typing import Dict, Any, List, Optional

from .base import BaseLLMService, LLMResponse
from ...core.config import get_settings
from ...core.exceptions import ServiceUnavailableError, LLMIntegrationError
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class OllamaService(BaseLLMService):
    """Service integration for Ollama LLMs"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', settings.OLLAMA_BASE_URL)
        # Use httpx.AsyncClient for async requests
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0) # Increased timeout for potentially long generations

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Helper method to make requests to Ollama API."""
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()  # Raise exception for 4xx or 5xx status codes
            return response.json()
        except httpx.HTTPStatusError as e:
            # Log the error details
            logger.error(f"Ollama API request failed: {e.response.status_code} - {e.response.text}")
            raise LLMIntegrationError(f"Ollama API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            # Log the error details
            logger.error(f"Could not connect to Ollama: {e}")
            raise ServiceUnavailableError(f"Could not connect to Ollama at {self.base_url}") from e

    async def generate_response(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """Generate a response from an Ollama model."""
        if options is None:
            options = {}

        model = options.get("model", "llama3.2") # Default to llama3.2 if no model specified
        request_payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,  # For simplicity, start with non-streaming
            "options": options.get("parameters", {}) # Pass other Ollama parameters if provided
        }

        try:
            ollama_response = await self._make_request("POST", "/api/generate", json=request_payload)

            # Basic parsing, adjust based on actual Ollama response structure
            response_text = ollama_response.get("response", "").strip()
            model_info = {"provider": "ollama", "model_name": ollama_response.get("model", model)}
            metadata = {
                "created_at": ollama_response.get("created_at"),
                "done": ollama_response.get("done"),
                "total_duration": ollama_response.get("total_duration"),
                "load_duration": ollama_response.get("load_duration"),
                "prompt_eval_count": ollama_response.get("prompt_eval_count"),
                "eval_count": ollama_response.get("eval_count"),
            }

            return LLMResponse(
                text=response_text,
                model_info=model_info,
                metadata=metadata,
                raw=ollama_response
            )
        except (ServiceUnavailableError, LLMIntegrationError) as e:
            # Re-raise specific errors for upstream handling
            raise e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error during Ollama generation: {e}")
            raise LLMIntegrationError(f"Unexpected error interacting with Ollama: {str(e)}") from e


    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available models from Ollama."""
        try:
            response_data = await self._make_request("GET", "/api/tags")
            models = response_data.get("models", [])
            # Format to match expected structure, e.g., [{"id": "model_name", "name": "Model Name"}]
            # Adjust based on desired frontend display format
            return [{"id": model.get("name"), "name": model.get("name")} for model in models]
        except (ServiceUnavailableError, LLMIntegrationError) as e:
            # Log and return empty list or re-raise, depending on desired handling
            logger.error(f"Failed to get Ollama models: {e}")
            return [] # Return empty list if models can't be fetched
        except Exception as e:
            logger.error(f"Unexpected error fetching Ollama models: {e}")
            return []

    async def close(self):
        """Close the httpx client."""
        await self.client.aclose()

# Example Usage (optional, for testing)
# async def main():
#     ollama_service = OllamaService()
#     try:
#         models = await ollama_service.get_available_models()
#         print("Available Models:", models)
#         if models:
#             response = await ollama_service.generate_response("Why is the sky blue?", options={"model": models[0]['id']})
#             print("\nResponse:", response)
#     finally:
#         await ollama_service.close()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

import httpx
from typing import Optional, Dict, Any, List

from ...core.config import get_settings
from .base import BaseLLMService, LLMResponse
from ...core.exceptions import ServiceUnavailableError, LLMIntegrationError, AuthenticationError
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class MistralService(BaseLLMService):
    """Service integration for Mistral AI LLMs"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = getattr(settings, 'MISTRAL_API_KEY', settings.MISTRAL_API_KEY)
        self.base_url = getattr(settings, 'MISTRAL_API_BASE_URL', settings.MISTRAL_API_BASE_URL)

        if not self.api_key:
            raise AuthenticationError("Mistral API key not configured. Set MISTRAL_API_KEY environment variable.")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=60.0
        )

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Helper method to make requests to Mistral API."""
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                 raise AuthenticationError(f"Mistral API authentication failed: {e.response.text}")
            print(f"Mistral API request failed: {e.response.status_code} - {e.response.text}")
            raise LLMIntegrationError(f"Mistral API error: {e.response.status_code} - {e.response.text}") from e
        except httpx.RequestError as e:
            print(f"Could not connect to Mistral API: {e}")
            raise ServiceUnavailableError(f"Could not connect to Mistral API at {settings.MISTRAL_API_BASE_URL}") from e

    async def generate_response(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """Generate a response from a Mistral model."""
        if options is None:
            options = {}

        model = options.get("model", "mistral-small-latest") # Default model
        messages = options.get("messages", [{"role": "user", "content": prompt}]) # Allow passing full message history

        # Ensure the last message is the user prompt if only prompt is given
        if not options.get("messages"):
            messages = [{"role": "user", "content": prompt}]

        request_payload = {
            "model": model,
            "messages": messages,
            "temperature": options.get("temperature", 0.7),
            "max_tokens": options.get("max_tokens", None), # Let API use default if not specified
            "top_p": options.get("top_p", 1.0),
            "stream": False, # Keep it simple for now
            "safe_prompt": options.get("safe_prompt", False)
        }

        # Remove None values from payload as Mistral API might not like them
        request_payload = {k: v for k, v in request_payload.items() if v is not None}

        logger.info(f"Mistral payload configured: {request_payload}")

        try:
            mistral_response = await self._make_request(
                "POST",
                "/chat/completions",
                json=request_payload
            )

            response_text = ""
            if mistral_response.get("choices") and len(mistral_response["choices"]) > 0:
                response_text = mistral_response["choices"][0].get("message", {}).get("content", "").strip()

            model_info = {"provider": "mistral", "model_name": mistral_response.get("model", model)}
            metadata = {
                 "usage": mistral_response.get("usage"), # {prompt_tokens, completion_tokens, total_tokens}
                 "finish_reason": mistral_response["choices"][0].get("finish_reason") if mistral_response.get("choices") else None
            }


            return LLMResponse(
                text=response_text,
                model_info=model_info,
                metadata=metadata,
                raw=mistral_response
            )
        except (ServiceUnavailableError, LLMIntegrationError, AuthenticationError) as e:
            raise e
        except Exception as e:
            print(f"Unexpected error during Mistral generation: {e}")
            raise LLMIntegrationError(f"Unexpected error interacting with Mistral: {str(e)}") from e

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of known available Mistral models.
           Note: Mistral API does not have a dedicated models endpoint as of now.
           Returning a hardcoded list based on common models.
        """
        # TODO: Potentially fetch this dynamically if Mistral adds an endpoint
        return [
            {"id": "mistral-small-latest", "name": "Mistral Small (Latest)", "provider": "mistral"},
            {"id": "mistral-medium-latest", "name": "Mistral Medium (Latest)", "provider": "mistral"},
            {"id": "mistral-large-latest", "name": "Mistral Large (Latest)", "provider": "mistral"},
            # Add specific dated versions if needed, e.g.:
            # {"id": "mistral-medium-2312", "name": "Mistral Medium (2312)", "provider": "mistral"},
        ]

    async def close(self):
        """Close the httpx client."""
        await self.client.aclose()


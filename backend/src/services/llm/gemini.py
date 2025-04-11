"""
Service integration for Google Gemini models.
"""
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from typing import Optional, Dict, Any, List
from .base import BaseLLMService, LLMResponse
from ...core.exceptions import AuthenticationError, ServiceUnavailableError, InvalidInputError,LLMIntegrationError
from ...core.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class GeminiService(BaseLLMService):
    """Service integration for Google Gemini LLMs"""

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', settings.GEMINI_API_KEY)
        if not self.api_key:
            raise AuthenticationError("Google API Key not configured. Set GEMINI_API_KEY environment variable.")
        
        try:
            genai.configure(api_key=self.api_key)
            # Optional: Add client options if needed, e.g., client_options={"api_endpoint": ...}
        except Exception as e:
            # Catch potential configuration errors
            raise AuthenticationError(f"Failed to configure Google Gemini SDK: {e}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available Google Gemini models."""
        # Currently, the python SDK doesn't easily expose structured info
        # like context window size. Hardcoding known/supported models.
        # TODO: Explore ways to get more model details dynamically if needed
        return [
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
            # Add other models like gemini-pro (older) if desired
            # {"id": "gemini-pro", "name": "Gemini Pro"}
        ]

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Gemini models."""
        try:
            models_list = []
            # Note: genai.list_models() returns an iterator
            for m in genai.list_models():
                # Filter for models usable with the generateContent method
                if 'generateContent' in m.supported_generation_methods:
                    models_list.append({
                        "id": m.name.split('/')[-1],  # Extract simple name like 'gemini-1.5-flash'
                        "name": m.display_name,
                        "description": m.description,
                        "provider": "google" 
                    })
            return models_list
        except google_exceptions.PermissionDenied as e:
             raise AuthenticationError(f"Google API Key is invalid or lacks permissions: {e}")
        except google_exceptions.GoogleAPIError as e:
            raise ServiceUnavailableError("google", f"Could not connect to Google API to list models: {e}")
        except Exception as e:
            raise LLMIntegrationError("google", f"An unexpected error occurred while listing Google models: {e}")

    async def generate_response(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """Generate a response from a Gemini model."""
        opts = options or {}
        model_name = opts.get("model", "gemini-1.5-flash") # Default model
        # Ensure the model name doesn't include the 'models/' prefix if passed from frontend
        if model_name.startswith("models/"):
            model_name = model_name.split('/')[-1]
            
        # Map common options to Gemini's GenerationConfig if needed
        # Example: opts.get("temperature"), opts.get("max_tokens" -> max_output_tokens)
        generation_config = genai.types.GenerationConfig(
            # candidate_count=1, # Default
            # stop_sequences=[...],
            max_output_tokens=opts.get("max_tokens", 2048), # Example mapping
            temperature=opts.get("temperature", 0.7), # Example mapping
            # top_p=...,
            # top_k=...
        )
        
        # Safety settings (adjust as needed)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        try:
            model = genai.GenerativeModel(
                model_name=f'models/{model_name}',
                generation_config=generation_config,
                safety_settings=safety_settings
                # system_instruction=opts.get("system_prompt") # If you add system prompt support
            )
            
            # Simple text generation for now
            response = await model.generate_content_async(prompt)

            # Error handling for blocked prompts or empty responses
            if not response.candidates:
                 # Check prompt_feedback for block reason
                 block_reason = response.prompt_feedback.block_reason.name if response.prompt_feedback else "Unknown"
                 raise InvalidInputError(
                     message=f"Request blocked by Google's safety filters. Reason: {block_reason}",
                     details={"block_reason": block_reason}
                 )

            # Assuming the first candidate is the primary response
            candidate = response.candidates[0]
            
            # Check finish reason (e.g., SAFETY, MAX_TOKENS)
            finish_reason = candidate.finish_reason.name if candidate.finish_reason else "Unknown"
            if finish_reason == "SAFETY":
                 raise LLMIntegrationError("google", "Response blocked by Google's safety filters.", details={"finish_reason": finish_reason})

            text_content = "".join(part.text for part in candidate.content.parts) if candidate.content and candidate.content.parts else ""

            # Extract usage metadata if available (may require specific API calls or might be inferred)
            # Gemini API v1 doesn't directly return token counts like OpenAI/Anthropic in the generate_content response.
            # You might need to use model.count_tokens() separately before/after or estimate.
            # For now, we'll return placeholder/null values.
            usage_metadata = {
                 "input_tokens": None, # Placeholder
                 "output_tokens": None, # Placeholder
                 # "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None
            }
             
            return LLMResponse(
                text=text_content,
                model_info={
                    "provider": "google",
                    "model": model_name
                },
                metadata={
                    "finish_reason": finish_reason,
                    "safety_ratings": [rating.to_dict() for rating in candidate.safety_ratings] if candidate.safety_ratings else [],
                    "usage": usage_metadata,
                    "id": response._result.request_id if hasattr(response._result, 'request_id') else None # Attempt to get some ID
                }
            )

        except google_exceptions.InvalidArgument as e:
             raise InvalidInputError(f"Invalid argument provided to Google API: {e}", details={"error_details": str(e)})
        except google_exceptions.PermissionDenied as e:
             raise AuthenticationError(f"Google API Key is invalid or lacks permissions for model {model_name}: {e}")
        except google_exceptions.ResourceExhausted as e:
             # Could be rate limiting or quota issue
             raise ServiceUnavailableError("google", f"Google API quota exceeded or rate limit hit: {e}")
        except google_exceptions.GoogleAPIError as e:
            # Catch other specific Google API errors
            status_code = e.code if hasattr(e, 'code') else 503
            raise LLMIntegrationError("google", f"Google API error: {e}", status_code=status_code, details={"error_details": str(e)})
        except Exception as e:
            # Catch-all for unexpected errors during generation
            raise LLMIntegrationError("google", f"An unexpected error occurred during Google generation: {e}")

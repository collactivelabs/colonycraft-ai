from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class LLMResponse(BaseModel):
    """Standardized response from LLM services"""
    text: str
    model_info: Dict[str, str]
    metadata: Dict[str, Any]
    raw: Dict[str, Any] = {}

class BaseLLMService(ABC):
    """Base class for all LLM service integrations"""

    @abstractmethod
    async def generate_response(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """Generate a response from an LLM model"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available models for this service"""
        pass

class LLMServiceFactory:
    """Factory class to get the appropriate LLM service"""

    @staticmethod
    def get_service(provider: str) -> BaseLLMService:
        """
        Get the LLM service for the specified provider

        Args:
            provider: The LLM provider name (e.g., 'anthropic', 'openai', 'ollama', 'mistral', 'google')

        Returns:
            An instance of the appropriate LLM service

        Raises:
            ValueError: If the provider is not supported
        """
        if provider.lower() == "anthropic":
            from .anthropic import AnthropicService
            return AnthropicService()
        elif provider.lower() == "openai":
            from .openai import OpenAIService
            return OpenAIService()
        elif provider.lower() == "ollama": 
            from .ollama import OllamaService
            return OllamaService()
        elif provider.lower() == "mistral": 
            from .mistral import MistralService
            return MistralService()
        elif provider.lower() == "google":  
            from .gemini import GeminiService
            return GeminiService()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
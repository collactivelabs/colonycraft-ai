from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import asyncio
from src.tasks.response_caching import cache_response, retrieve_from_cache
from src.core.optimizations.circuit_breaker import circuit_protected, CircuitOpenError
from src.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class LLMResponse(BaseModel):
    """Standardized response from LLM services"""
    text: str
    model_info: Dict[str, str]
    metadata: Dict[str, Any]
    raw: Dict[str, Any] = {}

class BaseLLMService(ABC):
    """Base class for all LLM service integrations"""

    def __init__(self):
        self.use_caching = True  # Enable/disable caching
        self.cache_ttl = 3600  # Default cache TTL (1 hour)

    @abstractmethod
    async def generate_response(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> LLMResponse:
        """Generate a response from an LLM model"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available models for this service"""
        pass
        
    async def _generate_with_caching(
        self, 
        prompt: str, 
        options: Optional[Dict[str, Any]] = None,
        provider: str = "unknown"
    ) -> LLMResponse:
        """
        Generate response with caching support
        
        Args:
            prompt: The prompt to send
            options: Additional parameters
            provider: Provider name for cache key
            
        Returns:
            LLM response
        """
        options = options or {}
        model = options.get("model", "unknown")
        
        # Try to get from cache first
        if self.use_caching:
            cached_response = await asyncio.to_thread(
                retrieve_from_cache,
                provider=provider,
                model=model,
                prompt=prompt,
                options=options
            )
            
            if cached_response:
                logger.info(f"Cache hit for {provider}/{model}")
                return cached_response
        
        # Generate new response
        response = await self._generate_response_impl(prompt, options)
        
        # Cache the response
        if self.use_caching:
            await asyncio.to_thread(
                cache_response,
                provider=provider,
                model=model,
                prompt=prompt,
                response_data=response.dict(),
                options=options,
                ttl=self.cache_ttl
            )
        
        return response
    
    @circuit_protected(name="llm_api_call", failure_threshold=5, recovery_timeout=60)
    async def _generate_response_impl(
        self, 
        prompt: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Actual implementation of generate_response with circuit breaker
        
        Args:
            prompt: The prompt to send
            options: Additional parameters
            
        Returns:
            LLM response
        """
        # This will be overridden by child classes
        raise NotImplementedError("Subclasses must implement this method")

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

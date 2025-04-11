from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from ....services.llm.base import LLMServiceFactory, LLMResponse
from ....core.auth import get_current_user
from ....models.user import User
from ....core.optimizations.request_batching import batch_requests
from ....core.optimizations.circuit_breaker import CircuitOpenError
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(tags=["LLM"])

class LLMRequest(BaseModel):
    provider: str
    model: str
    prompt: str
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProviderInfo(BaseModel):
    name: str
    models: List[Dict[str, Any]]

@router.post("/generate", response_model=LLMResponse)
async def generate_response(
    request: LLMRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a response from an LLM provider
    """
    try:
        service = LLMServiceFactory.get_service(request.provider)

        # Add any user-specific options or limitations
        options = request.options.copy() if request.options else {}
        options["user_id"] = str(current_user.id)
        options["model"] = request.model

        # Log the request
        logger.info(
            f"LLM request: user={current_user.email}, provider={request.provider}, "
            f"model={request.model}, prompt_length={len(request.prompt)}"
        )

        # Generate response
        response = await service.generate_response(
            prompt=request.prompt,
            options=options
        )

        # Log response stats
        logger.info(
            f"LLM response: user={current_user.email}, provider={request.provider}, "
            f"model={request.model}, input_tokens={response.metadata.get('usage', {}).get('input_tokens', 0)}, "
            f"output_tokens={response.metadata.get('usage', {}).get('output_tokens', 0)}"
        )

        return response
    except CircuitOpenError as e:
        logger.warning(f"Circuit breaker open: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service temporarily unavailable: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in LLM request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM service error: {str(e)}")

@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(
    current_user: User = Depends(get_current_user)
):
    """
    List all available LLM providers and their models
    """
    try:
        # Define provider names
        provider_names = ["anthropic", "openai", "ollama", "mistral", "google"] 
        providers = []

        # Use asyncio.gather to fetch all models concurrently
        async def get_provider_info(name):
            try:
                service = LLMServiceFactory.get_service(name)
                if hasattr(service, 'get_available_models') and asyncio.iscoroutinefunction(service.get_available_models):
                    models = await service.get_available_models() 
                elif hasattr(service, 'get_available_models'):
                    models = service.get_available_models() 
                else:
                    models = [] 
                    logger.warning(f"Provider {name} service missing get_available_models method.")
                
                return {"name": name, "models": models}
            except Exception as e:
                logger.error(f"Error fetching models for provider {name}: {e}")
                return {"name": name, "models": []}
        
        # Execute all provider info fetches concurrently
        provider_results = await asyncio.gather(*[
            get_provider_info(name) for name in provider_names
        ])
        
        return provider_results
    except Exception as e:
        logger.error(f"Error listing providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing providers: {str(e)}")

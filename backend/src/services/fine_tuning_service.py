from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from src.schemas.fine_tuning import FineTuningJob, FineTuningJobCreate, FineTuningModel
from src.core.config import settings
from openai import OpenAI, OpenAIError

def _openai_ts_to_datetime(timestamp: Optional[int]) -> Optional[datetime]:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

class FineTuningService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        if not self.openai_client:
            print("Warning: OpenAI API key not configured. OpenAI fine-tuning will not be available.")

    async def create_job(self, job_in: FineTuningJobCreate, user_id: Optional[int] = None) -> FineTuningJob:
        provider = self._get_provider_for_model(job_in.model)
        print(f"Attempting to create fine-tuning job for model {job_in.model} with provider {provider}")

        if provider == "openai" and self.openai_client:
            try:
                openai_hyperparams = job_in.hyperparameters or {}
                response = self.openai_client.fine_tuning.jobs.create(
                    model=job_in.model,
                    training_file=job_in.training_file_id,
                    validation_file=job_in.validation_file_id,
                    hyperparameters=openai_hyperparams if openai_hyperparams else None,
                )
                print(f"OpenAI fine-tuning job creation response: {response.id}")
                created_job = self._map_openai_response_to_schema(response, provider, user_id)
            except OpenAIError as e:
                print(f"OpenAI API error during job creation: {e}")
                raise HTTPException(status_code=e.status_code or 500, detail=f"OpenAI API error: {e.message or str(e)}")
            except Exception as e:
                print(f"Unexpected error during OpenAI job creation: {e}")
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

        elif provider == "google_unsupported_ft":
            print("Google provider not yet implemented for fine-tuning.")
            raise HTTPException(status_code=501, detail="Google fine-tuning not implemented")
        else:
            print(f"Unsupported provider '{provider}' for model {job_in.model}")
            raise HTTPException(status_code=400, detail=f"Unsupported provider for model {job_in.model}")

        return created_job

    async def list_jobs(self, user_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[FineTuningJob]:
        all_jobs: List[FineTuningJob] = []

        if self.openai_client:
            try:
                print(f"Listing OpenAI fine-tuning jobs (limit={limit})")
                response = self.openai_client.fine_tuning.jobs.list(limit=limit)
                openai_jobs = [
                    self._map_openai_response_to_schema(job, "openai", user_id)
                    for job in response.data
                ]
                all_jobs.extend(openai_jobs)
                print(f"Found {len(openai_jobs)} OpenAI jobs.")
            except OpenAIError as e:
                print(f"OpenAI API error during job listing: {e}")
            except Exception as e:
                print(f"Unexpected error during OpenAI job listing: {e}")

        return all_jobs[skip : skip + limit]

    async def get_job(self, job_id: str, user_id: Optional[int] = None) -> Optional[FineTuningJob]:
        provider = "openai"
        print(f"Retrieving fine-tuning job {job_id} (assuming provider: {provider})")

        if provider == "openai" and self.openai_client:
            try:
                response = self.openai_client.fine_tuning.jobs.retrieve(job_id)
                return self._map_openai_response_to_schema(response, provider, user_id)
            except OpenAIError as e:
                print(f"OpenAI API error retrieving job {job_id}: {e}")
                if e.status_code == 404:
                    return None
                raise HTTPException(status_code=e.status_code or 500, detail=f"OpenAI API error: {e.message or str(e)}")
            except Exception as e:
                print(f"Unexpected error retrieving OpenAI job {job_id}: {e}")
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

        return None

    async def cancel_job(self, job_id: str, user_id: Optional[int] = None) -> bool:
        provider = "openai"
        print(f"Cancelling fine-tuning job {job_id} (assuming provider: {provider})")

        if provider == "openai" and self.openai_client:
            try:
                response = self.openai_client.fine_tuning.jobs.cancel(job_id)
                print(f"OpenAI cancel response status for job {job_id}: {response.status}")
                return response.status in ["cancelled", "cancelling"]
            except OpenAIError as e:
                print(f"OpenAI API error cancelling job {job_id}: {e}")
                return False
            except Exception as e:
                print(f"Unexpected error cancelling OpenAI job {job_id}: {e}")
                return False

        return False

    async def list_models(self, user_id: Optional[int] = None) -> List[FineTuningModel]:
        models: List[FineTuningModel] = []

        openai_base_models_ids = [
            "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo-1106",
        ]
        for model_id in openai_base_models_ids:
            models.append(FineTuningModel(
                id=model_id,
                provider="openai",
                is_base_model=True,
                is_fine_tuned=False,
                base_model_id=None,
                created_at=None
            ))

        return models

    def _get_provider_for_model(self, model_id: str) -> str:
        model_id_lower = model_id.lower()
        if model_id_lower.startswith("gpt-") or "davinci" in model_id_lower or "babbage" in model_id_lower or "curie" in model_id_lower or "ada" in model_id_lower:
            return "openai"
        elif model_id_lower.startswith("gemini-"):
            return "google_unsupported_ft"
        else:
            print(f"Warning: Could not determine provider for model '{model_id}'. Defaulting to 'unknown'.")
            return "unknown"

    def _map_openai_response_to_schema(self, response: Any, provider: str, user_id: Optional[int]) -> FineTuningJob:
        hyperparams_data = response.hyperparameters if hasattr(response, 'hyperparameters') and response.hyperparameters else {}
        error_data = None
        if hasattr(response, 'error') and response.error:
            error_data = {
                'code': getattr(response.error, 'code', None),
                'message': getattr(response.error, 'message', None),
                'param': getattr(response.error, 'param', None)
            }

        return FineTuningJob(
            id=response.id,
            model=response.model,
            training_file_id=response.training_file,
            validation_file_id=getattr(response, 'validation_file', None),
            hyperparameters=hyperparams_data,
            status=response.status,
            created_at=_openai_ts_to_datetime(response.created_at),
            finished_at=_openai_ts_to_datetime(getattr(response, 'finished_at', None)),
            fine_tuned_model_id=response.fine_tuned_model,
            error=error_data,
            provider=provider,
            user_id=user_id,
        )

fine_tuning_service = FineTuningService()

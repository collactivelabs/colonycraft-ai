from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any, Dict

from src.schemas.fine_tuning import (
    FineTuningJob,
    FineTuningJobCreate,
    FineTuningModel,
)
from src.services.fine_tuning_service import fine_tuning_service

router = APIRouter()

@router.post("/jobs", response_model=FineTuningJob, status_code=status.HTTP_201_CREATED)
async def create_fine_tuning_job(
    *,
    job_in: FineTuningJobCreate,
) -> Any:
    """Create a new fine-tuning job."""
    user_id = None 
    try:
        created_job = await fine_tuning_service.create_job(job_in=job_in, user_id=user_id)
        return created_job
    except Exception as e:
        print(f"Error creating fine-tuning job: {e}") 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create fine-tuning job: {e}")

@router.get("/jobs", response_model=List[FineTuningJob], status_code=status.HTTP_200_OK)
async def list_fine_tuning_jobs(
    *,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve fine-tuning jobs."""
    user_id = None 
    jobs = await fine_tuning_service.list_jobs(user_id=user_id, skip=skip, limit=limit)
    return jobs

@router.get("/jobs/{job_id}", response_model=FineTuningJob, status_code=status.HTTP_200_OK)
async def get_fine_tuning_job(
    job_id: str
) -> Any:
    """Get status of a specific fine-tuning job."""
    user_id = None 
    job = await fine_tuning_service.get_job(job_id=job_id, user_id=user_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine-tuning job not found")
    return job

@router.delete("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def delete_fine_tuning_job(
    job_id: str
) -> Dict[str, str]:
    """Cancel a running fine-tuning job."""
    user_id = None 
    success = await fine_tuning_service.cancel_job(job_id=job_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine-tuning job not found or cannot be cancelled")
    return {"message": f"Fine-tuning job {job_id} cancellation initiated"}

@router.get("/models", response_model=List[FineTuningModel], status_code=status.HTTP_200_OK)
async def list_fine_tunable_models(
) -> Any:
    """List available fine-tunable base models or completed fine-tuned models."""
    user_id = None 
    models = await fine_tuning_service.list_models(user_id=user_id)
    return models

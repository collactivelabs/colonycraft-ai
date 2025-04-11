from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# Base model for shared properties
class FineTuningJobBase(BaseModel):
    model: str = Field(..., description="The base model to fine-tune.")
    training_file_id: str = Field(..., description="ID of the uploaded training file.")
    validation_file_id: Optional[str] = Field(None, description="ID of the uploaded validation file (optional).")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="Provider-specific hyperparameters.")

# Schema for creating a new job (request body for POST /jobs)
class FineTuningJobCreate(FineTuningJobBase):
    pass

# Schema for representing a job in the database/response
class FineTuningJob(FineTuningJobBase):
    id: str = Field(..., description="Unique identifier for the fine-tuning job (provider-specific).")
    status: str = Field(..., description="Current status of the job (e.g., pending, running, succeeded, failed, cancelled).")
    created_at: datetime = Field(..., description="Timestamp when the job was created.")
    finished_at: Optional[datetime] = Field(None, description="Timestamp when the job finished (if applicable).")
    fine_tuned_model_id: Optional[str] = Field(None, description="ID of the resulting fine-tuned model (if successful).")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if the job failed.")
    provider: str = Field(..., description="The LLM provider handling the job (e.g., openai, google).")
    user_id: Optional[int] = Field(None, description="ID of the user who initiated the job.") # Assuming association with users

    class Config:
        orm_mode = True # For compatibility with SQLAlchemy models

# Schema for listing jobs (response for GET /jobs)
class FineTuningJobList(BaseModel):
    jobs: list[FineTuningJob]
    total_count: int

# Schema for representing a model available for fine-tuning or a completed fine-tuned model
class FineTuningModel(BaseModel):
    id: str = Field(..., description="Model identifier.")
    provider: str = Field(..., description="The LLM provider for this model.")
    is_base_model: bool = Field(..., description="True if this is a base model available for fine-tuning.")
    is_fine_tuned: bool = Field(..., description="True if this is a successfully fine-tuned model.")
    base_model_id: Optional[str] = Field(None, description="ID of the base model if this is a fine-tuned model.")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the fine-tuned model was created.")
    # Add other relevant model details as needed

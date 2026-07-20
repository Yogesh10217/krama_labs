import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.domain.enums import JobType, JobStatus, JobStageStatus
from app.schemas.common import PaginatedResponse

class JobStageResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    stage_name: str
    status: JobStageStatus
    sequence: int
    progress: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobBase(BaseModel):
    claim_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    job_type: JobType

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    status: JobStatus
    progress: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

JobListResponse = PaginatedResponse[JobResponse]

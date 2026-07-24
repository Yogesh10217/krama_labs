"""
app/schemas/job_execution.py — Phase 10 Pydantic schemas for the async job API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class JobEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_execution_id: str
    event_type: str
    message: Optional[str] = None
    stage_name: Optional[str] = None
    progress: Optional[int] = None
    correlation_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime


class JobRetrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_execution_id: str
    attempt: int
    stage_name: Optional[str] = None
    reason: Optional[str] = None
    backoff_seconds: Optional[float] = None
    correlation_id: Optional[str] = None
    created_at: datetime


class JobExecutionCreate(BaseModel):
    document_id: Optional[str] = None
    job_type: str = "DOCUMENT_PROCESSING"
    priority: int = 0
    correlation_id: Optional[str] = None


class JobExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    document_id: Optional[str] = None
    job_type: str
    status: str
    priority: int
    worker_id: Optional[str] = None
    queue_name: str
    last_heartbeat_at: Optional[datetime] = None
    retry_count: int
    max_retries: int
    progress: int
    current_stage: Optional[str] = None
    last_successful_stage: Optional[str] = None
    last_success_timestamp: Optional[datetime] = None
    checkpoint_version: int
    correlation_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class JobExecutionDetail(JobExecutionResponse):
    events: List[JobEventSchema] = []
    retries: List[JobRetrySchema] = []


class CancelJobResponse(BaseModel):
    job_execution_id: str
    cancelled: bool
    message: str


class QueueHealthResponse(BaseModel):
    provider: str
    is_healthy: bool
    approximate_size: int
    details: Dict[str, Any] = {}

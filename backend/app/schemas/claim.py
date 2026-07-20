import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.domain.enums import ClaimStatus, ClaimPriority
from app.schemas.common import PaginatedResponse

class ClaimBase(BaseModel):
    external_reference: Optional[str] = None
    claim_type: Optional[str] = None
    priority: Optional[ClaimPriority] = ClaimPriority.NORMAL
    title: Optional[str] = None
    description: Optional[str] = None

class ClaimCreate(ClaimBase):
    pass

class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatus] = None
    priority: Optional[ClaimPriority] = None
    title: Optional[str] = None
    description: Optional[str] = None

class ClaimResponse(ClaimBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    status: ClaimStatus
    created_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClaimDetailResponse(ClaimResponse):
    # Documents and jobs would be linked here
    # Using generic placeholders, they will be loaded properly via API
    pass

ClaimListResponse = PaginatedResponse[ClaimResponse]

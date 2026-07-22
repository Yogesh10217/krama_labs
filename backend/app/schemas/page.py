import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.domain.enums import PageStatus, DocumentStatus


class PageResponse(BaseModel):
    """Schema representing page metadata."""

    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    width: Optional[int] = None
    height: Optional[int] = None
    status: PageStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PageListResponse(BaseModel):
    """Schema representing a list of pages."""

    pages: List[PageResponse]


class ConversionResponse(BaseModel):
    """Schema representing the result of document conversion."""

    document_id: uuid.UUID
    status: DocumentStatus
    page_count: int
    pages: List[PageResponse]

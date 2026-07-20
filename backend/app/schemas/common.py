from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")

class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationMetadata

class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str

class ErrorResponse(BaseModel):
    error: ErrorDetail

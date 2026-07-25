import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.security.apikey import create_api_key, revoke_api_key, rotate_api_key
from app.security.dependencies import Principal, require_permission
from app.security.rbac import Permission
from pydantic import BaseModel

router = APIRouter(prefix="/apikeys", tags=["apikeys"])

class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: List[str]
    expires_in_days: Optional[int] = 30

class APIKeyCreateResponse(BaseModel):
    id: uuid.UUID
    name: str
    raw_key: str
    scopes: str

@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_new_api_key(
    request: APIKeyCreateRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission(Permission.ADMIN_ALL))
):
    """Create a new API Key for the organization."""
    raw_key, db_key = create_api_key(
        user_id=principal.user_id,
        org_id=principal.organization_id,
        name=request.name,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days,
        db=db
    )
    return APIKeyCreateResponse(
        id=db_key.id,
        name=db_key.name,
        raw_key=raw_key,
        scopes=db_key.scopes
    )

@router.post("/{key_id}/revoke")
def revoke_existing_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission(Permission.ADMIN_ALL))
):
    """Revokes an API Key."""
    revoke_api_key(key_id, db)
    return {"message": "API key revoked"}

@router.post("/{key_id}/rotate", response_model=APIKeyCreateResponse)
def rotate_existing_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission(Permission.ADMIN_ALL))
):
    """Rotates an API Key."""
    new_raw, new_key = rotate_api_key(key_id, db)
    return APIKeyCreateResponse(
        id=new_key.id,
        name=new_key.name,
        raw_key=new_raw,
        scopes=new_key.scopes
    )

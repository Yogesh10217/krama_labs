import uuid
from typing import List, Optional
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import Config
from app.security.jwt import decode_token
from app.security.rbac import Permission, has_permission
from app.security.apikey import verify_api_key
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

@dataclass
class Principal:
    user_id: Optional[uuid.UUID]
    organization_id: Optional[uuid.UUID]
    role: str
    scopes: List[str]
    is_api_key: bool = False

def get_current_principal(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> Principal:
    """Extracts identity from either JWT or API Key."""
    
    if not Config.ENABLE_AUTH:
        # Development fallback
        org_id_str = request.headers.get("x-organization-id")
        org_id = uuid.UUID(org_id_str) if org_id_str else None
        return Principal(
            user_id=None,
            organization_id=org_id,
            role="SYSTEM_ADMIN",
            scopes=["*"]
        )
        
    if api_key:
        try:
            db_key = verify_api_key(api_key, db)
            scopes = db_key.scopes.split(",") if db_key.scopes != "*" else ["*"]
            return Principal(
                user_id=db_key.user_id,
                organization_id=db_key.organization_id,
                role="API_CLIENT",
                scopes=scopes,
                is_api_key=True
            )
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
                
            user_id = uuid.UUID(payload.get("sub"))
            org_id_str = payload.get("org_id")
            org_id = uuid.UUID(org_id_str) if org_id_str else None
            role = payload.get("role", "VIEWER")
            
            return Principal(
                user_id=user_id,
                organization_id=org_id,
                role=role,
                scopes=[],
                is_api_key=False
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_permission(permission: Permission):
    """Dependency generator to enforce RBAC permissions."""
    def permission_checker(principal: Principal = Depends(get_current_principal)):
        if not Config.ENABLE_AUTH:
            return principal
            
        if not has_permission(principal.role, permission, principal.scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission.value}"
            )
        return principal
    return permission_checker

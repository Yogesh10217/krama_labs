import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.security.auth import authenticate_user, create_user_tokens, revoke_refresh_token
from app.security.dependencies import get_current_principal, require_permission
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(request: TokenRequest, db: Session = Depends(get_db)):
    """OAuth2 compatible token login, returning access and refresh tokens."""
    try:
        user = authenticate_user(request.email, request.password, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token, refresh_token = create_user_tokens(str(user.id), db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh the access token using a valid refresh token."""
    from app.security.jwt import decode_token
    import jwt
    
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        
        user_id = payload.get("sub")
        # In a real app, also verify against DB to see if it's revoked
        access_token, new_refresh_token = create_user_tokens(user_id, db)
        # Optionally revoke the old refresh token
        revoke_refresh_token(request.refresh_token, db)
        
        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

@router.post("/revoke")
def revoke_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token."""
    revoke_refresh_token(request.refresh_token, db)
    return {"message": "Token revoked"}

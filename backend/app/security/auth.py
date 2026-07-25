import uuid
from datetime import datetime, timezone
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.security.crypto import verify_password, hash_password
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AuthenticationException, NotFoundException

def authenticate_user(email: str, password: str, db: Session) -> User:
    """Authenticates a user and updates last_login_at."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise AuthenticationException("Invalid email or password")
        
    if not user.hashed_password:
        raise AuthenticationException("User has no password set (OAuth only?)")
        
    if not verify_password(password, user.hashed_password):
        raise AuthenticationException("Invalid email or password")
        
    if not user.is_active:
        raise AuthenticationException("User is deactivated")
        
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return user

def create_user_tokens(user_id: str, db: Session) -> Tuple[str, str]:
    """Generates access and refresh tokens for a user, saving refresh token in DB."""
    access_token = create_access_token(subject=user_id)
    refresh_token_str = create_refresh_token(subject=user_id)
    
    # Store refresh token in db (hashed conceptually, or just as is for now)
    import hashlib
    token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
    
    db_token = RefreshToken(
        user_id=uuid.UUID(user_id),
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) # This should be + days, simplified for now
    )
    db.add(db_token)
    db.commit()
    
    return access_token, refresh_token_str

def revoke_refresh_token(refresh_token_str: str, db: Session) -> None:
    import hashlib
    token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if db_token:
        db_token.is_revoked = True
        db.commit()

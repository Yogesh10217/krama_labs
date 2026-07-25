from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
from dataclasses import dataclass
from app.core.config import Config

@dataclass
class TokenData:
    user_id: str
    org_id: Optional[str] = None
    role: Optional[str] = None
    scopes: List[str] = None
    token_type: str = "bearer"

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []

def create_access_token(
    subject: str, 
    extra_claims: dict = None, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a JWT access token."""
    to_encode = {"sub": subject, "type": "access"}
    if extra_claims:
        to_encode.update(extra_claims)
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=Config.JWT_ACCESS_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str) -> str:
    """Creates a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=Config.JWT_REFRESH_EXPIRE_DAYS)
    to_encode = {
        "sub": subject,
        "type": "refresh",
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    return jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])

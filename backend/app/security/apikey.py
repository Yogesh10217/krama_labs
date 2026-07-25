import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from app.db.models.api_key import APIKey
from app.security.crypto import generate_api_key, hash_api_key
from app.core.exceptions import NotFoundException, ValidationException

def create_api_key(
    user_id: uuid.UUID,
    org_id: Optional[uuid.UUID],
    name: str,
    scopes: List[str],
    expires_in_days: Optional[int],
    db: Session
) -> Tuple[str, APIKey]:
    """Creates a new API key and returns the raw key and DB model."""
    raw_key, key_hash = generate_api_key()
    
    expires_at = None
    if expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
    scopes_str = ",".join(scopes) if scopes else "*"
    
    db_key = APIKey(
        user_id=user_id,
        organization_id=org_id,
        key_prefix=raw_key[:10],
        key_hash=key_hash,
        name=name,
        scopes=scopes_str,
        expires_at=expires_at
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    return raw_key, db_key

def verify_api_key(raw_key: str, db: Session) -> APIKey:
    """Verifies an API key and returns the DB model if valid."""
    key_hash = hash_api_key(raw_key)
    db_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    
    if not db_key:
        raise NotFoundException("API Key not found or invalid", "INVALID_API_KEY")
        
    if db_key.is_revoked:
        raise ValidationException("API Key is revoked", "API_KEY_REVOKED")
        
    if db_key.expires_at and db_key.expires_at < datetime.now(timezone.utc):
        raise ValidationException("API Key is expired", "API_KEY_EXPIRED")
        
    db_key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    
    return db_key

def revoke_api_key(key_id: uuid.UUID, db: Session) -> None:
    """Revokes an API key."""
    db_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not db_key:
        raise NotFoundException("API Key not found")
        
    db_key.is_revoked = True
    db.commit()

def rotate_api_key(key_id: uuid.UUID, db: Session) -> Tuple[str, APIKey]:
    """Rotates an API key by generating a new one and revoking the old one."""
    old_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not old_key:
        raise NotFoundException("API Key not found")
        
    scopes_list = old_key.scopes.split(",") if old_key.scopes != "*" else ["*"]
    
    expires_in_days = None
    if old_key.expires_at:
        # Give it a new default 30 days or keep same duration? 
        # For simplicity, we just use 30 days for rotated keys if it had an expiry.
        expires_in_days = 30
        
    new_raw, new_key = create_api_key(
        user_id=old_key.user_id,
        org_id=old_key.organization_id,
        name=old_key.name + " (Rotated)",
        scopes=scopes_list,
        expires_in_days=expires_in_days,
        db=db
    )
    
    old_key.is_revoked = True
    db.commit()
    
    return new_raw, new_key

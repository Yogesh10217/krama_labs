import pytest
import uuid
from datetime import datetime, timedelta, timezone
from app.security.crypto import hash_password, verify_password, generate_api_key, hash_api_key, generate_secure_token
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.rbac import has_permission, Permission
from app.security.apikey import create_api_key, verify_api_key, revoke_api_key, rotate_api_key
from app.core.exceptions import AuthenticationException, NotFoundException, ValidationException
import jwt
from app.db.models.user import User

def test_password_hashing():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    
    assert password != hashed
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword!", hashed)

def test_api_key_generation():
    raw_key, key_hash = generate_api_key()
    assert raw_key.startswith("krama_")
    assert len(raw_key) > 20
    assert key_hash == hash_api_key(raw_key)

def test_secure_token():
    token = generate_secure_token()
    assert len(token) > 20

def test_jwt_access_token():
    user_id = str(uuid.uuid4())
    token = create_access_token(subject=user_id, extra_claims={"role": "ADMIN"})
    
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert payload["role"] == "ADMIN"
    assert "exp" in payload

def test_jwt_expired_token():
    user_id = str(uuid.uuid4())
    token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-1))
    
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)

def test_rbac_permissions():
    assert has_permission("SYSTEM_ADMIN", Permission.DOCUMENTS_READ)
    assert has_permission("SYSTEM_ADMIN", Permission.ADMIN_ALL)
    
    assert has_permission("OWNER", Permission.USERS_MANAGE)
    assert not has_permission("REVIEWER", Permission.USERS_MANAGE)
    assert has_permission("REVIEWER", Permission.REVIEW_APPROVE)
    
    assert not has_permission("VIEWER", Permission.DOCUMENTS_WRITE)
    assert has_permission("VIEWER", Permission.DOCUMENTS_READ)

def test_rbac_api_client():
    assert has_permission("API_CLIENT", Permission.DOCUMENTS_READ, scopes=["documents.read"])
    assert not has_permission("API_CLIENT", Permission.DOCUMENTS_WRITE, scopes=["documents.read"])
    assert has_permission("API_CLIENT", Permission.DOCUMENTS_WRITE, scopes=["*"])

# Add more tests that require DB later. For now, these basic unit tests cover the logic.

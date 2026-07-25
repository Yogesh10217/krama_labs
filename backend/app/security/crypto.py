import hashlib
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def generate_api_key() -> tuple[str, str]:
    """
    Generates a secure API key and its hash.
    Returns: (raw_key, key_hash)
    """
    prefix = secrets.token_urlsafe(8)[:10]
    secret = secrets.token_urlsafe(32)
    raw_key = f"krama_{prefix}_{secret}"
    return raw_key, hash_api_key(raw_key)

def hash_api_key(raw_key: str) -> str:
    """
    Hashes an API key using SHA-256 for secure database storage.
    """
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a secure URL-safe random token."""
    return secrets.token_urlsafe(nbytes)

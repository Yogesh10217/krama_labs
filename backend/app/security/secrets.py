import os
from abc import ABC, abstractmethod
from typing import Optional

class SecretProvider(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        pass

class EnvironmentSecretProvider(SecretProvider):
    def get_secret(self, key: str) -> Optional[str]:
        return os.getenv(key)

class VaultSecretProvider(SecretProvider):
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        
    def get_secret(self, key: str) -> Optional[str]:
        # Interface stub for Phase 13 vault integration
        return None

_provider: Optional[SecretProvider] = None

def get_secret_provider() -> SecretProvider:
    global _provider
    if _provider is None:
        from app.core.config import Config
        if Config.SECRET_PROVIDER == "vault" and Config.VAULT_URL:
            _provider = VaultSecretProvider(Config.VAULT_URL, Config.VAULT_TOKEN)
        else:
            _provider = EnvironmentSecretProvider()
    return _provider

def get_secret(key: str) -> Optional[str]:
    """Retrieves a secret without exposing it in logs."""
    return get_secret_provider().get_secret(key)

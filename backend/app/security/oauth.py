# Stub for OAuth2 integration
from typing import Dict, Any

class OAuth2Provider:
    """Base class for OAuth2 providers (Google, Microsoft, etc.)"""
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self) -> str:
        raise NotImplementedError()

    def get_token(self, code: str) -> Dict[str, Any]:
        raise NotImplementedError()

    def get_user_info(self, token: str) -> Dict[str, Any]:
        raise NotImplementedError()

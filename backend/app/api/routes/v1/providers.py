from fastapi import APIRouter
from typing import List, Dict, Any
from app.extraction.providers.factory import ProviderFactory

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_providers():
    providers = ProviderFactory.get_all_providers()
    
    result = []
    for name, provider in providers.items():
        try:
            is_healthy = provider.health()
            models = provider.supported_models()
        except Exception:
            is_healthy = False
            models = []
            
        result.append({
            "provider": name,
            "healthy": is_healthy,
            "available_models": models,
            "default_model": models[0] if models else None,
            "version": provider.provider_version()
        })
        
    return result

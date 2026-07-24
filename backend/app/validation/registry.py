from app.validation.base import Validator
from app.validation.rules import RuleValidator

_REGISTRY = {
    "rules": RuleValidator
}

def get_validator(provider_name: str) -> Validator:
    if provider_name not in _REGISTRY:
        raise ValueError(f"Unknown validation provider: {provider_name}")
    return _REGISTRY[provider_name]()

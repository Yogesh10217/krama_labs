from typing import Dict, Type
from .base import DocumentClassifier
from .rules import RulesClassifier
from app.core.exceptions import KramaException

class ProviderUnavailableException(KramaException):
    def __init__(self, provider: str, message: str = ""):
        super().__init__(
            status_code=503,
            error_code="CLASSIFICATION_PROVIDER_UNAVAILABLE",
            message=f"Classification provider '{provider}' is unavailable: {message}"
        )


_CLASSIFIERS: Dict[str, Type[DocumentClassifier]] = {
    "rules": RulesClassifier
}


def get_classifier(provider_name: str) -> DocumentClassifier:
    """
    Factory to retrieve a configured classifier instance.
    Raises ProviderUnavailableException if not found.
    """
    cls = _CLASSIFIERS.get(provider_name.lower())
    if not cls:
        raise ProviderUnavailableException(provider_name, "Provider is not registered.")
    
    # Instantiate the classifier
    try:
        return cls()
    except Exception as e:
        raise ProviderUnavailableException(provider_name, str(e))

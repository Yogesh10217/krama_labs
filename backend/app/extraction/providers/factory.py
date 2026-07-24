import logging
from typing import List, Dict
from app.core.config import Config
from app.extraction.providers.base import ExtractionProvider, ExtractionRequest, ExtractionResponse
from app.extraction.providers.rule import RuleProvider
from app.extraction.providers.ollama import OllamaProvider
from app.extraction.providers.gemini import GeminiProvider
from app.extraction.providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)

class FallbackProvider(ExtractionProvider):
    def __init__(self, providers: List[ExtractionProvider]):
        self.providers = providers

    def initialize(self) -> None:
        for p in self.providers:
            p.initialize()

    def health(self) -> bool:
        # Healthy if at least one is healthy
        return any(p.health() for p in self.providers)

    def supported_models(self) -> List[str]:
        models = []
        for p in self.providers:
            models.extend(p.supported_models())
        return models

    def provider_name(self) -> str:
        return "fallback_chain"

    def provider_version(self) -> str:
        return "1.0"

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        errors = []
        for provider in self.providers:
            try:
                logger.info(f"provider_started provider={provider.provider_name()} doc_id={request.document_id}")
                response = provider.extract(request)
                
                # Policy checks
                if not response.fields:
                    raise ValueError(f"Provider {provider.provider_name()} returned empty extraction")
                
                if response.confidence < 0.5:
                    raise ValueError(f"Provider {provider.provider_name()} confidence {response.confidence} below threshold 0.5")
                
                # Check missing required fields
                extracted_names = {f.name for f in response.fields if f.normalized_value}
                required_names = {f.name for f in request.schema.fields if getattr(f, 'required', False)}
                missing = required_names - extracted_names
                if missing:
                    raise ValueError(f"Provider {provider.provider_name()} missing required fields: {missing}")

                logger.info(f"provider_completed provider={provider.provider_name()} doc_id={request.document_id} latency={response.latency_ms}")
                return response

            except Exception as e:
                logger.warning(f"provider_failed provider={provider.provider_name()} error={str(e)}")
                errors.append(f"{provider.provider_name()}: {str(e)}")
                logger.info(f"provider_retry provider={provider.provider_name()} doc_id={request.document_id}")

        raise RuntimeError(f"All fallback providers failed: {errors}")


class ProviderFactory:
    _registry: Dict[str, ExtractionProvider] = {}
    _initialized = False

    @classmethod
    def _init(cls):
        if cls._initialized:
            return
        cls._registry = {
            "rule": RuleProvider(),
            "ollama": OllamaProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider()
        }
        cls._initialized = True

    @classmethod
    def get(cls) -> ExtractionProvider:
        cls._init()
        order_str = Config.EXTRACTION_FALLBACK_ORDER
        provider_names = [name.strip().lower() for name in order_str.split(",")]
        
        selected_providers = []
        for name in provider_names:
            if name in cls._registry:
                selected_providers.append(cls._registry[name])
            else:
                logger.warning(f"Provider {name} requested in fallback order but not registered.")

        if not selected_providers:
            # Fallback to rule if config is broken
            selected_providers.append(cls._registry["rule"])

        if len(selected_providers) == 1:
            return selected_providers[0]
            
        return FallbackProvider(selected_providers)

    @classmethod
    def get_all_providers(cls) -> Dict[str, ExtractionProvider]:
        cls._init()
        return cls._registry

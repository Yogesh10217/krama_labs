import time
import uuid
import requests
import logging
from typing import List
from app.core.config import Config
from app.extraction.providers.base import ExtractionProvider, ExtractionRequest, ExtractionResponse, ExtractedFieldData, FieldEvidenceData
from app.extraction.prompts.builder import PromptBuilder
from app.extraction.normalizer import ResponseNormalizer, ExtractionNormalizer

logger = logging.getLogger(__name__)

class OllamaProvider(ExtractionProvider):
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL.rstrip('/')
        self.model = Config.OLLAMA_MODEL
        self.prompt_builder = PromptBuilder()

    def initialize(self) -> None:
        pass

    def health(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def supported_models(self) -> List[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return [m["name"] for m in models]
        except requests.RequestException:
            pass
        return [self.model]

    def provider_name(self) -> str:
        return "ollama"

    def provider_version(self) -> str:
        return "1.0"

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        start_time = time.time()
        
        prompt_package = self.prompt_builder.build(request)
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt_package.system_prompt},
                {"role": "user", "content": prompt_package.user_prompt}
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        }
        
        timeout = Config.EXTRACTION_TIMEOUT_SECONDS

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            
            raw_output = data.get("message", {}).get("content", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            
            parsed_json = ResponseNormalizer.normalize_json(raw_output)
            
            # Map to ExtractedFieldData
            extracted_fields = []
            for field_def in request.schema.fields:
                raw_val = parsed_json.get(field_def.name)
                if raw_val is not None:
                    raw_str = str(raw_val)
                    raw, norm = ExtractionNormalizer.normalize(raw_str, field_def.data_type)
                    
                    evidence = []
                    # LLMs don't provide accurate bounding boxes yet, we defer to Phase 7 for validation grounding
                    evidence.append(FieldEvidenceData(
                        rule_id=f"ollama_{field_def.name}",
                        confidence=0.9 if norm else 0.5
                    ))
                    
                    extracted_fields.append(ExtractedFieldData(
                        name=field_def.name,
                        raw_value=raw,
                        normalized_value=norm,
                        data_type=field_def.data_type,
                        confidence=0.9,
                        evidence=evidence
                    ))
                    
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ExtractionResponse(
                provider=self.provider_name(),
                model=self.model,
                provider_version=self.provider_version(),
                schema_version=request.schema.schema_version,
                fields=extracted_fields,
                confidence=0.9,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                request_id=str(uuid.uuid4()),
                finish_reason="stop",
                cached=False,
                prompt_version=prompt_package.version
            )
            
        except Exception as e:
            logger.error(f"Ollama extraction failed: {str(e)}")
            raise e

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

class GeminiProvider(ExtractionProvider):
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model = Config.GEMINI_MODEL
        self.prompt_builder = PromptBuilder()

    def initialize(self) -> None:
        if not self.api_key:
            logger.warning("Gemini API key is missing. Provider will not function.")

    def health(self) -> bool:
        if not self.api_key:
            return False
        # Simple models list check
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        try:
            resp = requests.get(url, timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def supported_models(self) -> List[str]:
        return [self.model]

    def provider_name(self) -> str:
        return "gemini"

    def provider_version(self) -> str:
        return "1.0"

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        start_time = time.time()
        prompt_package = self.prompt_builder.build(request)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        # System instructions are supported in Gemini v1beta
        payload = {
            "system_instruction": {
                "parts": [{"text": prompt_package.system_prompt}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": prompt_package.user_prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }
        
        timeout = Config.EXTRACTION_TIMEOUT_SECONDS

        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            # Navigate Gemini response
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Gemini")
                
            raw_output = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", 0)
            completion_tokens = usage.get("candidatesTokenCount", 0)
            finish_reason = candidates[0].get("finishReason", "UNKNOWN")
            
            parsed_json = ResponseNormalizer.normalize_json(raw_output)
            
            # Map to ExtractedFieldData
            extracted_fields = []
            for field_def in request.schema.fields:
                raw_val = parsed_json.get(field_def.name)
                if raw_val is not None:
                    raw_str = str(raw_val)
                    raw, norm = ExtractionNormalizer.normalize(raw_str, field_def.data_type)
                    
                    evidence = [FieldEvidenceData(
                        rule_id=f"gemini_{field_def.name}",
                        confidence=0.95 if norm else 0.5
                    )]
                    
                    extracted_fields.append(ExtractedFieldData(
                        name=field_def.name,
                        raw_value=raw,
                        normalized_value=norm,
                        data_type=field_def.data_type,
                        confidence=0.95,
                        evidence=evidence
                    ))
                    
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ExtractionResponse(
                provider=self.provider_name(),
                model=self.model,
                provider_version=self.provider_version(),
                schema_version=request.schema.schema_version,
                fields=extracted_fields,
                confidence=0.95,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                request_id=str(uuid.uuid4()),
                finish_reason=finish_reason,
                cached=False,
                prompt_version=prompt_package.version
            )
            
        except Exception as e:
            logger.error(f"Gemini extraction failed: {str(e)}")
            raise e

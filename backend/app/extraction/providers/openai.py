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

class OpenAIProvider(ExtractionProvider):
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.base_url = Config.OPENAI_BASE_URL.rstrip('/')
        self.model = Config.OPENAI_MODEL
        self.prompt_builder = PromptBuilder()

    def initialize(self) -> None:
        if not self.api_key:
            logger.warning("OpenAI API key is missing. Provider will not function.")

    def health(self) -> bool:
        if not self.api_key:
            return False
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def supported_models(self) -> List[str]:
        if not self.api_key:
            return [self.model]
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                return [m["id"] for m in models]
        except requests.RequestException:
            pass
        return [self.model]

    def provider_name(self) -> str:
        return "openai"

    def provider_version(self) -> str:
        return "1.0"

    def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        start_time = time.time()
        prompt_package = self.prompt_builder.build(request)
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt_package.system_prompt},
                {"role": "user", "content": prompt_package.user_prompt}
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }
        
        timeout = Config.EXTRACTION_TIMEOUT_SECONDS

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("No choices returned from OpenAI")
                
            raw_output = choices[0].get("message", {}).get("content", "")
            finish_reason = choices[0].get("finish_reason", "unknown")
            
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            req_id = data.get("id", str(uuid.uuid4()))
            
            parsed_json = ResponseNormalizer.normalize_json(raw_output)
            
            extracted_fields = []
            for field_def in request.schema.fields:
                raw_val = parsed_json.get(field_def.name)
                if raw_val is not None:
                    raw_str = str(raw_val)
                    raw, norm = ExtractionNormalizer.normalize(raw_str, field_def.data_type)
                    
                    evidence = [FieldEvidenceData(
                        rule_id=f"openai_{field_def.name}",
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
                request_id=req_id,
                finish_reason=finish_reason,
                cached=False,
                prompt_version=prompt_package.version
            )
            
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {str(e)}")
            raise e

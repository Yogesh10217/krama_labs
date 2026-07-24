import os
import json
from typing import Any, List
from pathlib import Path
from app.extraction.providers.base import PromptPackage, ExtractionRequest

PROMPTS_DIR = Path(__file__).parent

class PromptBuilder:
    def __init__(self):
        self.version = "1.0"

    def _load_template(self, document_type: str) -> str:
        template_path = PROMPTS_DIR / f"{document_type}.txt"
        if not template_path.exists():
            template_path = PROMPTS_DIR / "default.txt"
        
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_sections(self, content: str) -> dict:
        sections = {"SYSTEM": "", "SCHEMA_INSTRUCTIONS": "", "USER": ""}
        current_section = None
        lines = []

        for line in content.splitlines():
            line_stripped = line.strip()
            if line_stripped in ["[SYSTEM]", "[SCHEMA_INSTRUCTIONS]", "[USER]"]:
                if current_section:
                    sections[current_section] = "\n".join(lines).strip()
                current_section = line_stripped.strip("[]")
                lines = []
            elif current_section:
                lines.append(line)
        
        if current_section:
            sections[current_section] = "\n".join(lines).strip()
            
        return sections

    def _format_schema(self, schema) -> str:
        # Dump schema to json string. We assume schema is a dict or BaseModel.
        if hasattr(schema, "model_dump"):
            return json.dumps(schema.model_dump(), indent=2)
        elif isinstance(schema, dict):
            return json.dumps(schema, indent=2)
        return str(schema)

    def _format_ocr_text(self, pages: List[Any]) -> str:
        # Pages is a list of OCRPageResult.
        # Ensure we have full_text attributes available.
        text_parts = []
        for page in pages:
            if hasattr(page, 'full_text'):
                text_parts.append(f"--- Page {getattr(page, 'page_number', '?')} ---\n{page.full_text}")
        return "\n".join(text_parts)

    def build(self, request: ExtractionRequest) -> PromptPackage:
        template_content = self._load_template(request.document_type)
        sections = self._parse_sections(template_content)
        
        schema_json = self._format_schema(request.schema)
        ocr_text = self._format_ocr_text(request.ocr_pages)
        
        system_base = sections.get("SYSTEM", "")
        schema_inst = sections.get("SCHEMA_INSTRUCTIONS", "").replace("{schema_json}", schema_json)
        
        system_prompt = f"{system_base}\n\n{schema_inst}".strip()
        user_prompt = sections.get("USER", "").replace("{ocr_text}", ocr_text)
        
        return PromptPackage(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_json=schema_json,
            version=self.version
        )

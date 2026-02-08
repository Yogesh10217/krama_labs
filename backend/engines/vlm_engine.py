"""Gemini VLM engine for document classification and extraction."""

import re
import json
from typing import Dict

import numpy as np
import cv2
from PIL import Image
import google.generativeai as genai

from config import Config
from engines.classifier import DOCUMENT_TAXONOMY, get_extraction_prompt, classify_by_keywords, get_category, get_label


class GeminiVLM:
    """Gemini VLM using Google AI API."""

    def __init__(self, model_name: str = None, api_key: str = None):
        model_name = model_name or Config.GEMINI_MODEL
        key = api_key or Config.GOOGLE_API_KEY
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        )
        print(f"  Gemini VLM initialized ({model_name})")

    def _image_to_pil(self, image) -> Image.Image:
        if isinstance(image, str):
            return Image.open(image)
        elif isinstance(image, np.ndarray):
            return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        return image

    def _parse_json(self, response: str) -> Dict:
        try:
            text = response.strip()
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*$", "", text)
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", response)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
            return {"error": "parse_failed", "raw": response[:500]}

    def _safe_generate(self, prompt: str, image: Image.Image) -> Dict:
        try:
            response = self.model.generate_content([prompt, image])
            return self._parse_json(response.text)
        except Exception as e:
            print(f"    Gemini error: {e}")
            return {"error": str(e)}

    def classify(self, image) -> Dict:
        image = self._image_to_pil(image)

        # Build the list of valid types from taxonomy
        type_keys = "|".join(DOCUMENT_TAXONOMY.keys())
        type_descriptions = "\n".join(
            f"  - {k}: {v['label']} ({v['description']})"
            for k, v in DOCUMENT_TAXONOMY.items()
        )

        prompt = f"""Analyze this document and classify it into one of the following Indian insurance / KYC document types.

Valid document types:
{type_descriptions}

Return JSON:
{{
    "document_type": "{type_keys}|unknown",
    "category": "medical|identity|vehicle|insurance|financial|other",
    "label": "Human readable label",
    "confidence": 0.95,
    "language": "english|hindi|mixed",
    "has_tables": true,
    "has_charts": false,
    "key_entities": ["entity1", "entity2"]
}}

IMPORTANT:
- For Aadhaar cards use "aadhaar_card"
- For PAN cards use "pan_card"
- For Driving License use "driving_license"
- For vehicle RC (bike/scooter) use "bike_rc", for car RC use "car_rc"
- For hospital discharge papers use "discharge_summary"
- For hospital bills/receipts use "hospital_bill"
- For insurance policies use "insurance_policy"
- For FIR/police reports use "fir"
- Use "unknown" only if the document does not match any type above."""

        result = self._safe_generate(prompt, image)

        # Normalize / enrich result
        doc_type = result.get("document_type", "unknown").lower().replace(" ", "_").replace("-", "_")
        if doc_type not in DOCUMENT_TAXONOMY and doc_type != "unknown":
            # Try fuzzy match
            for key in DOCUMENT_TAXONOMY:
                if key in doc_type or doc_type in key:
                    doc_type = key
                    break

        result["document_type"] = doc_type
        result.setdefault("category", get_category(doc_type))
        result.setdefault("label", get_label(doc_type))
        if "confidence" not in result:
            result["confidence"] = 0.5
        return result

    def extract(self, image, doc_type: str = "generic") -> Dict:
        image = self._image_to_pil(image)
        prompt = get_extraction_prompt(doc_type)
        return self._safe_generate(prompt, image)

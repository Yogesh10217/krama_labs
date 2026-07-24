import re
import json
from typing import Any, Tuple

class ExtractionNormalizer:
    @staticmethod
    def normalize(raw_value: str, data_type: str) -> Tuple[str, str]:
        """Normalize extracted value based on data type. 
        Returns (raw_value, normalized_value).
        """
        if not raw_value:
            return "", ""

        raw_str = str(raw_value).strip()
        norm_val = raw_str

        try:
            if data_type == "STRING" or data_type == "IDENTIFIER":
                norm_val = " ".join(raw_str.split()) # compress whitespace
            elif data_type == "CURRENCY" or data_type == "DECIMAL":
                # Remove currency symbols and commas
                cleaned = re.sub(r"[^\d.]", "", raw_str)
                # Handle multiple dots if any (take last one as decimal, or first? Just basic cleanup)
                parts = cleaned.split('.')
                if len(parts) > 2:
                    cleaned = "".join(parts[:-1]) + "." + parts[-1]
                if cleaned:
                    norm_val = str(float(cleaned))
                else:
                    norm_val = ""
            elif data_type == "INTEGER":
                cleaned = re.sub(r"[^\d]", "", raw_str)
                if cleaned:
                    norm_val = str(int(cleaned))
                else:
                    norm_val = ""
            elif data_type == "DATE":
                # Basic cleanup, true normalization requires parsing which we leave simple for now
                norm_val = re.sub(r"[^\d/\-]", "", raw_str)
            elif data_type == "BOOLEAN":
                lower = raw_str.lower()
                if lower in ("yes", "true", "y", "1"):
                    norm_val = "true"
                elif lower in ("no", "false", "n", "0"):
                    norm_val = "false"
        except Exception:
            # If normalization fails (e.g. float conversion), fallback to empty string
            norm_val = ""
        
        # Reject NaN or Infinity
        if norm_val.lower() in ("nan", "inf", "infinity", "-inf", "-infinity"):
            norm_val = ""

        return raw_str, norm_val


class ResponseNormalizer:
    @staticmethod
    def normalize_json(raw_output: str) -> dict:
        """Strip markdown and parse JSON safely."""
        cleaned = raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Maybe try to find first { and last }
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end+1])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Failed to parse JSON from provider output: {str(e)}")

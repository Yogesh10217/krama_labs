"""
OCR-based field extraction engine.

Extracts structured data from OCR text using regex patterns and keyword matching.
No VLM/API key required - works purely on PaddleOCR output.
"""

import re
from typing import Dict, List, Any, Optional, Tuple

from app.models import OCRRegion, BoundingBox, DocumentChunk


# ── Layout-aware markdown builder ───────────────────────────────────────────

class LayoutMarkdownBuilder:
    """Converts OCR regions into structured markdown by analyzing spatial layout."""

    @staticmethod
    def regions_to_markdown(regions: List[OCRRegion], page_width: float = 1920) -> str:
        """
        Convert OCR regions to markdown, respecting layout:
        - Large/uppercase text → headings
        - Aligned columns → tables
        - Bullet/number prefixes → lists
        - Everything else → paragraphs
        """
        if not regions:
            return ""

        # Sort by vertical then horizontal position
        sorted_regions = sorted(regions, key=lambda r: (r.bbox.y1, r.bbox.x1))

        # Group into lines (regions on same y-level)
        lines = LayoutMarkdownBuilder._group_into_lines(sorted_regions)

        # Detect table-like structures (multiple lines with aligned columns)
        md_parts = []
        i = 0
        while i < len(lines):
            line_regions = lines[i]
            line_text = " ".join(r.text for r in line_regions)

            # Check if this is a heading (large text, uppercase, short)
            if LayoutMarkdownBuilder._is_heading(line_regions):
                md_parts.append(f"\n## {line_text.strip()}\n")
                i += 1
                continue

            # Check for table structure (multiple columns, consecutive lines)
            table_lines, table_end = LayoutMarkdownBuilder._detect_table(lines, i)
            if table_lines and len(table_lines) >= 2:
                md_parts.append(LayoutMarkdownBuilder._build_table_md(table_lines))
                i = table_end
                continue

            # Check for list items
            if re.match(r'^[\d\u2022\-*]+[.)]\s', line_text.strip()):
                cleaned = re.sub(r'^[\d\u2022\-*]+[.)]+\s*', '', line_text.strip())
                md_parts.append(f"- {cleaned}")
                i += 1
                continue

            # Check for key-value pairs (label: value pattern)
            kv_match = re.match(r'^(.+?)[\s]*[:]\s*(.+)$', line_text.strip())
            if kv_match:
                md_parts.append(f"**{kv_match.group(1).strip()}:** {kv_match.group(2).strip()}")
                i += 1
                continue

            # Regular text
            if line_text.strip():
                md_parts.append(line_text.strip())

            i += 1

        return "\n\n".join(md_parts)

    @staticmethod
    def _group_into_lines(regions: List[OCRRegion], y_threshold: float = 15) -> List[List[OCRRegion]]:
        """Group OCR regions into lines based on vertical proximity."""
        if not regions:
            return []

        lines = []
        current_line = [regions[0]]

        for region in regions[1:]:
            if abs(region.bbox.y1 - current_line[-1].bbox.y1) < y_threshold:
                current_line.append(region)
            else:
                current_line.sort(key=lambda r: r.bbox.x1)
                lines.append(current_line)
                current_line = [region]

        if current_line:
            current_line.sort(key=lambda r: r.bbox.x1)
            lines.append(current_line)

        return lines

    @staticmethod
    def _is_heading(line_regions: List[OCRRegion]) -> bool:
        """Detect if a line is a heading based on text properties."""
        text = " ".join(r.text for r in line_regions).strip()
        if not text or len(text) > 120:
            return False

        # All uppercase
        if text.isupper() and len(text) > 3:
            return True

        # Large bounding box height relative to average
        avg_height = sum(r.bbox.height for r in line_regions) / len(line_regions)
        if avg_height > 30 and len(text) < 80:
            return True

        # Ends with common heading patterns
        if text.endswith(":") and len(text) < 40:
            return False  # This is a label, not a heading

        return False

    @staticmethod
    def _detect_table(lines: List[List[OCRRegion]], start: int) -> Tuple[List[List[str]], int]:
        """Detect table structure starting from a line index."""
        if start >= len(lines):
            return [], start

        # Check if multiple consecutive lines have similar column count (>= 2 cols)
        table_lines = []
        i = start

        while i < len(lines):
            regions = lines[i]
            if len(regions) >= 2:
                # Multiple regions on same line = potential table row
                cols = [r.text.strip() for r in regions]
                table_lines.append(cols)
                i += 1
            else:
                break

        if len(table_lines) >= 2:
            return table_lines, i
        return [], start

    @staticmethod
    def _build_table_md(table_lines: List[List[str]]) -> str:
        """Build markdown table from rows of columns."""
        if not table_lines:
            return ""

        # Normalize column counts
        max_cols = max(len(row) for row in table_lines)
        normalized = [row + [""] * (max_cols - len(row)) for row in table_lines]

        # First row is header
        header = "| " + " | ".join(normalized[0]) + " |"
        separator = "| " + " | ".join(["---"] * max_cols) + " |"
        rows = []
        for row in normalized[1:]:
            rows.append("| " + " | ".join(row) + " |")

        return "\n".join([header, separator] + rows)


# ── OCR text field extraction ───────────────────────────────────────────────

class OCRFieldExtractor:
    """Extracts structured fields from OCR text using regex and keyword patterns."""

    # Common Indian patterns
    AADHAAR_PATTERN = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
    PAN_PATTERN = re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b')
    DATE_PATTERN = re.compile(r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\b')
    AMOUNT_PATTERN = re.compile(r'(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)', re.IGNORECASE)
    PHONE_PATTERN = re.compile(r'\b(?:\+91[\s\-]?)?[6-9]\d{9}\b')
    EMAIL_PATTERN = re.compile(r'\b[\w\.\-]+@[\w\.\-]+\.\w+\b')
    PINCODE_PATTERN = re.compile(r'\b\d{6}\b')
    DL_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}\s?\d{4,}\b')
    VEHICLE_PATTERN = re.compile(r'\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{1,4}\b')
    POLICY_PATTERN = re.compile(r'\b(?:POL|PLY|INS|HIC)\w*[/\-]?\d{4,}\b', re.IGNORECASE)

    @classmethod
    def extract_from_regions(cls, regions: List[OCRRegion], doc_type: str) -> Dict[str, Any]:
        """Extract structured fields from OCR regions based on document type."""
        # Combine all OCR text
        full_text = "\n".join(r.text for r in sorted(regions, key=lambda r: (r.bbox.y1, r.bbox.x1)))

        # Common fields
        result = cls._extract_common_fields(full_text)

        # Type-specific extraction
        type_extractors = {
            "aadhaar_card": cls._extract_aadhaar,
            "pan_card": cls._extract_pan,
            "driving_license": cls._extract_dl,
            "passport": cls._extract_passport,
            "voter_id": cls._extract_voter_id,
            "discharge_summary": cls._extract_discharge,
            "hospital_bill": cls._extract_hospital_bill,
            "prescription": cls._extract_prescription,
            "lab_report": cls._extract_lab_report,
            "death_certificate": cls._extract_death_cert,
            "bike_rc": cls._extract_rc,
            "car_rc": cls._extract_rc,
            "fir": cls._extract_fir,
            "surveyor_report": cls._extract_surveyor,
            "repair_estimate": cls._extract_repair,
            "insurance_policy": cls._extract_insurance_policy,
            "claim_form": cls._extract_claim_form,
            "pre_auth_form": cls._extract_pre_auth,
            "bank_statement": cls._extract_bank_statement,
            "invoice": cls._extract_invoice,
        }

        extractor = type_extractors.get(doc_type)
        if extractor:
            specific = extractor(full_text, regions)
            result.update(specific)

        # Add raw text for fallback
        result["_ocr_text"] = full_text[:2000]
        result["_extraction_method"] = "ocr_regex"

        return result

    @classmethod
    def _extract_common_fields(cls, text: str) -> Dict[str, Any]:
        """Extract commonly found fields across all document types."""
        fields = {}

        # Dates
        dates = cls.DATE_PATTERN.findall(text)
        if dates:
            fields["dates_found"] = dates[:10]

        # Amounts
        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            fields["amounts_found"] = [a.replace(",", "") for a in amounts[:10]]

        # Phone numbers
        phones = cls.PHONE_PATTERN.findall(text)
        if phones:
            fields["phone_numbers"] = phones[:5]

        # Email
        emails = cls.EMAIL_PATTERN.findall(text)
        if emails:
            fields["emails"] = emails[:3]

        return fields

    @classmethod
    def _find_value_after(cls, text: str, keywords: List[str], max_chars: int = 100) -> Optional[str]:
        """Find value appearing after any of the keywords."""
        text_lower = text.lower()
        for kw in keywords:
            idx = text_lower.find(kw.lower())
            if idx >= 0:
                after = text[idx + len(kw):idx + len(kw) + max_chars]
                # Clean: take until newline, strip labels
                after = re.sub(r'^[\s:;\-]+', '', after)
                value = after.split('\n')[0].strip()
                if value:
                    return value
        return None

    @classmethod
    def _find_value_between(cls, text: str, start_kw: str, end_kw: str) -> Optional[str]:
        """Find value between two keywords."""
        text_lower = text.lower()
        s = text_lower.find(start_kw.lower())
        if s < 0:
            return None
        e = text_lower.find(end_kw.lower(), s + len(start_kw))
        if e < 0:
            return text[s + len(start_kw):s + len(start_kw) + 100].strip().split('\n')[0]
        return text[s + len(start_kw):e].strip()

    # ── Identity docs ──

    @classmethod
    def _extract_aadhaar(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        aadhaar_match = cls.AADHAAR_PATTERN.search(text)
        if aadhaar_match:
            num = aadhaar_match.group().replace(" ", "")
            result["aadhaar_number"] = f"XXXX XXXX {num[-4:]}"

        result["full_name"] = cls._find_value_after(text, ["name", "naam"]) or ""
        result["date_of_birth"] = cls._find_value_after(text, ["dob", "date of birth", "birth", "year of birth"]) or ""
        result["gender"] = cls._find_value_after(text, ["gender", "male", "female"]) or ""
        result["address"] = cls._find_value_after(text, ["address", "s/o", "d/o", "w/o", "c/o"], max_chars=200) or ""

        vid = re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', text)
        if vid:
            result["vid"] = vid.group()

        return result

    @classmethod
    def _extract_pan(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        pan_match = cls.PAN_PATTERN.search(text)
        if pan_match:
            result["pan_number"] = pan_match.group()

        result["full_name"] = cls._find_value_after(text, ["name"]) or ""
        result["father_name"] = cls._find_value_after(text, ["father", "father's name"]) or ""
        result["date_of_birth"] = cls._find_value_after(text, ["date of birth", "dob", "birth"]) or ""

        return result

    @classmethod
    def _extract_dl(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        dl_match = cls.DL_PATTERN.search(text)
        if dl_match:
            result["dl_number"] = dl_match.group()

        result["full_name"] = cls._find_value_after(text, ["name"]) or ""
        result["date_of_birth"] = cls._find_value_after(text, ["dob", "date of birth", "birth"]) or ""
        result["blood_group"] = cls._find_value_after(text, ["blood", "bg"]) or ""
        result["address"] = cls._find_value_after(text, ["address"], max_chars=200) or ""
        result["issue_date"] = cls._find_value_after(text, ["issue date", "doi", "issued"]) or ""
        result["validity_transport"] = cls._find_value_after(text, ["transport", "tr validity"]) or ""
        result["validity_non_transport"] = cls._find_value_after(text, ["non-transport", "nt validity"]) or ""
        result["issuing_rto"] = cls._find_value_after(text, ["rto", "authority"]) or ""

        # Vehicle classes
        classes = re.findall(r'\b(LMV|MCWG|HMV|HPMV|HTV|LMV-NT|LMVTR|MC50CC|MCWG|MCWOG)\b', text, re.IGNORECASE)
        if classes:
            result["vehicle_classes"] = list(set(c.upper() for c in classes))

        return result

    @classmethod
    def _extract_passport(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        passport_match = re.search(r'\b[A-Z]\d{7}\b', text)
        if passport_match:
            result["passport_number"] = passport_match.group()

        result["full_name"] = cls._find_value_after(text, ["given name", "surname", "name"]) or ""
        result["nationality"] = cls._find_value_after(text, ["nationality"]) or ""
        result["date_of_birth"] = cls._find_value_after(text, ["date of birth", "dob"]) or ""
        result["gender"] = cls._find_value_after(text, ["sex", "gender"]) or ""
        result["place_of_birth"] = cls._find_value_after(text, ["place of birth"]) or ""
        result["date_of_issue"] = cls._find_value_after(text, ["date of issue"]) or ""
        result["date_of_expiry"] = cls._find_value_after(text, ["date of expiry", "expiry"]) or ""
        result["place_of_issue"] = cls._find_value_after(text, ["place of issue"]) or ""

        return result

    @classmethod
    def _extract_voter_id(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        epic_match = re.search(r'\b[A-Z]{3}\d{7}\b', text)
        if epic_match:
            result["epic_number"] = epic_match.group()

        result["full_name"] = cls._find_value_after(text, ["name", "elector"]) or ""
        result["father_husband_name"] = cls._find_value_after(text, ["father", "husband"]) or ""
        result["date_of_birth"] = cls._find_value_after(text, ["date of birth", "dob", "age"]) or ""
        result["gender"] = cls._find_value_after(text, ["sex", "gender"]) or ""
        result["address"] = cls._find_value_after(text, ["address"], max_chars=200) or ""

        return result

    # ── Medical docs ──

    @classmethod
    def _extract_discharge(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["patient_name"] = cls._find_value_after(text, ["patient name", "patient", "name of patient"]) or ""
        result["age"] = cls._find_value_after(text, ["age", "yrs"]) or ""
        result["gender"] = cls._find_value_after(text, ["sex", "gender"]) or ""
        result["hospital_name"] = cls._find_value_after(text, ["hospital", "medical center", "healthcare"]) or ""
        result["uhid"] = cls._find_value_after(text, ["uhid", "mr no", "mrn", "ip no"]) or ""
        result["date_of_admission"] = cls._find_value_after(text, ["admission", "date of admission", "admitted"]) or ""
        result["date_of_discharge"] = cls._find_value_after(text, ["discharge", "date of discharge", "discharged"]) or ""
        result["diagnosis"] = cls._find_value_after(text, ["diagnosis", "final diagnosis", "principal diagnosis"], max_chars=200) or ""
        result["treating_doctor"] = cls._find_value_after(text, ["doctor", "consultant", "dr.", "treating"]) or ""
        result["department"] = cls._find_value_after(text, ["department", "dept", "speciality"]) or ""
        result["room_type"] = cls._find_value_after(text, ["room", "ward", "bed"]) or ""
        result["condition_at_discharge"] = cls._find_value_after(text, ["condition at discharge", "condition"]) or ""

        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            result["total_amount"] = amounts[-1].replace(",", "")

        return result

    @classmethod
    def _extract_hospital_bill(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["hospital_name"] = cls._find_value_after(text, ["hospital", "medical", "healthcare"]) or ""
        result["patient_name"] = cls._find_value_after(text, ["patient name", "patient", "name"]) or ""
        result["bill_number"] = cls._find_value_after(text, ["bill no", "bill number", "invoice no", "receipt"]) or ""
        result["bill_date"] = cls._find_value_after(text, ["bill date", "date", "invoice date"]) or ""
        result["uhid"] = cls._find_value_after(text, ["uhid", "mr no", "mrn"]) or ""

        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            cleaned = [a.replace(",", "") for a in amounts]
            result["amounts_breakdown"] = cleaned
            try:
                result["total_amount"] = max(float(a) for a in cleaned)
            except (ValueError, TypeError):
                pass

        result["payment_mode"] = cls._find_value_after(text, ["payment", "mode of payment", "paid by"]) or ""
        return result

    @classmethod
    def _extract_prescription(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["doctor_name"] = cls._find_value_after(text, ["dr.", "doctor", "physician"]) or ""
        result["patient_name"] = cls._find_value_after(text, ["patient", "name"]) or ""
        result["date"] = cls._find_value_after(text, ["date"]) or ""
        result["diagnosis"] = cls._find_value_after(text, ["diagnosis", "rx"]) or ""

        # Find medication patterns
        meds = re.findall(r'(?:Tab|Cap|Syp|Inj|Drops?)\s*\.?\s*(\w[\w\s\-]+?)(?:\d+\s*mg|\d+\s*ml|$)', text, re.IGNORECASE)
        if meds:
            result["medications"] = [m.strip() for m in meds[:10]]

        return result

    @classmethod
    def _extract_lab_report(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["lab_name"] = cls._find_value_after(text, ["lab", "laboratory", "pathology", "diagnostic"]) or ""
        result["patient_name"] = cls._find_value_after(text, ["patient name", "patient", "name"]) or ""
        result["sample_date"] = cls._find_value_after(text, ["sample date", "collection", "collected"]) or ""
        result["report_date"] = cls._find_value_after(text, ["report date", "reported", "date"]) or ""
        result["referred_by"] = cls._find_value_after(text, ["referred", "ref", "doctor"]) or ""

        # Try to extract test results
        tests = []
        test_patterns = [
            r'(Hemoglobin|Hb|WBC|RBC|Platelets|ESR|Creatinine|Urea|Sugar|Glucose|Cholesterol|'
            r'Bilirubin|SGOT|SGPT|Albumin|TSH|T3|T4|HbA1c|Uric Acid|Sodium|Potassium)'
            r'\s*[:=]?\s*([\d.]+)\s*(\w*/?\w*)?'
        ]
        for pattern in test_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                tests.append({
                    "test_name": match.group(1),
                    "result": match.group(2),
                    "unit": match.group(3) if match.lastindex >= 3 else ""
                })
        if tests:
            result["tests"] = tests

        return result

    @classmethod
    def _extract_death_cert(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["full_name"] = cls._find_value_after(text, ["name of deceased", "name", "deceased"]) or ""
        result["date_of_death"] = cls._find_value_after(text, ["date of death", "death"]) or ""
        result["place_of_death"] = cls._find_value_after(text, ["place of death"]) or ""
        result["cause_of_death"] = cls._find_value_after(text, ["cause of death", "cause"], max_chars=200) or ""
        result["age_at_death"] = cls._find_value_after(text, ["age", "age at death"]) or ""
        result["registration_number"] = cls._find_value_after(text, ["registration no", "reg no"]) or ""
        return result

    # ── Vehicle docs ──

    @classmethod
    def _extract_rc(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        veh_match = cls.VEHICLE_PATTERN.search(text)
        if veh_match:
            result["registration_number"] = veh_match.group()

        result["owner_name"] = cls._find_value_after(text, ["owner", "name"]) or ""
        result["address"] = cls._find_value_after(text, ["address"], max_chars=200) or ""
        result["vehicle_class"] = cls._find_value_after(text, ["class of vehicle", "vehicle class", "class"]) or ""
        result["maker_model"] = cls._find_value_after(text, ["maker", "model", "make"]) or ""
        result["fuel_type"] = cls._find_value_after(text, ["fuel", "fuel type"]) or ""
        result["engine_number"] = cls._find_value_after(text, ["engine no", "engine number", "engine"]) or ""
        result["chassis_number"] = cls._find_value_after(text, ["chassis no", "chassis number", "chassis"]) or ""
        result["registration_date"] = cls._find_value_after(text, ["registration date", "regn date", "date of reg"]) or ""
        result["fitness_upto"] = cls._find_value_after(text, ["fitness", "fitness upto"]) or ""
        result["insurance_upto"] = cls._find_value_after(text, ["insurance", "insurance upto"]) or ""

        return result

    @classmethod
    def _extract_fir(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["fir_number"] = cls._find_value_after(text, ["fir no", "fir number", "case no"]) or ""
        result["police_station"] = cls._find_value_after(text, ["police station", "ps", "station"]) or ""
        result["date_of_fir"] = cls._find_value_after(text, ["date of fir", "date", "filed on"]) or ""
        result["date_of_incident"] = cls._find_value_after(text, ["date of incident", "occurrence", "incident"]) or ""
        result["complainant_name"] = cls._find_value_after(text, ["complainant", "informant"]) or ""
        result["description_of_incident"] = cls._find_value_after(text, ["brief facts", "description", "gist"], max_chars=300) or ""

        veh = cls.VEHICLE_PATTERN.search(text)
        if veh:
            result["vehicle_number"] = veh.group()

        sections = re.findall(r'\b(?:Section|Sec\.?|IPC|BNS)\s*(\d+[A-Za-z]?(?:/\d+[A-Za-z]?)*)', text, re.IGNORECASE)
        if sections:
            result["offence_sections"] = sections

        return result

    @classmethod
    def _extract_surveyor(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["surveyor_name"] = cls._find_value_after(text, ["surveyor", "surveyor name", "assessed by"]) or ""
        result["survey_date"] = cls._find_value_after(text, ["survey date", "date of survey"]) or ""
        result["vehicle_registration"] = ""
        veh = cls.VEHICLE_PATTERN.search(text)
        if veh:
            result["vehicle_registration"] = veh.group()
        result["vehicle_make_model"] = cls._find_value_after(text, ["make", "model", "vehicle"]) or ""
        result["nature_of_damage"] = cls._find_value_after(text, ["nature of damage", "damage", "loss"], max_chars=200) or ""

        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            cleaned = [a.replace(",", "") for a in amounts]
            try:
                result["estimated_cost"] = max(float(a) for a in cleaned)
            except (ValueError, TypeError):
                pass

        return result

    @classmethod
    def _extract_repair(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["garage_name"] = cls._find_value_after(text, ["garage", "workshop", "service"]) or ""
        veh = cls.VEHICLE_PATTERN.search(text)
        if veh:
            result["vehicle_registration"] = veh.group()
        result["estimate_date"] = cls._find_value_after(text, ["date", "estimate date"]) or ""

        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            cleaned = [a.replace(",", "") for a in amounts]
            try:
                result["total_amount"] = max(float(a) for a in cleaned)
            except (ValueError, TypeError):
                pass

        result["labour_charges"] = cls._find_value_after(text, ["labour", "labor"]) or ""
        result["painting_charges"] = cls._find_value_after(text, ["paint", "painting"]) or ""
        return result

    # ── Insurance docs ──

    @classmethod
    def _extract_insurance_policy(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["insurer_name"] = cls._find_value_after(text, ["insurer", "insurance company", "underwritten"]) or ""
        result["policy_number"] = cls._find_value_after(text, ["policy no", "policy number", "policy"]) or ""
        pol_match = cls.POLICY_PATTERN.search(text)
        if pol_match:
            result["policy_number"] = pol_match.group()
        result["policyholder_name"] = cls._find_value_after(text, ["policyholder", "insured name", "insured", "name"]) or ""
        result["sum_insured"] = cls._find_value_after(text, ["sum insured", "sum assured", "cover amount"]) or ""
        result["premium_amount"] = cls._find_value_after(text, ["premium", "premium amount"]) or ""
        result["policy_start_date"] = cls._find_value_after(text, ["start date", "inception", "commencement", "from"]) or ""
        result["policy_end_date"] = cls._find_value_after(text, ["end date", "expiry", "upto", "to"]) or ""
        result["nominee_name"] = cls._find_value_after(text, ["nominee", "beneficiary"]) or ""

        return result

    @classmethod
    def _extract_claim_form(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["claim_number"] = cls._find_value_after(text, ["claim no", "claim number"]) or ""
        result["policy_number"] = cls._find_value_after(text, ["policy no", "policy number"]) or ""
        result["insured_name"] = cls._find_value_after(text, ["insured", "claimant", "name"]) or ""
        result["claim_type"] = cls._find_value_after(text, ["claim type", "type of claim"]) or ""
        result["date_of_claim"] = cls._find_value_after(text, ["date of claim", "claim date"]) or ""
        result["hospital_name"] = cls._find_value_after(text, ["hospital", "medical center"]) or ""
        result["diagnosis"] = cls._find_value_after(text, ["diagnosis"]) or ""

        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            cleaned = [a.replace(",", "") for a in amounts]
            try:
                result["claim_amount"] = max(float(a) for a in cleaned)
            except (ValueError, TypeError):
                pass

        return result

    @classmethod
    def _extract_pre_auth(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["insurer_name"] = cls._find_value_after(text, ["insurer", "insurance company"]) or ""
        result["tpa_name"] = cls._find_value_after(text, ["tpa", "third party"]) or ""
        result["pre_auth_number"] = cls._find_value_after(text, ["pre-auth", "preauth", "authorization no"]) or ""
        result["policy_number"] = cls._find_value_after(text, ["policy no", "policy number"]) or ""
        result["patient_name"] = cls._find_value_after(text, ["patient", "name"]) or ""
        result["hospital_name"] = cls._find_value_after(text, ["hospital"]) or ""
        result["diagnosis"] = cls._find_value_after(text, ["diagnosis"]) or ""
        result["proposed_treatment"] = cls._find_value_after(text, ["treatment", "proposed", "procedure"]) or ""

        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            cleaned = [a.replace(",", "") for a in amounts]
            try:
                result["estimated_cost"] = max(float(a) for a in cleaned)
            except (ValueError, TypeError):
                pass

        return result

    # ── Financial docs ──

    @classmethod
    def _extract_bank_statement(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["bank_name"] = cls._find_value_after(text, ["bank", "branch"]) or ""
        result["account_number"] = cls._find_value_after(text, ["account no", "a/c no", "account number"]) or ""
        result["account_holder"] = cls._find_value_after(text, ["account holder", "name"]) or ""
        result["ifsc_code"] = ""
        ifsc = re.search(r'\b[A-Z]{4}0[A-Z0-9]{6}\b', text)
        if ifsc:
            result["ifsc_code"] = ifsc.group()

        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            cleaned = [float(a.replace(",", "")) for a in amounts if a.replace(",", "").replace(".", "").isdigit()]
            if cleaned:
                result["closing_balance"] = cleaned[-1]

        return result

    @classmethod
    def _extract_invoice(cls, text: str, regions: List[OCRRegion]) -> Dict:
        result = {}
        result["invoice_number"] = cls._find_value_after(text, ["invoice no", "bill no", "receipt no"]) or ""
        result["invoice_date"] = cls._find_value_after(text, ["date", "invoice date"]) or ""
        result["vendor_name"] = cls._find_value_after(text, ["from", "seller", "vendor", "company"]) or ""

        gstin = re.search(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d]\w\b', text)
        if gstin:
            result["vendor_gstin"] = gstin.group()

        amounts = cls.AMOUNT_PATTERN.findall(text)
        if amounts:
            cleaned = [a.replace(",", "") for a in amounts]
            try:
                result["total_amount"] = max(float(a) for a in cleaned)
            except (ValueError, TypeError):
                pass

        return result

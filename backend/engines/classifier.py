"""
Document Classifier — Indian Insurance Document Types.

Classifies documents into insurance-relevant categories and provides
extraction prompts tailored to each document type.
"""

from typing import Dict, List, Tuple

# ── Indian insurance document taxonomy ──────────────────────────────────────

DOCUMENT_TAXONOMY: Dict[str, Dict] = {
    # ── MEDICAL ──
    "discharge_summary": {
        "category": "medical",
        "label": "Discharge Summary",
        "keywords": ["discharge", "summary", "hospital", "admitted", "diagnosis", "treatment"],
        "description": "Hospital discharge summary with diagnosis, treatment, and billing",
    },
    "hospital_bill": {
        "category": "medical",
        "label": "Hospital Bill",
        "keywords": ["bill", "invoice", "hospital", "charges", "room", "total", "receipt"],
        "description": "Itemized hospital bill or receipt",
    },
    "prescription": {
        "category": "medical",
        "label": "Prescription",
        "keywords": ["prescription", "rx", "medicine", "tablet", "mg", "dosage", "dr."],
        "description": "Doctor's prescription / medication order",
    },
    "lab_report": {
        "category": "medical",
        "label": "Lab Report",
        "keywords": ["lab", "report", "test", "blood", "urine", "pathology", "result", "range"],
        "description": "Pathology or diagnostic lab report",
    },
    "doctor_certificate": {
        "category": "medical",
        "label": "Doctor Certificate",
        "keywords": ["certificate", "doctor", "medical", "fitness", "unfit", "leave"],
        "description": "Medical certificate from a doctor",
    },
    "death_certificate": {
        "category": "medical",
        "label": "Death Certificate",
        "keywords": ["death", "certificate", "deceased", "cause of death", "registrar"],
        "description": "Death certificate for life insurance claims",
    },

    # ── IDENTITY ──
    "aadhaar_card": {
        "category": "identity",
        "label": "Aadhaar Card",
        "keywords": ["aadhaar", "aadhar", "uid", "uidai", "unique identification", "12 digit", "1234"],
        "description": "UIDAI Aadhaar card (12-digit UID)",
    },
    "pan_card": {
        "category": "identity",
        "label": "PAN Card",
        "keywords": ["pan", "permanent account", "income tax", "nsdl", "abcde1234f"],
        "description": "Income Tax PAN card (10-char alphanumeric)",
    },
    "driving_license": {
        "category": "identity",
        "label": "Driving License",
        "keywords": ["driving", "license", "licence", "dl", "rto", "transport", "motor vehicle"],
        "description": "Driving License issued by RTO",
    },
    "passport": {
        "category": "identity",
        "label": "Passport",
        "keywords": ["passport", "republic of india", "travel", "emigration", "visa"],
        "description": "Indian passport",
    },
    "voter_id": {
        "category": "identity",
        "label": "Voter ID",
        "keywords": ["voter", "election", "epic", "electoral", "commission"],
        "description": "Voter ID / EPIC card",
    },

    # ── VEHICLE / MOTOR INSURANCE ──
    "bike_rc": {
        "category": "vehicle",
        "label": "Bike Registration Certificate",
        "keywords": ["registration", "certificate", "rc", "two wheeler", "motorcycle", "bike", "scooter", "vehicle"],
        "description": "Two-wheeler registration certificate (RC)",
    },
    "car_rc": {
        "category": "vehicle",
        "label": "Car Registration Certificate",
        "keywords": ["registration", "certificate", "rc", "car", "four wheeler", "vehicle", "motor", "chassis"],
        "description": "Four-wheeler registration certificate (RC)",
    },
    "fir": {
        "category": "vehicle",
        "label": "FIR / Police Report",
        "keywords": ["fir", "first information", "police", "station", "complaint", "theft", "accident"],
        "description": "FIR or police report for motor claim",
    },
    "surveyor_report": {
        "category": "vehicle",
        "label": "Surveyor Report",
        "keywords": ["surveyor", "survey", "assessment", "damage", "estimate", "repair", "inspection"],
        "description": "Motor surveyor / damage assessment report",
    },
    "repair_estimate": {
        "category": "vehicle",
        "label": "Repair Estimate / Bill",
        "keywords": ["repair", "estimate", "garage", "workshop", "labour", "spare", "painting"],
        "description": "Vehicle repair estimate or final bill",
    },

    # ── INSURANCE ──
    "insurance_policy": {
        "category": "insurance",
        "label": "Insurance Policy",
        "keywords": ["policy", "insured", "premium", "sum insured", "cover", "schedule", "endorsement"],
        "description": "Insurance policy document / schedule",
    },
    "claim_form": {
        "category": "insurance",
        "label": "Claim Form",
        "keywords": ["claim", "form", "intimation", "tpa", "cashless", "reimbursement"],
        "description": "Insurance claim form / intimation",
    },
    "pre_auth_form": {
        "category": "insurance",
        "label": "Pre-Authorization Form",
        "keywords": ["pre-auth", "preauth", "authorization", "cashless", "network hospital"],
        "description": "Pre-authorization / cashless request form",
    },

    # ── FINANCIAL ──
    "bank_statement": {
        "category": "financial",
        "label": "Bank Statement",
        "keywords": ["bank", "statement", "account", "balance", "transaction", "credit", "debit"],
        "description": "Bank account statement",
    },
    "invoice": {
        "category": "financial",
        "label": "Invoice / Receipt",
        "keywords": ["invoice", "receipt", "bill", "gst", "tax", "amount", "payment"],
        "description": "Invoice or payment receipt",
    },
}


def get_all_types() -> List[str]:
    """Return all document type keys."""
    return list(DOCUMENT_TAXONOMY.keys())


def get_type_labels() -> Dict[str, str]:
    """Return {type_key: human_label} mapping."""
    return {k: v["label"] for k, v in DOCUMENT_TAXONOMY.items()}


def classify_by_keywords(text: str) -> Tuple[str, float]:
    """
    Rule-based fallback classifier using keyword matching on OCR text.
    Returns (doc_type_key, confidence).
    """
    if not text:
        return "unknown", 0.0

    text_lower = text.lower()
    scores: Dict[str, int] = {}

    for doc_type, info in DOCUMENT_TAXONOMY.items():
        score = 0
        for kw in info["keywords"]:
            if kw.lower() in text_lower:
                score += 1
        if score > 0:
            scores[doc_type] = score

    if not scores:
        return "unknown", 0.0

    best = max(scores, key=scores.get)
    max_possible = len(DOCUMENT_TAXONOMY[best]["keywords"])
    confidence = min(scores[best] / max(max_possible, 1), 1.0)

    return best, round(confidence, 2)


def get_category(doc_type: str) -> str:
    """Return category for a document type key."""
    info = DOCUMENT_TAXONOMY.get(doc_type)
    if info:
        return info["category"]
    # Fuzzy match
    dt_lower = doc_type.lower().replace(" ", "_").replace("-", "_")
    for key, info in DOCUMENT_TAXONOMY.items():
        if key in dt_lower or dt_lower in key:
            return info["category"]
    return "other"


def get_label(doc_type: str) -> str:
    """Return human-readable label for a document type key."""
    info = DOCUMENT_TAXONOMY.get(doc_type)
    if info:
        return info["label"]
    # Fuzzy
    dt_lower = doc_type.lower().replace(" ", "_").replace("-", "_")
    for key, info in DOCUMENT_TAXONOMY.items():
        if key in dt_lower or dt_lower in key:
            return info["label"]
    return doc_type.replace("_", " ").title()


def get_extraction_prompt(doc_type: str) -> str:
    """
    Return a tailored extraction prompt for the given document type.
    This is used by the VLM engine to get the right JSON schema per doc type.
    """

    prompts = {
        # ── MEDICAL ──
        "discharge_summary": """Extract all data from this hospital discharge summary.

Return JSON:
{
    "patient_name": "",
    "age": "",
    "gender": "",
    "hospital_name": "",
    "uhid": "",
    "ip_number": "",
    "date_of_admission": "",
    "date_of_discharge": "",
    "diagnosis": "",
    "icd_code": "",
    "procedures": [],
    "treating_doctor": "",
    "department": "",
    "room_type": "",
    "condition_at_discharge": "",
    "follow_up_date": "",
    "medications": [],
    "total_amount": 0,
    "history_of_present_illness": "",
    "investigation_findings": ""
}
Use null for missing fields. Extract exact values as shown in the document.""",

        "hospital_bill": """Extract all data from this hospital bill / receipt.

Return JSON:
{
    "hospital_name": "",
    "patient_name": "",
    "bill_number": "",
    "bill_date": "",
    "admission_date": "",
    "discharge_date": "",
    "uhid": "",
    "room_charges": 0,
    "doctor_fees": 0,
    "nursing_charges": 0,
    "medicine_charges": 0,
    "investigation_charges": 0,
    "ot_charges": 0,
    "consumables": 0,
    "subtotal": 0,
    "discount": 0,
    "tax_gst": 0,
    "total_amount": 0,
    "amount_paid": 0,
    "balance_due": 0,
    "payment_mode": "",
    "line_items": [{"description": "", "amount": 0}]
}
Use null for missing fields. Extract exact amounts in INR.""",

        "prescription": """Extract all data from this medical prescription.

Return JSON:
{
    "doctor_name": "",
    "doctor_registration": "",
    "clinic_hospital": "",
    "patient_name": "",
    "date": "",
    "diagnosis": "",
    "medications": [{"name": "", "dosage": "", "frequency": "", "duration": ""}],
    "instructions": "",
    "follow_up": ""
}
Use null for missing fields.""",

        "lab_report": """Extract all data from this lab / pathology report.

Return JSON:
{
    "lab_name": "",
    "patient_name": "",
    "age": "",
    "gender": "",
    "sample_date": "",
    "report_date": "",
    "referred_by": "",
    "sample_id": "",
    "tests": [{"test_name": "", "result": "", "unit": "", "reference_range": "", "flag": ""}],
    "summary": ""
}
Use null for missing fields. Extract exact values.""",

        "death_certificate": """Extract all data from this death certificate.

Return JSON:
{
    "full_name": "",
    "date_of_death": "",
    "place_of_death": "",
    "cause_of_death": "",
    "age_at_death": "",
    "gender": "",
    "father_husband_name": "",
    "address": "",
    "registration_number": "",
    "registration_date": "",
    "registrar_name": "",
    "issuing_authority": ""
}
Use null for missing fields.""",

        # ── IDENTITY ──
        "aadhaar_card": """Extract all data from this Aadhaar card.

Return JSON:
{
    "full_name": "",
    "aadhaar_number": "",
    "date_of_birth": "",
    "gender": "",
    "address": "",
    "father_name": "",
    "vid": "",
    "issue_date": ""
}
Use null for missing fields. Mask Aadhaar to show only last 4 digits (XXXX XXXX 1234).""",

        "pan_card": """Extract all data from this PAN card.

Return JSON:
{
    "full_name": "",
    "father_name": "",
    "date_of_birth": "",
    "pan_number": "",
    "signature_present": true
}
Use null for missing fields. PAN format: ABCDE1234F.""",

        "driving_license": """Extract all data from this Driving License.

Return JSON:
{
    "full_name": "",
    "dl_number": "",
    "date_of_birth": "",
    "blood_group": "",
    "address": "",
    "issue_date": "",
    "validity_transport": "",
    "validity_non_transport": "",
    "vehicle_classes": [],
    "issuing_rto": "",
    "father_husband_name": "",
    "photo_present": true
}
Use null for missing fields.""",

        "passport": """Extract all data from this passport.

Return JSON:
{
    "full_name": "",
    "passport_number": "",
    "nationality": "",
    "date_of_birth": "",
    "gender": "",
    "place_of_birth": "",
    "date_of_issue": "",
    "date_of_expiry": "",
    "place_of_issue": "",
    "father_name": "",
    "mother_name": "",
    "address": "",
    "mrz_line_1": "",
    "mrz_line_2": ""
}
Use null for missing fields.""",

        "voter_id": """Extract all data from this Voter ID / EPIC card.

Return JSON:
{
    "full_name": "",
    "epic_number": "",
    "father_husband_name": "",
    "date_of_birth": "",
    "gender": "",
    "address": "",
    "part_number": "",
    "assembly_constituency": ""
}
Use null for missing fields.""",

        # ── VEHICLE ──
        "bike_rc": """Extract all data from this two-wheeler Registration Certificate (RC).

Return JSON:
{
    "registration_number": "",
    "owner_name": "",
    "father_husband_name": "",
    "address": "",
    "vehicle_class": "",
    "maker_model": "",
    "fuel_type": "",
    "engine_number": "",
    "chassis_number": "",
    "manufacturing_year": "",
    "registration_date": "",
    "fitness_upto": "",
    "insurance_upto": "",
    "rto_name": "",
    "cubic_capacity": "",
    "seating_capacity": "",
    "color": ""
}
Use null for missing fields.""",

        "car_rc": """Extract all data from this four-wheeler Registration Certificate (RC).

Return JSON:
{
    "registration_number": "",
    "owner_name": "",
    "father_husband_name": "",
    "address": "",
    "vehicle_class": "",
    "maker_model": "",
    "fuel_type": "",
    "engine_number": "",
    "chassis_number": "",
    "manufacturing_year": "",
    "registration_date": "",
    "fitness_upto": "",
    "insurance_upto": "",
    "tax_upto": "",
    "rto_name": "",
    "cubic_capacity": "",
    "seating_capacity": "",
    "gross_vehicle_weight": "",
    "color": "",
    "hypothecated_to": ""
}
Use null for missing fields.""",

        "fir": """Extract all data from this FIR / Police Report.

Return JSON:
{
    "fir_number": "",
    "police_station": "",
    "district": "",
    "date_of_fir": "",
    "date_of_incident": "",
    "time_of_incident": "",
    "place_of_incident": "",
    "complainant_name": "",
    "complainant_address": "",
    "offence_sections": [],
    "description_of_incident": "",
    "vehicle_number": "",
    "accused_details": "",
    "investigating_officer": ""
}
Use null for missing fields.""",

        "surveyor_report": """Extract all data from this motor surveyor report.

Return JSON:
{
    "surveyor_name": "",
    "surveyor_license": "",
    "survey_date": "",
    "vehicle_registration": "",
    "vehicle_make_model": "",
    "owner_name": "",
    "policy_number": "",
    "insurer": "",
    "date_of_accident": "",
    "place_of_accident": "",
    "nature_of_damage": "",
    "damaged_parts": [],
    "repair_replace_recommendation": [],
    "estimated_cost": 0,
    "salvage_value": 0,
    "net_assessment": 0,
    "depreciation_applied": "",
    "remarks": ""
}
Use null for missing fields.""",

        "repair_estimate": """Extract all data from this vehicle repair estimate / bill.

Return JSON:
{
    "garage_name": "",
    "vehicle_registration": "",
    "vehicle_make_model": "",
    "owner_name": "",
    "estimate_date": "",
    "labour_charges": 0,
    "spare_parts": [{"part_name": "", "quantity": 0, "amount": 0}],
    "painting_charges": 0,
    "total_labour": 0,
    "total_parts": 0,
    "gst": 0,
    "total_amount": 0,
    "remarks": ""
}
Use null for missing fields. Extract amounts in INR.""",

        # ── INSURANCE ──
        "insurance_policy": """Extract all data from this insurance policy document.

Return JSON:
{
    "insurer_name": "",
    "policy_number": "",
    "policy_type": "",
    "policyholder_name": "",
    "insured_name": "",
    "date_of_birth": "",
    "sum_insured": 0,
    "premium_amount": 0,
    "policy_start_date": "",
    "policy_end_date": "",
    "nominee_name": "",
    "nominee_relation": "",
    "coverage_details": [],
    "exclusions": [],
    "deductible": 0,
    "co_payment": "",
    "tpa_name": "",
    "plan_name": ""
}
Use null for missing fields.""",

        "claim_form": """Extract all data from this insurance claim form.

Return JSON:
{
    "claim_number": "",
    "policy_number": "",
    "insured_name": "",
    "claim_type": "",
    "date_of_claim": "",
    "date_of_incident": "",
    "hospital_name": "",
    "diagnosis": "",
    "treating_doctor": "",
    "estimated_amount": 0,
    "claim_amount": 0,
    "tpa_id": "",
    "pre_auth_number": "",
    "admission_type": "",
    "declaration_signed": true
}
Use null for missing fields.""",

        "pre_auth_form": """Extract all data from this pre-authorization / cashless form.

Return JSON:
{
    "insurer_name": "",
    "tpa_name": "",
    "pre_auth_number": "",
    "policy_number": "",
    "patient_name": "",
    "hospital_name": "",
    "treating_doctor": "",
    "diagnosis": "",
    "proposed_treatment": "",
    "estimated_cost": 0,
    "room_type_requested": "",
    "expected_days": "",
    "date_of_admission": "",
    "date_of_request": "",
    "status": ""
}
Use null for missing fields.""",

        # ── FINANCIAL ──
        "bank_statement": """Extract all data from this bank statement.

Return JSON:
{
    "bank_name": "",
    "account_number": "",
    "account_holder": "",
    "ifsc_code": "",
    "statement_period_from": "",
    "statement_period_to": "",
    "opening_balance": 0,
    "closing_balance": 0,
    "total_credits": 0,
    "total_debits": 0,
    "transactions": [{"date": "", "description": "", "amount": 0, "type": "credit|debit", "balance": 0}]
}
Use null for missing fields. Extract amounts in INR.""",

        "invoice": """Extract all data from this invoice / receipt.

Return JSON:
{
    "invoice_number": "",
    "invoice_date": "",
    "vendor_name": "",
    "vendor_gstin": "",
    "buyer_name": "",
    "line_items": [{"description": "", "quantity": 0, "rate": 0, "amount": 0}],
    "subtotal": 0,
    "cgst": 0,
    "sgst": 0,
    "igst": 0,
    "total_amount": 0,
    "payment_mode": ""
}
Use null for missing fields. Extract amounts in INR.""",
    }

    # Normalize key
    key = doc_type.lower().replace(" ", "_").replace("-", "_")
    if key in prompts:
        return prompts[key]

    # Fuzzy match
    for pkey in prompts:
        if pkey in key or key in pkey:
            return prompts[pkey]

    # Generic fallback
    return """Extract all structured data from this document.

Return JSON with:
- document_type: what kind of document this is
- title: document title
- date: any dates found
- names: any person or organization names
- key_values: dictionary of important label-value pairs
- tables: any tabular data as list of row objects
- amounts: any monetary amounts found
- id_numbers: any ID/reference numbers

Use null for missing fields."""

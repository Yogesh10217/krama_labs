from typing import Dict, List

# Canonical Document Taxonomy for Krama AI
# Extracted from Indian Insurance Domain

DOCUMENT_TAXONOMY: Dict[str, Dict] = {
    # ── FALLBACK ──
    "unknown": {
        "category": "other",
        "label": "Unknown",
        "keywords": [],
        "description": "Unclassified or unknown document type",
    },

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
    """Return all canonical document type keys."""
    return list(DOCUMENT_TAXONOMY.keys())

def is_valid_type(doc_type: str) -> bool:
    """Check if a document type is in the canonical taxonomy."""
    return doc_type in DOCUMENT_TAXONOMY

def get_type_label(doc_type: str) -> str:
    """Return the human-readable label for a document type key."""
    info = DOCUMENT_TAXONOMY.get(doc_type)
    if info:
        return info["label"]
    return "Unknown"

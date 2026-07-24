from typing import Dict, Optional
from app.extraction.schemas import DocumentSchema, FieldDefinition
from app.core.exceptions import KramaException

class ExtractionSchemaUnavailableException(KramaException):
    def __init__(self, document_type: str):
        super().__init__(
            status_code=400,
            code="EXTRACTION_SCHEMA_UNAVAILABLE",
            message=f"No extraction schema available for document type: {document_type}"
        )

# Extendable Field Registry
_REGISTRY: Dict[str, DocumentSchema] = {}

def register_schema(document_type: str, schema: DocumentSchema):
    _REGISTRY[document_type] = schema

def get_schema(document_type: str) -> DocumentSchema:
    schema = _REGISTRY.get(document_type)
    if not schema:
        raise ExtractionSchemaUnavailableException(document_type)
    return schema

# Hardcoded initial schemas based on Krama AI taxonomy
register_schema("aadhaar_card", DocumentSchema(
    schema_name="aadhaar_card_extraction",
    schema_version="1.0",
    fields=[
        FieldDefinition(name="aadhaar_number", display_name="Aadhaar Number", data_type="IDENTIFIER", required=True, aliases=["aadhaar", "uid", "vid"]),
        FieldDefinition(name="name", display_name="Name", data_type="STRING", required=True, aliases=["name", "name of"]),
        FieldDefinition(name="dob", display_name="Date of Birth", data_type="DATE", required=False, aliases=["dob", "yob", "year of birth"]),
        FieldDefinition(name="gender", display_name="Gender", data_type="STRING", required=False, aliases=["male", "female", "transgender"]),
    ]
))

register_schema("pan_card", DocumentSchema(
    schema_name="pan_card_extraction",
    schema_version="1.0",
    fields=[
        FieldDefinition(name="pan_number", display_name="PAN Number", data_type="IDENTIFIER", required=True, aliases=["pan", "permanent account number"]),
        FieldDefinition(name="name", display_name="Name", data_type="STRING", required=True, aliases=["name"]),
        FieldDefinition(name="father_name", display_name="Father's Name", data_type="STRING", required=False, aliases=["father", "father's name"]),
        FieldDefinition(name="dob", display_name="Date of Birth", data_type="DATE", required=False, aliases=["dob", "date of birth"]),
    ]
))

register_schema("invoice", DocumentSchema(
    schema_name="invoice_extraction",
    schema_version="1.0",
    fields=[
        FieldDefinition(name="invoice_number", display_name="Invoice Number", data_type="IDENTIFIER", required=True, aliases=["invoice no", "inv no", "bill no"]),
        FieldDefinition(name="invoice_date", display_name="Invoice Date", data_type="DATE", required=False, aliases=["date", "invoice date"]),
        FieldDefinition(name="total_amount", display_name="Total Amount", data_type="CURRENCY", required=True, aliases=["total", "amount", "grand total", "net amount"]),
        FieldDefinition(name="gst_number", display_name="GST Number", data_type="IDENTIFIER", required=False, aliases=["gstin", "gst no"]),
    ]
))

register_schema("hospital_bill", DocumentSchema(
    schema_name="hospital_bill_extraction",
    schema_version="1.0",
    fields=[
        FieldDefinition(name="bill_number", display_name="Bill Number", data_type="IDENTIFIER", required=True, aliases=["bill no", "receipt no", "invoice no"]),
        FieldDefinition(name="bill_date", display_name="Bill Date", data_type="DATE", required=False, aliases=["date", "bill date"]),
        FieldDefinition(name="patient_name", display_name="Patient Name", data_type="STRING", required=True, aliases=["patient name", "mr.", "mrs.", "name"]),
        FieldDefinition(name="total_amount", display_name="Total Amount", data_type="CURRENCY", required=True, aliases=["total", "amount", "net amount"]),
        FieldDefinition(name="hospital_name", display_name="Hospital Name", data_type="STRING", required=False, aliases=[]),
    ]
))

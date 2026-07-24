import pytest
import uuid
from typing import Generator
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.domain.enums import DocumentStatus, ValidationStatus
from app.db.models.document import Document
from app.db.models.page import Page
from app.db.models.ocr import OCRPageResult, OCRRegion
from app.db.models.extraction import ExtractionRun, ExtractedField, FieldEvidence
from app.db.models.validation import ValidationRun, ValidatedField, ValidationEvidence
from app.db.models.classification import DocumentClassification

from app.services.validation_service import ValidationService
from app.core.exceptions import DocumentNotReadyForValidationException

def test_validation_eligibility_fails_if_not_extracted(db_session: Session, test_org):
    doc_id = uuid.uuid4()
    doc = Document(id=doc_id, organization_id=test_org.id, claim_id=uuid.uuid4(), status=DocumentStatus.CLASSIFIED, original_filename="test.pdf")
    db_session.add(doc)
    db_session.commit()
    
    service = ValidationService(db=db_session, storage=None)
    with pytest.raises(DocumentNotReadyForValidationException):
        service.validate_document(test_org.id, doc_id)

class FakeStorage:
    def save_stream(self, key, stream):
        pass
    def delete(self, key):
        pass
    def exists(self, key):
        return True

def test_rule_validator_tiers(db_session: Session, test_org):
    mock_storage = FakeStorage()
    # Setup test data
    doc_id = uuid.uuid4()
    doc = Document(id=doc_id, organization_id=test_org.id, claim_id=uuid.uuid4(), status=DocumentStatus.EXTRACTED, original_filename="test.pdf")
    db_session.add(doc)
    
    page1 = Page(document_id=doc_id, page_number=1, status="PROCESSED", storage_key="p1")
    page2 = Page(document_id=doc_id, page_number=2, status="PROCESSED", storage_key="p2")
    db_session.add_all([page1, page2])
    db_session.flush()

    ocr_p1 = OCRPageResult(page_id=page1.id, engine="test", engine_version="1", language="en", full_text="Invoice No: 1234 Total: 50.00")
    ocr_p2 = OCRPageResult(page_id=page2.id, engine="test", engine_version="1", language="en", full_text="Terms: Net 30")
    db_session.add_all([ocr_p1, ocr_p2])
    db_session.flush()

    # OCR Regions
    reg1 = OCRRegion(id=uuid.uuid4(), ocr_result_id=ocr_p1.id, region_index=0, reading_order=0, text="Invoice No: 1234", confidence=0.9, x1=0, y1=0, x2=10, y2=10)
    reg2 = OCRRegion(id=uuid.uuid4(), ocr_result_id=ocr_p1.id, region_index=1, reading_order=1, text="Total: 50.00", confidence=0.9, x1=0, y1=20, x2=10, y2=30)
    reg3 = OCRRegion(id=uuid.uuid4(), ocr_result_id=ocr_p2.id, region_index=0, reading_order=0, text="Terms: Net 30", confidence=0.9, x1=0, y1=0, x2=10, y2=10)
    db_session.add_all([reg1, reg2, reg3])
    db_session.flush()

    cls = DocumentClassification(
        organization_id=test_org.id, 
        document_id=doc.id, 
        document_type="invoice", 
        classifier_name="test", 
        classifier_version="1", 
        confidence=1.0, 
        artifact_storage_key="test_cls"
    )
    db_session.add(cls)
    db_session.flush()

    # Extraction
    extr = ExtractionRun(
        organization_id=test_org.id, 
        document_id=doc.id, 
        classification_id=cls.id, 
        extractor_name="test", 
        extractor_version="1", 
        schema_name="invoice_extraction", 
        schema_version="1", 
        status="COMPLETED", 
        artifact_storage_key="test"
    )
    db_session.add(extr)
    db_session.flush()

    # Field 1: Supported (Tier 1 Exact Match)
    f1 = ExtractedField(extraction_run_id=extr.id, field_name="invoice_no", raw_value="Invoice No: 1234", normalized_value="1234", data_type="string")
    db_session.add(f1)
    db_session.flush()
    ev1 = FieldEvidence(extracted_field_id=f1.id, page_id=page1.id, ocr_region_id=reg1.id, confidence=1.0, evidence_type="text")
    db_session.add(ev1)

    # Field 2: Supported (Tier 2 Fallback - contained match on page 1)
    f2 = ExtractedField(extraction_run_id=extr.id, field_name="total", raw_value="50.00", normalized_value="50", data_type="number")
    db_session.add(f2)
    db_session.flush()
    # Evidence points to reg1, but value is in reg2 (same page)
    ev2 = FieldEvidence(extracted_field_id=f2.id, page_id=page1.id, ocr_region_id=reg1.id, confidence=0.5, evidence_type="text")
    db_session.add(ev2)

    # Field 3: Supported (Tier 3 Fallback - exact match on page 2)
    f3 = ExtractedField(extraction_run_id=extr.id, field_name="terms", raw_value="Terms: Net 30", normalized_value="net30", data_type="string")
    db_session.add(f3)
    db_session.flush()
    # No evidence provided by extraction
    
    # Field 4: Unsupported
    f4 = ExtractedField(extraction_run_id=extr.id, field_name="missing", raw_value="Missing Value", normalized_value="missing", data_type="string")
    db_session.add(f4)

    db_session.commit()

    service = ValidationService(db=db_session, storage=mock_storage)
    run = service.validate_document(test_org.id, doc_id)

    assert run.status == "COMPLETED"
    
    # Refresh to check statuses
    db_session.refresh(run)
    fields = {f.extracted_field.field_name: f for f in run.fields}
    
    assert fields["invoice_no"].validation_status == ValidationStatus.SUPPORTED
    assert fields["invoice_no"].evidence[0].support_type == "exact_match"
    
    assert fields["total"].validation_status == ValidationStatus.SUPPORTED
    assert fields["total"].evidence[0].support_type == "contained_match_page_fallback"
    
    assert fields["terms"].validation_status == ValidationStatus.SUPPORTED
    assert fields["terms"].evidence[0].support_type == "exact_match_doc_fallback"
    
    assert fields["missing"].validation_status == ValidationStatus.MISSING_EVIDENCE

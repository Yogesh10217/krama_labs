import uuid
import pytest
from app.classification.normalizer import ClassificationNormalizer
from app.classification.base import ClassificationResult, ClassificationInput
from app.classification.rules import RulesClassifier

def test_classification_normalizer_valid():
    raw = ClassificationResult(
        document_type="invoice",
        confidence=0.85,
        classifier_name="test",
        classifier_version="1.0",
        evidence=[{"match": "yes"}]
    )
    result = ClassificationNormalizer.normalize(raw)
    assert result.document_type == "invoice"
    assert result.confidence == 0.85

def test_classification_normalizer_invalid_confidence():
    raw = ClassificationResult(
        document_type="invoice",
        confidence=float('inf'),
        classifier_name="test",
        classifier_version="1.0"
    )
    result = ClassificationNormalizer.normalize(raw)
    assert result.confidence == 0.0

def test_classification_normalizer_unknown_taxonomy():
    raw = ClassificationResult(
        document_type="made_up_type",
        confidence=0.9,
        classifier_name="test",
        classifier_version="1.0"
    )
    result = ClassificationNormalizer.normalize(raw)
    assert result.document_type == "unknown"
    assert result.confidence == 0.0  # penalize confidence for fallback

def test_rules_classifier_empty_input():
    classifier = RulesClassifier()
    input_data = ClassificationInput(
        document_id="123",
        original_filename="test.pdf",
        ocr_text="   \n  ",
        pages_text={1: "   "}
    )
    res = classifier.classify(input_data)
    assert res.document_type == "unknown"
    assert res.confidence == 0.0

def test_rules_classifier_match():
    classifier = RulesClassifier()
    input_data = ClassificationInput(
        document_id="123",
        original_filename="test.pdf",
        ocr_text="this is a hospital bill with charges and receipt",
        pages_text={1: "this is a hospital bill with charges and receipt"}
    )
    res = classifier.classify(input_data)
    assert res.document_type == "hospital_bill"
    assert res.confidence > 0.0

from app.services.classification_service import ClassificationService, DocumentNotReadyForClassificationException
from app.db.models.document import Document
from app.db.models.ocr import OCRPageResult
from app.domain.enums import DocumentStatus
from app.storage.factory import get_storage_provider

def test_classification_service_eligibility(db_session, test_org):
    import uuid
    # Setup document in OCR_PARTIAL
    doc = Document(
        organization_id=test_org.id,
        claim_id=uuid.uuid4(),
        original_filename="test.pdf",
        status=DocumentStatus.OCR_PARTIAL
    )
    db_session.add(doc)
    db_session.commit()

    storage = get_storage_provider()
    service = ClassificationService(db=db_session, storage=storage)

    with pytest.raises(DocumentNotReadyForClassificationException):
        service.classify_document(test_org.id, doc.id)

    # Status should be preserved
    db_session.refresh(doc)
    assert doc.status == DocumentStatus.OCR_PARTIAL

def test_classification_service_success(db_session, test_org):
    import uuid
    # Setup document in OCR_COMPLETED
    doc = Document(
        organization_id=test_org.id,
        claim_id=uuid.uuid4(),
        original_filename="invoice.pdf",
        status=DocumentStatus.OCR_COMPLETED
    )
    db_session.add(doc)
    db_session.commit()

    # Add OCR data
    from app.db.models.page import Page
    page = Page(document_id=doc.id, page_number=1, status="OCR_COMPLETED")
    db_session.add(page)
    db_session.commit()

    ocr = OCRPageResult(
        page_id=page.id,
        full_text="invoice total amount receipt gst tax payment",
        engine="fake",
        engine_version="1.0",
        language="en"
    )
    db_session.add(ocr)
    db_session.commit()

    storage = get_storage_provider()
    service = ClassificationService(db=db_session, storage=storage)

    classification = service.classify_document(test_org.id, doc.id)

    assert classification.document_type == "invoice"
    assert classification.confidence > 0
    assert classification.artifact_storage_key is not None

    # Check document status
    db_session.refresh(doc)
    assert doc.status == DocumentStatus.CLASSIFIED
    assert doc.document_type == "invoice"  # Synchronized!

    # Idempotency
    classification2 = service.classify_document(test_org.id, doc.id)
    assert classification.id == classification2.id

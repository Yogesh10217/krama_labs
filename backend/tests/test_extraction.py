import pytest
import uuid
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.domain.enums import DocumentStatus, JobStageStatus, ExtractionStatus
from app.db.models.document import Document
from app.db.models.classification import DocumentClassification
from app.db.models.extraction import ExtractionRun, ExtractedField
from app.db.models.job import Job
from app.db.models.job_stage import JobStage
from app.db.models.page import Page
from app.db.models.ocr import OCRPageResult, OCRRegion
from app.services.extraction_service import ExtractionService, DocumentNotReadyForExtractionException, ExtractionFailedException
from tests.fakes.fake_extractor import FakeExtractor

@pytest.fixture
def fake_extractor():
    return FakeExtractor()

@pytest.fixture
def mock_storage_provider():
    storage = MagicMock()
    storage.exists.return_value = True
    return storage

@pytest.fixture
def ocr_completed_document(db_session, test_org):
    doc = Document(
        organization_id=test_org.id,
        claim_id=uuid.uuid4(),
        status=DocumentStatus.OCR_COMPLETED,
        page_count=1,
        original_filename="test.pdf"
    )
    db_session.add(doc)
    db_session.commit()
    
    page = Page(document_id=doc.id, page_number=1, status="OCR_COMPLETED")
    db_session.add(page)
    db_session.commit()
    
    ocr = OCRPageResult(page_id=page.id, full_text="fake text", engine="fake", engine_version="1.0", language="en")
    db_session.add(ocr)
    db_session.commit()
    
    region = OCRRegion(ocr_result_id=ocr.id, region_index=0, reading_order=0, text="1234 5678 9012", x1=0.0, y1=0.0, x2=1.0, y2=1.0, confidence=1.0)
    db_session.add(region)
    db_session.commit()
    
    return doc

@pytest.fixture
def classified_document(db_session, test_org, ocr_completed_document):
    doc = ocr_completed_document
    doc.status = DocumentStatus.CLASSIFIED
    
    classification = DocumentClassification(
        document_id=doc.id,
        organization_id=test_org.id,
        classifier_name="rules",
        classifier_version="1.0",
        document_type="aadhaar_card",
        confidence=0.9,
        artifact_storage_key="test_key"
    )
    db_session.add(classification)
    
    job = Job(organization_id=test_org.id, document_id=doc.id, job_type="DOCUMENT_PROCESSING")
    db_session.add(job)
    db_session.commit()
    
    return doc

def test_extraction_success(db_session, test_org, classified_document, fake_extractor, mock_storage_provider):
    service = ExtractionService(db_session, mock_storage_provider)
    
    with patch("app.services.extraction_service.ProviderFactory.get", return_value=fake_extractor):
        run = service.extract_document(test_org.id, classified_document.id)
        
    assert run is not None
    assert run.status == ExtractionStatus.COMPLETED
    assert run.schema_name == "aadhaar_card_extraction"
    assert len(run.fields) == 1
    assert run.fields[0].field_name == "aadhaar_number"
    assert run.fields[0].normalized_value == "1234 5678 9012"
    
    db_session.refresh(classified_document)
    assert classified_document.status == DocumentStatus.EXTRACTED
    
    job = db_session.query(Job).filter(Job.document_id == classified_document.id).first()
    stage = db_session.query(JobStage).filter(JobStage.job_id == job.id, JobStage.stage_name == "EXTRACT").first()
    assert stage is not None
    assert stage.status == JobStageStatus.SUCCEEDED
    
    assert mock_storage_provider.save_stream.called

def test_extraction_not_ready(db_session, test_org, ocr_completed_document, mock_storage_provider):
    service = ExtractionService(db_session, mock_storage_provider)
    with pytest.raises(DocumentNotReadyForExtractionException):
        service.extract_document(test_org.id, ocr_completed_document.id)

def test_extraction_failure_compensation(db_session, test_org, classified_document, fake_extractor, mock_storage_provider):
    service = ExtractionService(db_session, mock_storage_provider)
    fake_extractor.should_fail = True
    
    with patch("app.services.extraction_service.ProviderFactory.get", return_value=fake_extractor):
        with pytest.raises(ExtractionFailedException):
            service.extract_document(test_org.id, classified_document.id)
            
    db_session.refresh(classified_document)
    assert classified_document.status == DocumentStatus.EXTRACTION_FAILED
    
    run = db_session.query(ExtractionRun).filter(ExtractionRun.document_id == classified_document.id).first()
    assert run is None
    # Artifact was never saved since failure occurred during extraction, so delete should not be called
    assert not mock_storage_provider.delete.called

def test_extraction_idempotency(db_session, test_org, classified_document, fake_extractor, mock_storage_provider):
    service = ExtractionService(db_session, mock_storage_provider)
    
    with patch("app.services.extraction_service.ProviderFactory.get", return_value=fake_extractor):
        run1 = service.extract_document(test_org.id, classified_document.id)
        run2 = service.extract_document(test_org.id, classified_document.id)
        
    assert run1.id == run2.id
    assert mock_storage_provider.save_stream.call_count == 1

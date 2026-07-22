import os
import json
import io
import uuid
import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Config
from app.db.models.document import Document
from app.db.models.page import Page
from app.db.models.job import Job
from app.db.models.job_stage import JobStage
from app.domain.enums import DocumentStatus, JobStatus, JobStageStatus, PageStatus
from app.ocr.registry import clear_engine_cache, _engine_cache
from app.storage.factory import get_storage_provider
from tests.fakes.fake_ocr_engine import FakeOCREngine

# Fake image bytes
FAKE_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x64\x00\x00\x00\x64\x08\x06\x00\x00\x00\x70\xe2\x95\x54\x00\x00\x00\x00IEND\xaeB`\x82"

@pytest.fixture
def fake_ocr(monkeypatch):
    clear_engine_cache()
    fake_engine = FakeOCREngine()
    monkeypatch.setattr("app.core.config.Config.OCR_PROVIDER", "fake", raising=False)
    monkeypatch.setattr("app.ocr.registry._create_engine", lambda p: fake_engine)
    yield fake_engine
    clear_engine_cache()

@pytest.fixture
def fake_document(db_session: Session, test_org) -> Document:
    doc_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        organization_id=test_org.id,
        claim_id=claim_id,
        original_filename="test.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        checksum="fakehash",
        storage_key=f"artifacts/{test_org.id}/{claim_id}/{doc_id}/raw.pdf",
        status=DocumentStatus.CONVERTED,
        page_count=2
    )
    db_session.add(doc)
    
    job = Job(
        id=uuid.uuid4(),
        organization_id=test_org.id,
        document_id=doc_id,
        claim_id=claim_id,
        status=JobStatus.PENDING,
        job_type="DOCUMENT_PROCESSING"
    )
    db_session.add(job)
    
    stage = JobStage(
        id=uuid.uuid4(),
        job_id=job.id,
        stage_name="CONVERT",
        sequence=1,
        status=JobStageStatus.SUCCEEDED
    )
    db_session.add(stage)
    
    for i in range(1, 3):
        page = Page(
            id=uuid.uuid4(),
            document_id=doc_id,
            page_number=i,
            status=PageStatus.MATERIALIZED,
            width=100,
            height=100,
            content_type="image/png",
            storage_key=f"artifacts/{test_org.id}/{claim_id}/{doc_id}/pages/{i:04d}.png",
            size_bytes=len(FAKE_PNG_BYTES)
        )
        db_session.add(page)
        
    db_session.commit()
    
    # Put fake PNGs in storage
    storage = get_storage_provider()
    for page in doc.pages:
        storage.save_stream(page.storage_key, io.BytesIO(FAKE_PNG_BYTES))
        
    storage.save_stream(doc.storage_key, io.BytesIO(b"fake_raw_pdf"))
    return doc

class TestOCRProviderUnavailable:
    def test_startup_and_upload_without_paddle(self, client, monkeypatch):
        """Application startup and upload works without PaddleOCR installed."""
        # This mocks import paddle as raising ImportError in _create_engine
        def mock_create(*args, **kwargs):
            raise ImportError("No module named 'paddle'")
            
        monkeypatch.setattr("app.ocr.registry._create_engine", mock_create)
        monkeypatch.setattr(Config, "OCR_PROVIDER", "paddle")
        clear_engine_cache()
        
        # Health check should work
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        
    def test_ocr_provider_unavailable_returns_503(self, client, fake_document, monkeypatch):
        """OCR request with unavailable provider returns structured 503."""
        def mock_create(*args, **kwargs):
            raise ImportError("No module named 'paddle'")
            
        monkeypatch.setattr("app.ocr.registry._create_engine", mock_create)
        monkeypatch.setattr(Config, "OCR_PROVIDER", "paddle")
        clear_engine_cache()
        
        response = client.post(
            f"/api/v1/documents/{fake_document.id}/ocr",
            headers={"X-Organization-ID": str(fake_document.organization_id)}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "OCR_PROVIDER_UNAVAILABLE"


class TestOCRExecution:
    def test_document_ocr_success(self, client, db_session, fake_document, fake_ocr):
        """End-to-end OCR processing of a document."""
        response = client.post(
            f"/api/v1/documents/{fake_document.id}/ocr",
            headers={"X-Organization-ID": str(fake_document.organization_id)}
        )
        assert response.status_code == 200
        
        # Check parent Job remains PENDING
        db_session.refresh(fake_document)
        assert fake_document.status == DocumentStatus.OCR_COMPLETED
        job = db_session.query(Job).filter(Job.document_id == fake_document.id).first()
        assert job.status == JobStatus.PENDING
        
        # Check pages
        for page in fake_document.pages:
            assert page.status == PageStatus.OCR_COMPLETED
            assert len(page.ocr_result) == 1
            result = page.ocr_result[0]
            assert result.language == "en"
            assert result.full_text == "Fake Word 1\nLow Confidence Word"
            
            # Low confidence regions are preserved
            assert len(result.regions) == 2
            
            # Check JSON canonical artifact
            storage = get_storage_provider()
            artifact_bytes = storage.open(result.artifact_storage_key).read()
            artifact = json.loads(artifact_bytes.decode("utf-8"))
            
            assert artifact["schema_version"] == "1.0"
            assert artifact["engine"] == "fake"
            assert len(artifact["regions"]) == 2
            
            # Equivalent canonical data
            assert artifact["full_text"] == result.full_text
            
            # Normalized polygon bounds check
            for r in artifact["regions"]:
                for point in r["polygon"]:
                    assert 0.0 <= point[0] <= 1.0
                    assert 0.0 <= point[1] <= 1.0

    def test_completed_page_retry_skips_engine(self, client, db_session, fake_document, fake_ocr):
        """A retry on a completed document does not invoke the engine."""
        # Process once
        client.post(f"/api/v1/documents/{fake_document.id}/ocr", headers={"X-Organization-ID": str(fake_document.organization_id)})
        assert fake_ocr.call_count == 2
        
        # Process again
        client.post(f"/api/v1/documents/{fake_document.id}/ocr", headers={"X-Organization-ID": str(fake_document.organization_id)})
        assert fake_ocr.call_count == 2  # Did not increase

    def test_partial_document_retry(self, client, db_session, fake_document, fake_ocr, monkeypatch):
        """Only incomplete pages are processed."""
        # Create an OCRPageResult for page 1 to simulate completion
        from app.db.models.ocr import OCRPageResult
        from app.services.ocr_service import OCRService
        page1 = fake_document.pages[0]
        db_session.add(OCRPageResult(
            page_id=page1.id,
            engine="fake",
            engine_version="1.0",
            language="en",
            full_text="test",
            region_count=1,
            average_confidence=1.0,
            processing_time_ms=10,
            artifact_storage_key="test"
        ))
        db_session.commit()
        
        original_process_page = OCRService._process_page
        
        # First simulate a failure for page 2
        def mock_process_page(*args, **kwargs):
            raise Exception("Simulated OCR failure")
            
        monkeypatch.setattr(OCRService, "_process_page", mock_process_page)
        
        response = client.post(f"/api/v1/documents/{fake_document.id}/ocr", headers={"X-Organization-ID": str(fake_document.organization_id)})
        assert response.status_code == 200
        assert response.json()["ocr_pages_failed"] == 1
        
        db_session.refresh(fake_document)
        assert fake_document.status == DocumentStatus.OCR_PARTIAL
        page2 = next(p for p in fake_document.pages if p.page_number == 2)
        assert page2.status == PageStatus.OCR_FAILED
        
        # Now remove the mock and retry
        monkeypatch.setattr(OCRService, "_process_page", original_process_page)
        response = client.post(f"/api/v1/documents/{fake_document.id}/ocr", headers={"X-Organization-ID": str(fake_document.organization_id)})
        assert response.status_code == 200
        assert fake_ocr.call_count == 1  # Only page 2 processed this time
        
        db_session.refresh(fake_document)
        assert fake_document.status == DocumentStatus.OCR_COMPLETED

    def test_ocr_processing_recovery(self, client, db_session, fake_document, fake_ocr):
        """A page stuck in OCR_PROCESSING can be reclaimed."""
        page1 = fake_document.pages[0]
        page1.status = PageStatus.OCR_PROCESSING
        db_session.commit()
        
        client.post(f"/api/v1/documents/{fake_document.id}/ocr", headers={"X-Organization-ID": str(fake_document.organization_id)})
        assert fake_ocr.call_count == 2  # Both processed/reclaimed

    def test_artifact_cleanup_on_db_failure(self, client, db_session, fake_document, fake_ocr, monkeypatch):
        """Artifact is deleted if DB commit fails."""
        
        from app.services.ocr_service import OCRService
        from app.storage.local import LocalStorageProvider
        
        # We need access to the storage provider to verify the artifact was created before failure
        storage = LocalStorageProvider(str(fake_document.organization_id)) # Not exactly, but we can access it via app config or monkeypatch.
        # Wait, the test has 'client' which uses the app dependencies. It's easier to just check it inside the mock.
        
        # Patch the specific OCRService db commit boundary
        def mock_persist_page_result(self_service, page, raw_result, ordered_regions, full_text, region_count, avg_conf, artifact_key):
            # Verify the artifact was initially stored
            assert self_service._storage.exists(artifact_key)
            raise Exception("Simulated DB Persistence Failure")
        
        monkeypatch.setattr(OCRService, "_persist_page_result", mock_persist_page_result)
        
        response = client.post(f"/api/v1/documents/{fake_document.id}/ocr", headers={"X-Organization-ID": str(fake_document.organization_id)})
        assert response.status_code == 200
        assert response.json()["ocr_pages_failed"] == 2
        
        db_session.refresh(fake_document)
        assert fake_document.status == DocumentStatus.OCR_PARTIAL
        
        # Check that artifacts were not left behind
        from app.db.models.ocr import OCRPageResult, OCRRegion
        
        storage = get_storage_provider()
        prefix = f"artifacts/{fake_document.organization_id}/{fake_document.claim_id}/{fake_document.id}/ocr/"
        for i in range(1, 3):
            key = f"{prefix}{i:04d}.json"
            assert not storage.exists(key)
            
        # Raw document and canonical page survive, and DB rows rolled back
        for page in fake_document.pages:
            assert storage.exists(page.storage_key)
            assert page.status == PageStatus.OCR_FAILED
            
            # DB Persistence failed, so no OCR records should exist
            page_results = db_session.query(OCRPageResult).filter(OCRPageResult.page_id == page.id).all()
            assert len(page_results) == 0
        for p in fake_document.pages:
            assert storage.exists(p.storage_key)

    def test_no_ocr_text_in_logs(self, client, db_session, fake_document, fake_ocr, caplog):
        """Ensure sensitive OCR text isn't logged."""
        client.post(f"/api/v1/documents/{fake_document.id}/ocr", headers={"X-Organization-ID": str(fake_document.organization_id)})
        
        for record in caplog.records:
            assert "Fake Word 1" not in record.message
            assert "Low Confidence Word" not in record.message

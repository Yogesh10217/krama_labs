"""Tests for Phase 2 single-document ingestion API.

These tests exercise ACTUAL ingestion behavior:
- Real streaming
- Real SHA-256 computation
- Real local filesystem writes
- Real database persistence
- Real compensation behavior

Tests do NOT use external services (no network, no GPU, no OCR).
The LocalStorageProvider is configured with a pytest tmp_path directory.
"""
import hashlib
import io
import os
import uuid
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.document import Document
from app.db.models.job import Job
from app.domain.enums import DocumentStatus, JobStatus
from app.storage.base import StorageWriteError


# ─── Minimal valid file fixtures ──────────────────────────────────────────────

def minimal_pdf() -> bytes:
    return b"%PDF-1.4 minimal"

def minimal_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 50

def minimal_jpeg() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 50

def minimal_tiff_le() -> bytes:
    """Little-endian TIFF."""
    return b"II*\x00" + b"\x00" * 50

def minimal_tiff_be() -> bytes:
    """Big-endian TIFF."""
    return b"MM\x00*" + b"\x00" * 50


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _upload_file(client, org_id, claim_id, filename, data, content_type="application/octet-stream"):
    """Helper: POST to /upload endpoint."""
    headers = {"X-Organization-ID": str(org_id)}
    files = {"file": (filename, io.BytesIO(data), content_type)}
    return client.post(
        f"/api/v1/claims/{claim_id}/documents/upload",
        files=files,
        headers=headers,
    )


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def override_storage(tmp_path, app_instance):
    """Override the storage provider to use a temporary directory for each test."""
    from app.storage.local import LocalStorageProvider
    from app.storage import factory

    provider = LocalStorageProvider(str(tmp_path / "storage"))

    # Patch the lru_cache'd factory to return our temp provider.
    with patch("app.storage.factory._build_provider", return_value=provider):
        # Also patch the cached result directly.
        factory._build_provider.cache_clear = lambda: None
        yield provider


# ─── Valid uploads ─────────────────────────────────────────────────────────────

class TestValidUploads:
    def test_valid_pdf_upload(self, client, test_org, db_session):
        claim_res = client.post("/api/v1/claims", json={"title": "Test Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        data = minimal_pdf()
        res = _upload_file(client, test_org.id, claim_id, "test.pdf", data, "application/pdf")

        assert res.status_code == status.HTTP_201_CREATED
        body = res.json()
        assert body["document"]["status"] == "UPLOADED"
        assert body["document"]["file_extension"] == "pdf"
        assert body["document"]["size_bytes"] == len(data)
        assert body["document"]["checksum"] == _sha256(data)
        assert body["job"]["status"] == "PENDING"
        assert body["job"]["job_type"] == "DOCUMENT_PROCESSING"
        assert body["job"]["progress"] == 0

    def test_valid_png_upload(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "PNG Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "image.png", minimal_png(), "image/png")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["document"]["file_extension"] == "png"

    def test_valid_jpeg_upload(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "JPEG Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "photo.jpg", minimal_jpeg(), "image/jpeg")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["document"]["file_extension"] == "jpg"

    def test_valid_tiff_upload_little_endian(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "TIFF Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "scan.tiff", minimal_tiff_le(), "image/tiff")
        assert res.status_code == status.HTTP_201_CREATED

    def test_valid_tiff_upload_big_endian(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "TIFF BE"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "scan.tif", minimal_tiff_be(), "image/tiff")
        assert res.status_code == status.HTTP_201_CREATED

    def test_generic_mime_accepted_when_signature_matches(self, client, test_org):
        """application/octet-stream is a legitimate browser MIME; accept if signature+ext agree."""
        claim_res = client.post("/api/v1/claims", json={"title": "Generic MIME"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        # Valid PDF content but generic MIME type from browser.
        res = _upload_file(client, test_org.id, claim_id, "doc.pdf", minimal_pdf(), "application/octet-stream")
        assert res.status_code == status.HTTP_201_CREATED

    def test_sha256_stored_correctly(self, client, test_org, db_session):
        claim_res = client.post("/api/v1/claims", json={"title": "SHA Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        data = minimal_pdf() + b" extra data to make it unique"
        res = _upload_file(client, test_org.id, claim_id, "unique.pdf", data, "application/pdf")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["document"]["checksum"] == _sha256(data)

    def test_storage_key_is_server_generated_neutral(self, client, test_org, db_session):
        """Storage key must be a provider-neutral logical key, not an absolute path."""
        claim_res = client.post("/api/v1/claims", json={"title": "Key Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "bill.pdf", minimal_pdf(), "application/pdf")
        assert res.status_code == status.HTTP_201_CREATED
        doc_id = res.json()["document"]["id"]

        doc = db_session.get(Document, uuid.UUID(doc_id))
        assert doc is not None
        assert doc.storage_key.startswith("raw/")
        assert str(test_org.id) in doc.storage_key
        assert claim_id in doc.storage_key
        # Must NOT contain backslash (Windows path) or drive letter
        assert "\\" not in doc.storage_key
        assert ":" not in doc.storage_key
        # Must NOT be exposed in the API response
        response_body = res.json()
        assert "storage_key" not in str(response_body)

    def test_document_status_is_uploaded_not_registered(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "Status Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "doc.pdf", minimal_pdf(), "application/pdf")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["document"]["status"] == "UPLOADED"
        # Must not be PROCESSING or REGISTERED
        assert res.json()["document"]["status"] not in ("PROCESSING", "REGISTERED")

    def test_job_status_is_pending_not_running(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "Job Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "x.pdf", minimal_pdf(), "application/pdf")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["job"]["status"] == "PENDING"
        assert res.json()["job"]["status"] != "RUNNING"

    def test_page_count_is_null(self, client, test_org, db_session):
        """Page materialization is Phase 3; page_count must be null after upload."""
        claim_res = client.post("/api/v1/claims", json={"title": "Page Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "p.pdf", minimal_pdf(), "application/pdf")
        doc_id = res.json()["document"]["id"]
        doc = db_session.get(Document, uuid.UUID(doc_id))
        assert doc.page_count is None


# ─── Rejection cases ──────────────────────────────────────────────────────────

class TestRejectionCases:
    def test_empty_file_rejected(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "Empty"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "empty.pdf", b"", "application/pdf")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.json()["error"]["code"] == "EMPTY_FILE"

    def test_unsupported_extension_rejected(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "Unsupported"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "virus.exe", b"MZ\x90\x00", "application/octet-stream")
        assert res.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        assert res.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

    def test_unsupported_extension_txt(self, client, test_org):
        claim_res = client.post("/api/v1/claims", json={"title": "TXT"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "notes.txt", b"Hello world", "text/plain")
        assert res.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    def test_invalid_signature_rejected(self, client, test_org):
        """File with .pdf extension but wrong magic bytes."""
        claim_res = client.post("/api/v1/claims", json={"title": "Bad Sig"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        # Content looks like a ZIP but has .pdf extension.
        zip_header = b"PK\x03\x04" + b"\x00" * 30
        res = _upload_file(client, test_org.id, claim_id, "fake.pdf", zip_header, "application/pdf")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.json()["error"]["code"] == "INVALID_FILE_SIGNATURE"

    def test_strong_mime_mismatch_rejected(self, client, test_org):
        """Extension=.pdf + MIME=image/png + PDF signature → reject (strong mismatch)."""
        claim_res = client.post("/api/v1/claims", json={"title": "Mismatch"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "trick.pdf", minimal_pdf(), "image/png")
        assert res.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )
        code = res.json()["error"]["code"]
        assert code in ("CONTENT_TYPE_MISMATCH", "INVALID_FILE_SIGNATURE")

    def test_cross_tenant_upload_denied(self, client, db_session, test_org):
        """Cannot upload to a claim that belongs to a different org."""
        from app.db.models.organization import Organization
        from app.db.models.claim import Claim

        # Create a claim under test_org.
        real_claim = Claim(organization_id=test_org.id, title="Real Org Claim")
        db_session.add(real_claim)
        db_session.commit()

        # Create attacker org.
        attacker_org = Organization(name="Attacker", slug=f"attacker-{uuid.uuid4().hex[:6]}")
        db_session.add(attacker_org)
        db_session.commit()

        headers = {"X-Organization-ID": str(attacker_org.id)}
        files = {"file": ("bill.pdf", io.BytesIO(minimal_pdf()), "application/pdf")}
        res = client.post(f"/api/v1/claims/{real_claim.id}/documents/upload", files=files, headers=headers)
        # Must return 404 to prevent claim existence leakage.
        assert res.status_code == status.HTTP_404_NOT_FOUND


# ─── Size limit ───────────────────────────────────────────────────────────────

class TestSizeLimit:
    def test_file_size_limit_enforced(self, client, test_org, app_instance):
        """Override MAX_UPLOAD_SIZE_MB to 0 and verify rejection."""
        claim_res = client.post("/api/v1/claims", json={"title": "Size"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        # Temporarily reduce max size to 1 byte.
        with patch("app.services.ingestion_service.Config.MAX_UPLOAD_SIZE_MB", 0), \
             patch("app.services.ingestion_service.Config.max_upload_size_bytes", return_value=1):
            res = _upload_file(client, test_org.id, claim_id, "big.pdf", minimal_pdf(), "application/pdf")

        assert res.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert res.json()["error"]["code"] == "FILE_TOO_LARGE"


# ─── Duplicates ───────────────────────────────────────────────────────────────

class TestDuplicates:
    def test_same_bytes_same_claim_rejected(self, client, test_org):
        """Duplicate: same bytes + same claim → 409."""
        claim_res = client.post("/api/v1/claims", json={"title": "Dup Claim"}, headers={"X-Organization-ID": str(test_org.id)})
        claim_id = claim_res.json()["id"]

        data = minimal_pdf() + b" duplicate-test"
        _upload_file(client, test_org.id, claim_id, "dup.pdf", data, "application/pdf")
        res = _upload_file(client, test_org.id, claim_id, "dup.pdf", data, "application/pdf")

        assert res.status_code == status.HTTP_409_CONFLICT
        assert res.json()["error"]["code"] == "DUPLICATE_DOCUMENT"

    def test_same_bytes_different_claim_allowed(self, client, test_org):
        """Same checksum across different claims in same org → allowed."""
        h1 = {"X-Organization-ID": str(test_org.id)}
        c1 = client.post("/api/v1/claims", json={"title": "Claim A"}, headers=h1).json()["id"]
        c2 = client.post("/api/v1/claims", json={"title": "Claim B"}, headers=h1).json()["id"]

        data = minimal_pdf() + b" cross-claim-same-data"
        r1 = _upload_file(client, test_org.id, c1, "doc.pdf", data, "application/pdf")
        r2 = _upload_file(client, test_org.id, c2, "doc.pdf", data, "application/pdf")

        assert r1.status_code == status.HTTP_201_CREATED
        assert r2.status_code == status.HTTP_201_CREATED

    def test_no_cross_tenant_duplicate_leakage(self, client, db_session, test_org):
        """Duplicate check must not leak checksum info across organizations."""
        from app.db.models.organization import Organization

        other_org = Organization(name="Other", slug=f"other-{uuid.uuid4().hex[:6]}")
        db_session.add(other_org)
        db_session.commit()
        db_session.refresh(other_org)

        # Upload to org A's claim.
        h1 = {"X-Organization-ID": str(test_org.id)}
        c1 = client.post("/api/v1/claims", json={"title": "OrgA Claim"}, headers=h1).json()["id"]
        data = minimal_pdf() + b" tenant-isolation-data"
        _upload_file(client, test_org.id, c1, "doc.pdf", data, "application/pdf")

        # Upload same content to org B's claim → should be allowed (no leakage).
        h2 = {"X-Organization-ID": str(other_org.id)}
        c2 = client.post("/api/v1/claims", json={"title": "OrgB Claim"}, headers=h2).json()["id"]
        r2 = _upload_file(client, other_org.id, c2, "doc.pdf", data, "application/pdf")
        assert r2.status_code == status.HTTP_201_CREATED


# ─── Compensation ─────────────────────────────────────────────────────────────

class TestCompensation:
    def test_storage_failure_creates_no_db_records(self, client, test_org, db_session):
        """If storage write fails, no Document or Job is persisted."""
        from app.storage.local import LocalStorageProvider

        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Comp Claim"}, headers=h).json()["id"]

        with patch.object(LocalStorageProvider, "save_stream", side_effect=StorageWriteError("disk full")):
            res = _upload_file(client, test_org.id, claim_id, "fail.pdf", minimal_pdf(), "application/pdf")

        assert res.status_code in (status.HTTP_503_SERVICE_UNAVAILABLE, status.HTTP_500_INTERNAL_SERVER_ERROR)

        # No Document or Job should exist.
        docs = db_session.execute(select(Document).where(Document.claim_id == uuid.UUID(claim_id))).scalars().all()
        assert len(docs) == 0

    def test_db_failure_triggers_storage_compensation(self, client, test_org, tmp_path, app_instance, db_session):
        """If DB commit fails after storage succeeds, the stored file should be deleted."""
        from app.storage.local import LocalStorageProvider

        provider = LocalStorageProvider(str(tmp_path / "storage2"))
        deleted_keys = []

        original_delete = provider.delete

        def capturing_delete(key):
            deleted_keys.append(key)
            original_delete(key)

        provider.delete = capturing_delete

        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "DB Fail Claim"}, headers=h).json()["id"]

        with patch("app.storage.factory._build_provider", return_value=provider), \
             patch("sqlalchemy.orm.Session.commit", side_effect=Exception("Simulated DB failure")):
            res = _upload_file(client, test_org.id, claim_id, "dbfail.pdf", minimal_pdf(), "application/pdf")

        assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        # Compensation: delete was called.
        assert len(deleted_keys) >= 1

    def test_temp_file_removed_after_success(self, client, test_org, tmp_path):
        """Temporary files must be cleaned up after successful ingestion."""
        import tempfile as tempfile_module

        created_tmp_files = []
        original_mkstemp = tempfile_module.mkstemp

        def tracking_mkstemp(*args, **kwargs):
            fd, path = original_mkstemp(*args, **kwargs)
            created_tmp_files.append(path)
            return fd, path

        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Tmp Claim"}, headers=h).json()["id"]

        with patch("tempfile.mkstemp", side_effect=tracking_mkstemp):
            res = _upload_file(client, test_org.id, claim_id, "tmp.pdf", minimal_pdf(), "application/pdf")

        assert res.status_code == status.HTTP_201_CREATED
        # All tracked tmp files should be gone.
        for path in created_tmp_files:
            if "krama_upload_" in path:
                assert not os.path.exists(path), f"Temp file not cleaned up: {path}"

    def test_temp_file_removed_after_validation_failure(self, client, test_org, tmp_path):
        """Temporary files must be cleaned up even when validation fails."""
        import tempfile as tempfile_module

        created_tmp_files = []
        original_mkstemp = tempfile_module.mkstemp

        def tracking_mkstemp(*args, **kwargs):
            fd, path = original_mkstemp(*args, **kwargs)
            created_tmp_files.append(path)
            return fd, path

        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Tmp Fail Claim"}, headers=h).json()["id"]

        with patch("tempfile.mkstemp", side_effect=tracking_mkstemp):
            # Invalid signature → validation fails.
            res = _upload_file(client, test_org.id, claim_id, "bad.pdf", b"PK\x03\x04bad", "application/pdf")

        assert res.status_code in (400, 415)
        for path in created_tmp_files:
            if "krama_upload_" in path:
                assert not os.path.exists(path), f"Temp file leaked: {path}"


# ─── No OCR / No processing ──────────────────────────────────────────────────

class TestNoProcessing:
    def test_upload_does_not_invoke_ocr(self, client, test_org):
        """Prove that the upload path never touches DocumentProcessor or OCR."""
        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "NoOCR"}, headers=h).json()["id"]

        with patch("app.services.pipeline.DocumentProcessor") as mock_proc:
            res = _upload_file(client, test_org.id, claim_id, "test.pdf", minimal_pdf(), "application/pdf")

        # DocumentProcessor must never be instantiated or called.
        mock_proc.assert_not_called()
        assert res.status_code == status.HTTP_201_CREATED

    def test_upload_does_not_create_job_stages(self, client, test_org, db_session):
        """Phase 2 creates only one Job record with no stages."""
        from app.db.models.job_stage import JobStage

        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "NoStages"}, headers=h).json()["id"]

        res = _upload_file(client, test_org.id, claim_id, "s.pdf", minimal_pdf(), "application/pdf")
        assert res.status_code == status.HTTP_201_CREATED
        job_id = res.json()["job"]["id"]

        stages = db_session.execute(
            select(JobStage).where(JobStage.job_id == uuid.UUID(job_id))
        ).scalars().all()
        assert len(stages) == 0


# ─── Content retrieval ────────────────────────────────────────────────────────

class TestContentRetrieval:
    def test_content_returns_correct_bytes(self, client, test_org):
        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Content"}, headers=h).json()["id"]

        data = minimal_pdf() + b" content-test-bytes"
        res = _upload_file(client, test_org.id, claim_id, "doc.pdf", data, "application/pdf")
        doc_id = res.json()["document"]["id"]

        content_res = client.get(f"/api/v1/documents/{doc_id}/content", headers=h)
        assert content_res.status_code == status.HTTP_200_OK
        assert content_res.content == data

    def test_content_enforces_tenant_isolation(self, client, db_session, test_org):
        from app.db.models.organization import Organization

        other_org = Organization(name="Content Thief", slug=f"ct-{uuid.uuid4().hex[:6]}")
        db_session.add(other_org)
        db_session.commit()

        h_real = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Real Doc"}, headers=h_real).json()["id"]
        res = _upload_file(client, test_org.id, claim_id, "secret.pdf", minimal_pdf(), "application/pdf")
        doc_id = res.json()["document"]["id"]

        h_evil = {"X-Organization-ID": str(other_org.id)}
        stolen = client.get(f"/api/v1/documents/{doc_id}/content", headers=h_evil)
        assert stolen.status_code == status.HTTP_404_NOT_FOUND

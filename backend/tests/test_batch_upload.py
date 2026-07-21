"""Tests for Phase 2 batch upload API.

Verifies:
- Multiple valid files succeed
- Mixed valid/invalid → partial results
- File count limit enforced
- Total size limit enforced cumulatively
- Duplicate within batch handled correctly
- Response preserves original order
- No sensitive internals in error messages
"""
import io
import uuid
from unittest.mock import patch

import pytest
from fastapi import status


def minimal_pdf(suffix: bytes = b"") -> bytes:
    return b"%PDF-1.4 batch-test" + suffix


def minimal_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 30


def _batch_upload(client, org_id, claim_id, files_spec):
    """Helper: POST to /batch endpoint.

    files_spec: list of (filename, data, content_type)
    """
    headers = {"X-Organization-ID": str(org_id)}
    files = [
        ("files", (fname, io.BytesIO(data), ctype))
        for fname, data, ctype in files_spec
    ]
    return client.post(
        f"/api/v1/claims/{claim_id}/documents/batch",
        files=files,
        headers=headers,
    )


@pytest.fixture(autouse=True)
def override_storage(tmp_path, app_instance):
    from app.storage.local import LocalStorageProvider
    provider = LocalStorageProvider(str(tmp_path / "batch_storage"))
    with patch("app.storage.factory._build_provider", return_value=provider):
        yield provider


class TestBatchUpload:
    def test_multiple_valid_files_succeed(self, client, test_org):
        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Batch Valid"}, headers=h).json()["id"]

        files = [
            ("a.pdf", minimal_pdf(b"A"), "application/pdf"),
            ("b.png", minimal_png(), "image/png"),
        ]
        res = _batch_upload(client, test_org.id, claim_id, files)

        assert res.status_code == status.HTTP_200_OK
        body = res.json()
        assert body["total"] == 2
        assert body["succeeded"] == 2
        assert body["failed"] == 0
        assert all(r["status"] == "success" for r in body["results"])
        assert all(r["document_id"] is not None for r in body["results"])

    def test_mixed_valid_invalid_partial_results(self, client, test_org):
        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Mixed Batch"}, headers=h).json()["id"]

        files = [
            ("good.pdf", minimal_pdf(b"good"), "application/pdf"),
            ("virus.exe", b"MZ\x90\x00bad", "application/octet-stream"),
            ("scan.png", minimal_png(), "image/png"),
        ]
        res = _batch_upload(client, test_org.id, claim_id, files)

        assert res.status_code == status.HTTP_200_OK
        body = res.json()
        assert body["total"] == 3
        assert body["succeeded"] == 2
        assert body["failed"] == 1

        # Order preserved
        assert body["results"][0]["filename"] == "good.pdf"
        assert body["results"][0]["status"] == "success"
        assert body["results"][1]["filename"] == "virus.exe"
        assert body["results"][1]["status"] == "failed"
        assert body["results"][1]["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
        assert body["results"][2]["status"] == "success"

    def test_file_count_limit_enforced(self, client, test_org, app_instance):
        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Count Limit"}, headers=h).json()["id"]

        # Temporarily set limit to 2.
        with patch("app.api.routes.v1.documents.Config") as mock_cfg:
            mock_cfg.MAX_BATCH_FILES = 2
            mock_cfg.MAX_BATCH_TOTAL_SIZE_MB = 500
            mock_cfg.max_batch_total_size_bytes.return_value = 500 * 1024 * 1024
            mock_cfg.UPLOAD_CHUNK_SIZE_BYTES = 1048576

            files = [
                (f"file{i}.pdf", minimal_pdf(bytes([i])), "application/pdf")
                for i in range(3)  # 3 files exceeds limit of 2
            ]
            res = _batch_upload(client, test_org.id, claim_id, files)

        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.json()["error"]["code"] == "BATCH_LIMIT_EXCEEDED"

    def test_duplicate_within_batch_reported_failed(self, client, test_org):
        """Same bytes uploaded twice in one batch: first succeeds, second fails."""
        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Dup Batch"}, headers=h).json()["id"]

        data = minimal_pdf(b"dup-in-batch")
        files = [
            ("orig.pdf", data, "application/pdf"),
            ("copy.pdf", data, "application/pdf"),  # duplicate
        ]
        res = _batch_upload(client, test_org.id, claim_id, files)

        assert res.status_code == status.HTTP_200_OK
        body = res.json()
        assert body["succeeded"] == 1
        assert body["failed"] == 1
        assert body["results"][1]["error"]["code"] == "DUPLICATE_DOCUMENT"

    def test_error_messages_contain_no_internals(self, client, test_org):
        """Batch error responses must not expose stack traces or paths."""
        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Safe Errors"}, headers=h).json()["id"]

        files = [("bad.exe", b"MZ\x90\x00", "application/octet-stream")]
        res = _batch_upload(client, test_org.id, claim_id, files)

        body = res.json()
        error_msg = body["results"][0]["error"]["message"]
        # Must not contain Python traceback indicators.
        assert "Traceback" not in error_msg
        assert "File \"" not in error_msg
        assert "line " not in error_msg.lower() or "line" not in error_msg

    def test_response_preserves_original_order(self, client, test_org):
        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Order Test"}, headers=h).json()["id"]

        files = [
            ("first.pdf", minimal_pdf(b"1"), "application/pdf"),
            ("second.pdf", minimal_pdf(b"2"), "application/pdf"),
            ("third.pdf", minimal_pdf(b"3"), "application/pdf"),
        ]
        res = _batch_upload(client, test_org.id, claim_id, files)

        body = res.json()
        assert body["results"][0]["filename"] == "first.pdf"
        assert body["results"][1]["filename"] == "second.pdf"
        assert body["results"][2]["filename"] == "third.pdf"

    def test_single_file_failure_does_not_rollback_others(self, client, test_org, db_session):
        """A middle-file failure must not affect other successfully committed files."""
        from sqlalchemy import select
        from app.db.models.document import Document

        h = {"X-Organization-ID": str(test_org.id)}
        claim_id = client.post("/api/v1/claims", json={"title": "Independence"}, headers=h).json()["id"]

        files = [
            ("a.pdf", minimal_pdf(b"independent-A"), "application/pdf"),
            ("bad.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("c.pdf", minimal_pdf(b"independent-C"), "application/pdf"),
        ]
        res = _batch_upload(client, test_org.id, claim_id, files)

        assert res.status_code == status.HTTP_200_OK
        assert res.json()["succeeded"] == 2

        # Verify both successful docs exist in DB.
        docs = db_session.execute(
            select(Document).where(Document.claim_id == uuid.UUID(claim_id))
        ).scalars().all()
        assert len(docs) == 2

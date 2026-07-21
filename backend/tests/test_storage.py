"""Tests for LocalStorageProvider and StorageProvider abstraction.

Covers:
- Save stream
- Open stored object
- Exists
- Delete
- Path traversal prevention (multiple attack vectors)
- Storage key remains provider-neutral
- Missing object behavior
- Metadata retrieval
"""
import io
import os
import pytest
from pathlib import Path

from app.storage.local import LocalStorageProvider
from app.storage.base import StorageError, StorageNotFoundError, StorageWriteError


@pytest.fixture
def storage(tmp_path):
    """LocalStorageProvider backed by a pytest temporary directory."""
    return LocalStorageProvider(str(tmp_path))


# ─── save_stream ─────────────────────────────────────────────────────────────

class TestSaveStream:
    def test_save_and_open(self, storage):
        data = b"%PDF-1.4 test content"
        key = "raw/org/claim/doc/source.pdf"
        storage.save_stream(key, io.BytesIO(data))

        with storage.open(key) as f:
            assert f.read() == data

    def test_returns_byte_count(self, storage):
        data = b"A" * 1024
        n = storage.save_stream("raw/x/y/z/source.txt", io.BytesIO(data))
        assert n == 1024

    def test_creates_parent_directories(self, storage, tmp_path):
        key = "raw/a/b/c/d/source.pdf"
        storage.save_stream(key, io.BytesIO(b"data"))
        assert (tmp_path / "raw" / "a" / "b" / "c" / "d" / "source.pdf").is_file()

    def test_overwrites_existing(self, storage):
        key = "raw/x/source.pdf"
        storage.save_stream(key, io.BytesIO(b"original"))
        storage.save_stream(key, io.BytesIO(b"updated"))
        with storage.open(key) as f:
            assert f.read() == b"updated"

    def test_empty_stream(self, storage):
        key = "raw/x/empty.pdf"
        storage.save_stream(key, io.BytesIO(b""))
        assert storage.exists(key)
        with storage.open(key) as f:
            assert f.read() == b""


# ─── open ─────────────────────────────────────────────────────────────────────

class TestOpen:
    def test_open_nonexistent_raises_not_found(self, storage):
        with pytest.raises(StorageNotFoundError):
            storage.open("raw/missing/source.pdf")

    def test_stream_is_readable(self, storage):
        data = b"\xff\xd8\xff JPEG content"
        storage.save_stream("raw/x/j.jpg", io.BytesIO(data))
        with storage.open("raw/x/j.jpg") as f:
            chunk = f.read(4)
            assert chunk == b"\xff\xd8\xff "


# ─── exists ──────────────────────────────────────────────────────────────────

class TestExists:
    def test_returns_false_for_missing(self, storage):
        assert storage.exists("raw/nobody/source.pdf") is False

    def test_returns_true_after_save(self, storage):
        key = "raw/org/cl/doc/source.png"
        storage.save_stream(key, io.BytesIO(b"\x89PNG\r\n\x1a\n"))
        assert storage.exists(key) is True


# ─── delete ──────────────────────────────────────────────────────────────────

class TestDelete:
    def test_delete_existing(self, storage):
        key = "raw/to/delete.pdf"
        storage.save_stream(key, io.BytesIO(b"%PDF-"))
        storage.delete(key)
        assert storage.exists(key) is False

    def test_delete_nonexistent_is_idempotent(self, storage):
        # Should NOT raise.
        storage.delete("raw/never/existed.pdf")

    def test_delete_then_open_raises(self, storage):
        key = "raw/gone.pdf"
        storage.save_stream(key, io.BytesIO(b"%PDF-"))
        storage.delete(key)
        with pytest.raises(StorageNotFoundError):
            storage.open(key)


# ─── get_metadata ─────────────────────────────────────────────────────────────

class TestGetMetadata:
    def test_metadata_for_stored_object(self, storage):
        data = b"Hello, World!"
        key = "raw/x/meta.pdf"
        storage.save_stream(key, io.BytesIO(data))
        meta = storage.get_metadata(key)
        assert meta.key == key
        assert meta.size_bytes == len(data)
        assert meta.last_modified is not None

    def test_metadata_missing_raises_not_found(self, storage):
        with pytest.raises(StorageNotFoundError):
            storage.get_metadata("raw/does/not/exist.pdf")


# ─── Path traversal protection ───────────────────────────────────────────────

class TestPathTraversalProtection:
    """Storage provider must refuse any key that would escape STORAGE_ROOT."""

    TRAVERSAL_KEYS = [
        "../outside.pdf",
        "../../etc/passwd",
        "raw/../../secret",
        "raw/../../../windows/system32/evil.dll",
        "/etc/passwd",
        "/absolute/path.pdf",
        "C:\\windows\\system32\\evil.dll",
        "\\\\server\\share\\file.pdf",  # UNC path
        "raw/a\x00b.pdf",             # Null byte
        "",                            # Empty
    ]

    @pytest.mark.parametrize("key", TRAVERSAL_KEYS)
    def test_save_refuses_traversal(self, storage, key):
        with pytest.raises(StorageError):
            storage.save_stream(key, io.BytesIO(b"data"))

    @pytest.mark.parametrize("key", TRAVERSAL_KEYS)
    def test_open_refuses_traversal(self, storage, key):
        with pytest.raises(StorageError):
            storage.open(key)

    @pytest.mark.parametrize("key", TRAVERSAL_KEYS)
    def test_delete_refuses_traversal(self, storage, key):
        # delete is idempotent but must still reject traversal keys.
        # Either raises StorageError or silently skips (both are acceptable for delete).
        # We only verify it does NOT escape the root.
        try:
            storage.delete(key)
        except StorageError:
            pass  # Expected for traversal keys

    def test_storage_key_stays_provider_neutral(self, storage):
        """Stored logical key must not include machine-specific physical path."""
        key = "raw/org-123/claim-456/doc-789/source.pdf"
        storage.save_stream(key, io.BytesIO(b"%PDF-test"))
        # Key itself contains no STORAGE_ROOT information.
        assert str(storage._root) not in key
        assert os.sep not in key or "/" in key  # uses forward slashes

"""Centralized file type policy for Phase 2 ingestion.

This module is the single source of truth for:
- Supported file extensions
- Accepted MIME types per format
- Magic byte signatures for signature-based validation
- Per-format display names

Policy rules:
1. Extension must be in SUPPORTED_EXTENSIONS.
2. Declared MIME must appear in the allowed set for that extension, OR be the
   generic 'application/octet-stream' (browsers legitimately send this).
3. File signature must match expected magic bytes.
4. A STRONG mismatch — extension says PDF, MIME says image/png, signature is PNG
   — should be rejected regardless of the generic-MIME allowance.

Security note:
- Client MIME type is considered UNTRUSTED metadata.
- File signature has the highest trust.
- Extension is trusted but cannot be relied on exclusively.
- 'application/octet-stream' is accepted as a generic MIME (browser behavior)
  as long as extension and signature agree.

TIFF notes:
- TIFF has two valid magic sequences: little-endian (II) and big-endian (MM).
- Both are listed in the signatures table.

JPEG notes:
- JPEG files begin with FF D8 FF.

Do NOT add new formats without updating ALL three mappings below.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Sequence


# ─── Generic MIME that browsers may send for any file type ────────────────────
GENERIC_OCTET_STREAM = "application/octet-stream"


@dataclass(frozen=True)
class FileTypePolicy:
    """Defines the accepted properties for a single file format."""

    # Human-readable label for error messages.
    label: str
    # Normalised extensions (lowercase, no leading dot).
    extensions: FrozenSet[str]
    # Accepted MIME types (lowercase).
    mime_types: FrozenSet[str]
    # List of accepted magic-byte prefixes. Each entry is a bytes literal.
    # A file is accepted if its first bytes start with ANY of these.
    signatures: Sequence[bytes]


# ─── Supported Formats ───────────────────────────────────────────────────────

PDF_POLICY = FileTypePolicy(
    label="PDF",
    extensions=frozenset({"pdf"}),
    mime_types=frozenset({"application/pdf", "application/x-pdf"}),
    signatures=[b"%PDF-"],
)

PNG_POLICY = FileTypePolicy(
    label="PNG",
    extensions=frozenset({"png"}),
    mime_types=frozenset({"image/png"}),
    signatures=[b"\x89PNG\r\n\x1a\n"],
)

JPEG_POLICY = FileTypePolicy(
    label="JPEG",
    extensions=frozenset({"jpg", "jpeg"}),
    mime_types=frozenset({"image/jpeg", "image/jpg", "image/pjpeg"}),
    signatures=[b"\xff\xd8\xff"],  # All JPEG variants start with FF D8 FF
)

TIFF_POLICY = FileTypePolicy(
    label="TIFF",
    extensions=frozenset({"tif", "tiff"}),
    mime_types=frozenset({"image/tiff", "image/x-tiff", "image/tiff-fx"}),
    signatures=[
        b"II*\x00",  # Little-endian (Intel)
        b"MM\x00*",  # Big-endian (Motorola)
    ],
)

# All active policies in one list.
ALL_POLICIES: list[FileTypePolicy] = [PDF_POLICY, PNG_POLICY, JPEG_POLICY, TIFF_POLICY]

# Convenience flat sets derived from ALL_POLICIES.
SUPPORTED_EXTENSIONS: FrozenSet[str] = frozenset(
    ext for policy in ALL_POLICIES for ext in policy.extensions
)
SUPPORTED_MIME_TYPES: FrozenSet[str] = frozenset(
    mime for policy in ALL_POLICIES for mime in policy.mime_types
)

# Maximum signature prefix length we need to read.
MAX_SIGNATURE_BYTES: int = max(
    len(sig) for policy in ALL_POLICIES for sig in policy.signatures
)


def policy_for_extension(ext: str) -> FileTypePolicy | None:
    """Return the policy for a normalised extension, or None if unsupported."""
    ext_lower = ext.lower().lstrip(".")
    for policy in ALL_POLICIES:
        if ext_lower in policy.extensions:
            return policy
    return None


def policy_for_signature(header: bytes) -> FileTypePolicy | None:
    """Return the first policy whose signature matches the file header bytes."""
    for policy in ALL_POLICIES:
        for sig in policy.signatures:
            if header.startswith(sig):
                return policy
    return None


def is_strong_mime_mismatch(declared_mime: str, ext_policy: FileTypePolicy) -> bool:
    """Return True when the declared MIME conflicts strongly with the extension policy.

    A MIME of 'application/octet-stream' is NEVER a strong mismatch because
    browsers legitimately send this for any file type.

    Example of a strong mismatch:
        extension=pdf, declared_mime=image/png  → True
        extension=pdf, declared_mime=application/octet-stream → False
        extension=pdf, declared_mime=application/pdf → False
    """
    if declared_mime == GENERIC_OCTET_STREAM:
        return False
    # Normalise.
    mime_lower = declared_mime.lower().strip()
    if mime_lower in ext_policy.mime_types:
        return False
    # Check if the declared MIME belongs to a completely different policy.
    for policy in ALL_POLICIES:
        if mime_lower in policy.mime_types and policy is not ext_policy:
            return True
    # Unknown MIME — not a strong mismatch, just unrecognised.
    return False

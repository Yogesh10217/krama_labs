"""Phase 2 checksum index on documents

Adds a composite index on (claim_id, checksum) to the documents table to support
efficient duplicate detection during ingestion. This index allows the duplicate
lookup query (find_active_by_checksum_in_claim) to run in O(log n) instead of a
full table scan.

Note: We intentionally do NOT add a unique constraint because:
- Archived documents with the same checksum should be permitted.
- The duplicate policy is enforced at the application level.

Revision ID: b07106af6973
Revises: 794e26ca76d7
Create Date: 2026-07-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b07106af6973'
down_revision: Union[str, Sequence[str], None] = '794e26ca76d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite index for efficient duplicate document detection."""
    op.create_index(
        'ix_documents_claim_id_checksum',
        'documents',
        ['claim_id', 'checksum'],
        unique=False,
    )


def downgrade() -> None:
    """Remove the composite duplicate-detection index."""
    op.drop_index('ix_documents_claim_id_checksum', table_name='documents')

"""Phase 3 page model update

Revision ID: d0e7b298584e
Revises: b07106af6973
Create Date: 2026-07-22 19:50:52.205177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e7b298584e'
down_revision: Union[str, Sequence[str], None] = 'b07106af6973'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Postgres supports enum extension with ALTER TYPE
        # We use COMMIT to run this outside transactions because PostgreSQL requires it.
        op.execute("COMMIT")
        op.execute("ALTER TYPE documentstatus ADD VALUE 'CONVERTING'")
        op.execute("ALTER TYPE documentstatus ADD VALUE 'CONVERTED'")
        op.execute("ALTER TYPE documentstatus ADD VALUE 'CONVERSION_FAILED'")
    
    op.add_column('pages', sa.Column('storage_key', sa.String(length=1024), nullable=True))
    op.add_column('pages', sa.Column('content_type', sa.String(length=100), nullable=True))
    op.add_column('pages', sa.Column('checksum', sa.String(length=64), nullable=True))
    op.add_column('pages', sa.Column('size_bytes', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('pages', 'size_bytes')
    op.drop_column('pages', 'checksum')
    op.drop_column('pages', 'content_type')
    op.drop_column('pages', 'storage_key')
    # PostgreSQL enum values cannot be easily dropped without dropping the type,
    # so we don't drop them in downgrade (Postgres doesn't support ALTER TYPE DROP VALUE anyway).

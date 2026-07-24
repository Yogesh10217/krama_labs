"""add_phase10_job_execution

Revision ID: 16ccd25ae4b8
Revises: ec53a9403aac
Create Date: 2026-07-24 22:16:55.823438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16ccd25ae4b8'
down_revision: Union[str, Sequence[str], None] = 'ec53a9403aac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 10 async job execution tables."""
    op.create_table(
        'job_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=True),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.String(), nullable=True),
        sa.Column('queue_name', sa.String(), nullable=False),
        sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('current_stage', sa.String(), nullable=True),
        sa.Column('last_successful_stage', sa.String(), nullable=True),
        sa.Column('last_success_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checkpoint_version', sa.Integer(), nullable=False),
        sa.Column('checkpoint_meta', sa.JSON(), nullable=True),
        sa.Column('correlation_id', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_executions_correlation_id', 'job_executions', ['correlation_id'], unique=False)
    op.create_index('ix_job_executions_document_id', 'job_executions', ['document_id'], unique=False)
    op.create_index('ix_job_executions_organization_id', 'job_executions', ['organization_id'], unique=False)
    op.create_index('ix_job_executions_status', 'job_executions', ['status'], unique=False)

    op.create_table(
        'job_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_execution_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('stage_name', sa.String(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('correlation_id', sa.String(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['job_execution_id'], ['job_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_events_job_execution_id', 'job_events', ['job_execution_id'], unique=False)

    op.create_table(
        'job_retries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_execution_id', sa.String(), nullable=False),
        sa.Column('attempt', sa.Integer(), nullable=False),
        sa.Column('stage_name', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('backoff_seconds', sa.Float(), nullable=True),
        sa.Column('correlation_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['job_execution_id'], ['job_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_retries_job_execution_id', 'job_retries', ['job_execution_id'], unique=False)


def downgrade() -> None:
    """Remove Phase 10 async job execution tables."""
    op.drop_index('ix_job_retries_job_execution_id', table_name='job_retries')
    op.drop_table('job_retries')
    op.drop_index('ix_job_events_job_execution_id', table_name='job_events')
    op.drop_table('job_events')
    op.drop_index('ix_job_executions_status', table_name='job_executions')
    op.drop_index('ix_job_executions_organization_id', table_name='job_executions')
    op.drop_index('ix_job_executions_document_id', table_name='job_executions')
    op.drop_index('ix_job_executions_correlation_id', table_name='job_executions')
    op.drop_table('job_executions')

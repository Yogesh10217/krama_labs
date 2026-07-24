"""
tests/test_jobs.py — Phase 10 Unit & Integration Tests

Tests cover:
  1. PipelineStateMachine — transitions, resume, terminal detection
  2. CancellationToken — cancel/raise semantics
  3. InMemoryJobQueue — enqueue/dequeue/ack/nack/peek/size/health
  4. JobDispatcher — creates job, enqueues message, idempotency
  5. JobExecutor — full success path, failure path, cancellation path
  6. RetryPolicy — back-off calculation
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.db.models  # noqa: F401 — ensure all models are registered

from app.domain.enums import ExecutionStatus, JobEventType
from app.jobs.cancellation import CancellationToken, CancelledError
from app.jobs.context import JobContext
from app.jobs.executor import JobExecutor
from app.jobs.queue import InMemoryJobQueue, QueueMessage
from app.jobs.stage import PipelineStage, StageResult, RetryPolicy
from app.jobs.state_machine import PipelineStateMachine, StageTransitionError
from app.jobs.dispatcher import JobDispatcher


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="function")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture(scope="function")
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def org_id():
    return str(uuid.uuid4())


@pytest.fixture
def doc_id():
    return str(uuid.uuid4())


@pytest.fixture
def job_ctx(org_id, doc_id):
    return JobContext(
        job_execution_id=str(uuid.uuid4()),
        document_id=doc_id,
        organization_id=org_id,
        correlation_id=str(uuid.uuid4()),
    )


@pytest.fixture
def queue():
    return InMemoryJobQueue(name="test")


# ===========================================================================
# Helpers — Fake Stages
# ===========================================================================

class _SuccessStage(PipelineStage):
    def __init__(self, name: str, wt: int = 10) -> None:
        self._name = name
        self._wt = wt
        self.called = False

    def stage_name(self) -> str:
        return self._name

    def weight(self) -> int:
        return self._wt

    def execute(self, ctx, cancellation_token, checkpoint=None) -> StageResult:
        self.called = True
        return StageResult(stage_name=self._name, success=True, progress_contribution=self._wt)


class _FailingStage(PipelineStage):
    def __init__(self, name: str = "fail", max_att: int = 1) -> None:
        self._name = name
        self._max_att = max_att

    def stage_name(self) -> str:
        return self._name

    def weight(self) -> int:
        return 10

    def retry_policy(self) -> RetryPolicy:
        return RetryPolicy(max_attempts=self._max_att, backoff_seconds=0.0)

    def execute(self, ctx, cancellation_token, checkpoint=None) -> StageResult:
        return StageResult(stage_name=self._name, success=False, progress_contribution=0, error_message="intentional failure")


class _CancellingStage(PipelineStage):
    def __init__(self, token: CancellationToken) -> None:
        self._token = token

    def stage_name(self) -> str:
        return "cancel_stage"

    def weight(self) -> int:
        return 10

    def execute(self, ctx, cancellation_token, checkpoint=None) -> StageResult:
        self._token.cancel()
        cancellation_token.raise_if_cancelled()
        return StageResult(stage_name=self.stage_name(), success=True, progress_contribution=10)


# ===========================================================================
# 1. CancellationToken
# ===========================================================================

class TestCancellationToken:
    def test_initial_state_not_cancelled(self):
        token = CancellationToken()
        assert not token.is_cancelled

    def test_cancel_sets_state(self):
        token = CancellationToken()
        token.cancel()
        assert token.is_cancelled

    def test_cancel_is_idempotent(self):
        token = CancellationToken()
        token.cancel()
        token.cancel()  # should not raise
        assert token.is_cancelled

    def test_raise_if_cancelled(self):
        token = CancellationToken()
        token.cancel()
        with pytest.raises(CancelledError):
            token.raise_if_cancelled()

    def test_no_raise_when_not_cancelled(self):
        token = CancellationToken()
        token.raise_if_cancelled()  # should not raise


# ===========================================================================
# 2. InMemoryJobQueue
# ===========================================================================

class TestInMemoryJobQueue:
    def _msg(self, job_id: str = None) -> QueueMessage:
        job_id = job_id or str(uuid.uuid4())
        ctx = MagicMock(spec=JobContext)
        return QueueMessage(message_id=str(uuid.uuid4()), job_execution_id=job_id, context=ctx)

    def test_enqueue_and_dequeue(self):
        q = InMemoryJobQueue()
        msg = self._msg()
        q.enqueue(msg)
        received = q.dequeue(timeout_seconds=1.0)
        assert received is not None
        assert received.job_execution_id == msg.job_execution_id

    def test_dequeue_empty_returns_none(self):
        q = InMemoryJobQueue()
        assert q.dequeue(timeout_seconds=0.1) is None

    def test_size(self):
        q = InMemoryJobQueue()
        assert q.size() == 0
        q.enqueue(self._msg())
        assert q.size() == 1

    def test_peek_nonempty(self):
        q = InMemoryJobQueue()
        msg = self._msg()
        q.enqueue(msg)
        peeked = q.peek()
        assert peeked is not None
        assert peeked.job_execution_id == msg.job_execution_id
        assert q.size() == 1  # peek doesn't consume

    def test_peek_empty(self):
        q = InMemoryJobQueue()
        assert q.peek() is None

    def test_ack_removes_inflight(self):
        q = InMemoryJobQueue()
        q.enqueue(self._msg())
        msg = q.dequeue(timeout_seconds=1.0)
        q.ack(msg.message_id)
        assert msg.message_id not in q._in_flight

    def test_nack_requeues(self):
        q = InMemoryJobQueue()
        original = self._msg()
        q.enqueue(original)
        received = q.dequeue(timeout_seconds=1.0)
        q.nack(received.message_id, requeue=True)
        requeued = q.dequeue(timeout_seconds=1.0)
        assert requeued is not None
        assert requeued.job_execution_id == original.job_execution_id

    def test_health(self):
        q = InMemoryJobQueue()
        h = q.health()
        assert h.is_healthy
        assert h.provider == "inmemory"

    def test_delivery_count_increments(self):
        q = InMemoryJobQueue()
        q.enqueue(self._msg())
        msg = q.dequeue(timeout_seconds=1.0)
        assert msg.delivery_count == 1


# ===========================================================================
# 3. PipelineStateMachine
# ===========================================================================

class TestPipelineStateMachine:
    def test_next_returns_first_stage(self):
        s1 = _SuccessStage("s1")
        s2 = _SuccessStage("s2")
        machine = PipelineStateMachine([s1, s2])
        result = machine.next()
        assert not result.is_terminal
        assert result.next_stage is s1

    def test_advance_success_moves_to_next(self):
        s1 = _SuccessStage("s1")
        s2 = _SuccessStage("s2")
        machine = PipelineStateMachine([s1, s2])
        machine.next()
        machine.advance(success=True)
        result = machine.next()
        assert result.next_stage is s2

    def test_advance_to_terminal(self):
        s1 = _SuccessStage("s1")
        machine = PipelineStateMachine([s1])
        machine.next()
        machine.advance(success=True)
        assert machine.is_terminal

    def test_resume_skips_completed_stage(self):
        s1 = _SuccessStage("s1")
        s2 = _SuccessStage("s2")
        machine = PipelineStateMachine([s1, s2], last_successful_stage="s1")
        result = machine.next()
        assert result.next_stage is s2

    def test_resume_past_all_stages_is_terminal(self):
        s1 = _SuccessStage("s1")
        machine = PipelineStateMachine([s1], last_successful_stage="s1")
        assert machine.is_terminal

    def test_mark_terminal_stops_pipeline(self):
        s1 = _SuccessStage("s1")
        machine = PipelineStateMachine([s1])
        machine.mark_terminal()
        assert machine.is_terminal

    def test_empty_stages_raises(self):
        with pytest.raises(StageTransitionError):
            PipelineStateMachine([])

    def test_checkpoint_roundtrip(self):
        s1 = _SuccessStage("s1")
        machine = PipelineStateMachine([s1])
        machine.save_checkpoint("s1", {"foo": "bar"})
        assert machine.get_checkpoint("s1") == {"foo": "bar"}

    def test_all_stage_names(self):
        stages = [_SuccessStage("a"), _SuccessStage("b")]
        machine = PipelineStateMachine(stages)
        assert machine.all_stage_names() == ["a", "b"]


# ===========================================================================
# 4. RetryPolicy
# ===========================================================================

class TestRetryPolicy:
    def test_backoff_increases_exponentially(self):
        policy = RetryPolicy(max_attempts=4, backoff_seconds=2.0, backoff_multiplier=2.0, max_backoff_seconds=100.0)
        assert policy.backoff_for(1) == 2.0
        assert policy.backoff_for(2) == 4.0
        assert policy.backoff_for(3) == 8.0
        assert policy.backoff_for(4) == 16.0

    def test_backoff_clamped_by_max(self):
        policy = RetryPolicy(backoff_seconds=5.0, backoff_multiplier=10.0, max_backoff_seconds=15.0)
        assert policy.backoff_for(3) == 15.0


# ===========================================================================
# 5. JobDispatcher
# ===========================================================================

class TestJobDispatcher:
    def test_dispatch_creates_job(self, db, queue, org_id, doc_id):
        dispatcher = JobDispatcher(db=db, queue=queue)
        job = dispatcher.dispatch(organization_id=org_id, document_id=doc_id)
        assert job.id is not None
        assert job.status == ExecutionStatus.QUEUED.value
        assert job.organization_id == org_id
        assert job.document_id == doc_id

    def test_dispatch_enqueues_message(self, db, queue, org_id, doc_id):
        dispatcher = JobDispatcher(db=db, queue=queue)
        dispatcher.dispatch(organization_id=org_id, document_id=doc_id)
        assert queue.size() == 1

    def test_dispatch_idempotency(self, db, queue, org_id, doc_id):
        dispatcher = JobDispatcher(db=db, queue=queue)
        job1 = dispatcher.dispatch(organization_id=org_id, document_id=doc_id)
        job2 = dispatcher.dispatch(organization_id=org_id, document_id=doc_id)
        # Second dispatch returns same job
        assert job1.id == job2.id
        # Only one message in queue
        assert queue.size() == 1

    def test_dispatch_creates_job_created_event(self, db, queue, org_id, doc_id):
        from app.db.models.job_execution import JobEvent
        dispatcher = JobDispatcher(db=db, queue=queue)
        job = dispatcher.dispatch(organization_id=org_id, document_id=doc_id)
        events = db.query(JobEvent).filter(JobEvent.job_execution_id == job.id).all()
        assert len(events) >= 1
        assert events[0].event_type == JobEventType.JOB_CREATED.value


# ===========================================================================
# 6. JobExecutor — Full Success Path
# ===========================================================================

class TestJobExecutor:
    def _make_job(self, db, org_id, doc_id):
        from app.db.models.job_execution import JobExecution
        from datetime import datetime, timezone
        job = JobExecution(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            document_id=doc_id,
            job_type="DOCUMENT_PROCESSING",
            status=ExecutionStatus.QUEUED.value,
            priority=0,
            queue_name="test",
            retry_count=0,
            max_retries=3,
            progress=0,
            checkpoint_version=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
        return job

    def test_all_stages_succeed(self, db, job_ctx, org_id, doc_id):
        stages = [_SuccessStage("s1", 50), _SuccessStage("s2", 50)]
        job = self._make_job(db, org_id, doc_id)
        job_ctx = JobContext(
            job_execution_id=job.id,
            document_id=doc_id,
            organization_id=org_id,
        )
        executor = JobExecutor(db=db, stages=stages)
        token = CancellationToken()
        executor.run(job=job, ctx=job_ctx, cancellation_token=token)
        assert job.status == ExecutionStatus.COMPLETED.value
        assert job.progress == 100

    def test_stage_failure_marks_job_failed(self, db, job_ctx, org_id, doc_id):
        stages = [_SuccessStage("s1", 50), _FailingStage("s2", max_att=1)]
        job = self._make_job(db, org_id, doc_id)
        job_ctx = JobContext(job_execution_id=job.id, document_id=doc_id, organization_id=org_id)
        executor = JobExecutor(db=db, stages=stages)
        token = CancellationToken()
        executor.run(job=job, ctx=job_ctx, cancellation_token=token)
        assert job.status == ExecutionStatus.FAILED.value

    def test_cancellation_stops_execution(self, db, org_id, doc_id):
        token = CancellationToken()
        stages = [_SuccessStage("s1"), _CancellingStage(token)]
        job = self._make_job(db, org_id, doc_id)
        job_ctx = JobContext(job_execution_id=job.id, document_id=doc_id, organization_id=org_id)
        executor = JobExecutor(db=db, stages=stages)
        executor.run(job=job, ctx=job_ctx, cancellation_token=token)
        assert job.status == ExecutionStatus.CANCELLED.value

    def test_events_are_recorded(self, db, org_id, doc_id):
        from app.db.models.job_execution import JobEvent
        stages = [_SuccessStage("s1", 100)]
        job = self._make_job(db, org_id, doc_id)
        job_ctx = JobContext(job_execution_id=job.id, document_id=doc_id, organization_id=org_id)
        executor = JobExecutor(db=db, stages=stages)
        token = CancellationToken()
        executor.run(job=job, ctx=job_ctx, cancellation_token=token)
        events = db.query(JobEvent).filter(JobEvent.job_execution_id == job.id).all()
        event_types = {e.event_type for e in events}
        assert JobEventType.JOB_STARTED.value in event_types
        assert JobEventType.JOB_COMPLETED.value in event_types
        assert JobEventType.STAGE_STARTED.value in event_types
        assert JobEventType.STAGE_COMPLETED.value in event_types

    def test_retry_records_are_created(self, db, org_id, doc_id):
        from app.db.models.job_execution import JobRetry
        stages = [_FailingStage("s1", max_att=3)]
        job = self._make_job(db, org_id, doc_id)
        job_ctx = JobContext(job_execution_id=job.id, document_id=doc_id, organization_id=org_id)
        executor = JobExecutor(db=db, stages=stages)
        token = CancellationToken()
        executor.run(job=job, ctx=job_ctx, cancellation_token=token)
        retries = db.query(JobRetry).filter(JobRetry.job_execution_id == job.id).all()
        assert len(retries) == 3  # 3 attempts = 3 retry records

    def test_progress_is_weighted(self, db, org_id, doc_id):
        stages = [_SuccessStage("s1", 60), _SuccessStage("s2", 40)]
        job = self._make_job(db, org_id, doc_id)
        job_ctx = JobContext(job_execution_id=job.id, document_id=doc_id, organization_id=org_id)
        executor = JobExecutor(db=db, stages=stages)
        token = CancellationToken()
        executor.run(job=job, ctx=job_ctx, cancellation_token=token)
        assert job.progress == 100

    def test_last_successful_stage_checkpoint(self, db, org_id, doc_id):
        stages = [_SuccessStage("s1", 50), _FailingStage("s2", max_att=1)]
        job = self._make_job(db, org_id, doc_id)
        job_ctx = JobContext(job_execution_id=job.id, document_id=doc_id, organization_id=org_id)
        executor = JobExecutor(db=db, stages=stages)
        token = CancellationToken()
        executor.run(job=job, ctx=job_ctx, cancellation_token=token)
        # s1 should be recorded as last successful
        assert job.last_successful_stage == "s1"

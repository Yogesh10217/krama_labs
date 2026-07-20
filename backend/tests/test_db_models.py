import pytest
from sqlalchemy.exc import IntegrityError
from app.db.models.job import Job
from app.db.models.job_stage import JobStage
from app.db.models.claim import Claim
from app.domain.enums import JobType, JobStageStatus

def test_job_progress_constraints(db_session, test_org):
    """Test that progress must be between 0 and 100."""
    job = Job(
        organization_id=test_org.id,
        job_type=JobType.DOCUMENT_PROCESSING,
        progress=-1
    )
    db_session.add(job)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    job2 = Job(
        organization_id=test_org.id,
        job_type=JobType.DOCUMENT_PROCESSING,
        progress=101
    )
    db_session.add(job2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    job3 = Job(
        organization_id=test_org.id,
        job_type=JobType.DOCUMENT_PROCESSING,
        progress=50
    )
    db_session.add(job3)
    db_session.commit()
    assert job3.id is not None

def test_multiple_null_external_references(db_session, test_org):
    """Test that multiple claims can have NULL external references."""
    claim1 = Claim(organization_id=test_org.id, title="Claim 1")
    claim2 = Claim(organization_id=test_org.id, title="Claim 2")
    
    db_session.add(claim1)
    db_session.add(claim2)
    db_session.commit()
    
    assert claim1.id is not None
    assert claim2.id is not None

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.domain.enums import (
    DocumentStatus,
    ReviewStatus,
    ReviewDecisionType,
    ValidationStatus
)
from app.db.models.document import Document
from app.db.models.classification import DocumentClassification
from app.db.models.extraction import ExtractionRun, ExtractedField
from app.db.models.validation import ValidationRun, ValidatedField
from app.db.models.review import ReviewSession, ReviewDecision, ReviewComment, ReviewHistory
from app.services.review_service import ReviewService
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.services.final_document_resolver import FinalDocumentResolver
from app.workflow.policies import AutoApprovalPolicy, CriticalFieldPolicy
from app.core.exceptions import (
    ReviewSessionNotFoundException,
    ConcurrentReviewConflictException,
    ReviewStateInvalidException
)

@pytest.fixture
def pipeline_document(db_session, test_org):
    doc = Document(
        organization_id=test_org.id,
        claim_id=uuid.uuid4(),
        status=DocumentStatus.VALIDATED,
        page_count=1,
        original_filename="invoice.pdf",
        document_type="invoice"
    )
    db_session.add(doc)
    db_session.commit()

    classification = DocumentClassification(
        document_id=doc.id,
        organization_id=test_org.id,
        classifier_name="rules",
        classifier_version="1.0",
        document_type="invoice",
        confidence=0.95,
        artifact_storage_key="class_key"
    )
    db_session.add(classification)
    db_session.commit()

    ext_run = ExtractionRun(
        organization_id=test_org.id,
        document_id=doc.id,
        classification_id=classification.id,
        extractor_name="rules",
        extractor_version="1.0",
        schema_name="invoice_schema",
        schema_version="1.0",
        status="COMPLETED",
        artifact_storage_key="ext_key",
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(ext_run)
    db_session.commit()

    ef1 = ExtractedField(
        extraction_run_id=ext_run.id,
        field_name="total",
        raw_value="100.00",
        normalized_value="100.00",
        data_type="CURRENCY",
        confidence=0.90
    )
    ef2 = ExtractedField(
        extraction_run_id=ext_run.id,
        field_name="vendor",
        raw_value="ACME Corp",
        normalized_value="ACME Corp",
        data_type="STRING",
        confidence=0.90
    )
    db_session.add_all([ef1, ef2])
    db_session.commit()

    val_run = ValidationRun(
        organization_id=test_org.id,
        document_id=doc.id,
        extraction_run_id=ext_run.id,
        validator_name="rules",
        validator_version="1.0",
        status="COMPLETED",
        artifact_storage_key="val_key",
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(val_run)
    db_session.commit()

    vf1 = ValidatedField(
        validation_run_id=val_run.id,
        extracted_field_id=ef1.id,
        validation_status=ValidationStatus.SUPPORTED,
        validation_score=0.98,
        validation_reason="Exact match"
    )
    vf2 = ValidatedField(
        validation_run_id=val_run.id,
        extracted_field_id=ef2.id,
        validation_status=ValidationStatus.SUPPORTED,
        validation_score=0.96,
        validation_reason="Fuzzy match"
    )
    db_session.add_all([vf1, vf2])
    db_session.commit()

    return doc


def test_auto_approval_flow(db_session, test_org, pipeline_document):
    orchestrator = WorkflowOrchestrator(db_session)
    session = orchestrator.process_validation_result(test_org.id, pipeline_document.id)

    assert session is not None
    assert session.status == ReviewStatus.AUTO_APPROVED
    assert session.completed_at is not None
    
    db_session.refresh(pipeline_document)
    assert pipeline_document.status == DocumentStatus.AUTO_APPROVED

    # Check history
    assert len(session.history) == 1
    assert session.history[0].event == "auto_approved"
    assert session.history[0].actor == "SYSTEM"


def test_manual_review_routing_low_score(db_session, test_org, pipeline_document):
    # Lower validation score of a field
    val_run = pipeline_document.validation_runs[0]
    val_run.fields[0].validation_score = 0.50
    db_session.commit()

    orchestrator = WorkflowOrchestrator(db_session)
    session = orchestrator.process_validation_result(test_org.id, pipeline_document.id)

    assert session is not None
    assert session.status == ReviewStatus.PENDING_REVIEW
    assert session.completed_at is None
    
    db_session.refresh(pipeline_document)
    assert pipeline_document.status == DocumentStatus.REVIEW_PENDING


def test_reviewer_assignment_and_state_transition(db_session, test_org, pipeline_document):
    # Route to human review
    val_run = pipeline_document.validation_runs[0]
    val_run.fields[0].validation_score = 0.50
    db_session.commit()

    orchestrator = WorkflowOrchestrator(db_session)
    session = orchestrator.process_validation_result(test_org.id, pipeline_document.id)

    review_service = ReviewService(db_session)
    reviewer_id = uuid.uuid4()

    # Assign reviewer
    updated_session = review_service.assign_reviewer(
        organization_id=test_org.id,
        document_id=pipeline_document.id,
        reviewer_id=reviewer_id,
        expected_version=1
    )

    assert updated_session.assigned_user_id == reviewer_id
    assert updated_session.status == ReviewStatus.IN_REVIEW
    assert updated_session.version == 2

    db_session.refresh(pipeline_document)
    assert pipeline_document.status == DocumentStatus.UNDER_REVIEW


def test_optimistic_locking_conflict(db_session, test_org, pipeline_document):
    review_service = ReviewService(db_session)
    session = review_service.create_session(test_org.id, pipeline_document.id, auto_approve=False)

    reviewer_id = uuid.uuid4()
    
    # Passing wrong expected_version should raise exception
    with pytest.raises(ConcurrentReviewConflictException):
        review_service.assign_reviewer(
            organization_id=test_org.id,
            document_id=pipeline_document.id,
            reviewer_id=reviewer_id,
            expected_version=99
        )


def test_field_decision_and_correction(db_session, test_org, pipeline_document):
    review_service = ReviewService(db_session)
    session = review_service.create_session(test_org.id, pipeline_document.id, auto_approve=False)

    vf = pipeline_document.validation_runs[0].fields[0]
    reviewer_id = uuid.uuid4()

    # Record field correction
    decision = review_service.record_decision(
        organization_id=test_org.id,
        document_id=pipeline_document.id,
        validated_field_id=vf.id,
        decision_type=ReviewDecisionType.CORRECT,
        reviewer_id=reviewer_id,
        corrected_value="150.00",
        reason="OCR misread digit",
        expected_version=1
    )

    assert decision.decision == ReviewDecisionType.CORRECT
    assert decision.corrected_value == "150.00"
    assert decision.reviewer_id == reviewer_id
    
    db_session.refresh(session)
    assert session.version == 2


def test_field_level_comments(db_session, test_org, pipeline_document):
    review_service = ReviewService(db_session)
    session = review_service.create_session(test_org.id, pipeline_document.id, auto_approve=False)

    vf = pipeline_document.validation_runs[0].fields[0]
    reviewer_id = uuid.uuid4()

    comment = review_service.add_comment(
        organization_id=test_org.id,
        document_id=pipeline_document.id,
        comment_text="Verified with physical receipt",
        reviewer_id=reviewer_id,
        validated_field_id=vf.id
    )

    assert comment.comment == "Verified with physical receipt"
    assert comment.validated_field_id == vf.id


def test_review_completion_and_finalization(db_session, test_org, pipeline_document):
    review_service = ReviewService(db_session)
    session = review_service.create_session(test_org.id, pipeline_document.id, auto_approve=False)
    reviewer_id = uuid.uuid4()

    # Make decisions for all critical fields
    for vf in pipeline_document.validation_runs[0].fields:
        review_service.record_decision(
            organization_id=test_org.id,
            document_id=pipeline_document.id,
            validated_field_id=vf.id,
            decision_type=ReviewDecisionType.APPROVE,
            reviewer_id=reviewer_id
        )

    db_session.refresh(session)
    completed_session = review_service.complete_review(
        organization_id=test_org.id,
        document_id=pipeline_document.id,
        reviewer_id=reviewer_id
    )

    assert completed_session.status == ReviewStatus.APPROVED
    assert completed_session.completed_at is not None

    db_session.refresh(pipeline_document)
    assert pipeline_document.status == DocumentStatus.FINALIZED


def test_final_document_view_resolution(db_session, test_org, pipeline_document):
    review_service = ReviewService(db_session)
    session = review_service.create_session(test_org.id, pipeline_document.id, auto_approve=False)
    reviewer_id = uuid.uuid4()

    vf1 = pipeline_document.validation_runs[0].fields[0] # total (extracted 100.00)
    
    # Correct field value in review
    review_service.record_decision(
        organization_id=test_org.id,
        document_id=pipeline_document.id,
        validated_field_id=vf1.id,
        decision_type=ReviewDecisionType.CORRECT,
        reviewer_id=reviewer_id,
        corrected_value="250.00"
    )

    # Compute FinalDocumentView
    resolver = FinalDocumentResolver(db_session)
    final_view = resolver.resolve(test_org.id, pipeline_document.id)

    assert final_view.document_id == pipeline_document.id
    total_field = next(f for f in final_view.fields if f.field_name == "total")
    
    assert total_field.final_value == "250.00"
    assert total_field.source == "REVIEWER_CORRECTION"
    assert total_field.raw_value == "100.00"

    # CANONICAL ARTIFACT IMMUTABILITY CHECK
    db_session.refresh(vf1)
    assert vf1.extracted_field.raw_value == "100.00"
    assert vf1.extracted_field.normalized_value == "100.00"


def test_tenant_isolation(db_session, test_org, pipeline_document):
    review_service = ReviewService(db_session)
    review_service.create_session(test_org.id, pipeline_document.id, auto_approve=False)

    other_org_id = uuid.uuid4()
    with pytest.raises(ReviewSessionNotFoundException):
        review_service.get_review_session(other_org_id, pipeline_document.id)

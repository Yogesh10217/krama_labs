import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_organization_context
from app.db.models.organization import Organization
from app.db.session import get_db
from app.services.review_service import ReviewService
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.services.final_document_resolver import FinalDocumentResolver
from app.schemas.review import (
    ReviewSessionResponse,
    ReviewAssignRequest,
    ReviewDecisionCreate,
    ReviewDecisionResponse,
    ReviewCommentCreate,
    ReviewCommentResponse,
    ReviewCompleteRequest,
    FinalDocumentView
)

router = APIRouter()

@router.post("/{document_id}/review/start", response_model=ReviewSessionResponse)
def start_review(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    orchestrator = WorkflowOrchestrator(db)
    session = orchestrator.process_validation_result(org.id, document_id)
    return session


@router.post("/{document_id}/review/assign", response_model=ReviewSessionResponse)
def assign_reviewer(
    document_id: uuid.UUID,
    body: ReviewAssignRequest,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = ReviewService(db)
    session = service.assign_reviewer(
        organization_id=org.id,
        document_id=document_id,
        reviewer_id=body.reviewer_id,
        expected_version=body.expected_version
    )
    return session


@router.post("/{document_id}/review/decision", response_model=ReviewDecisionResponse)
def record_decision(
    document_id: uuid.UUID,
    body: ReviewDecisionCreate,
    x_reviewer_id: Annotated[str | None, Header()] = None,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    reviewer_id = uuid.UUID(x_reviewer_id) if x_reviewer_id else org.id
    service = ReviewService(db)
    decision = service.record_decision(
        organization_id=org.id,
        document_id=document_id,
        validated_field_id=body.validated_field_id,
        decision_type=body.decision,
        reviewer_id=reviewer_id,
        corrected_value=body.corrected_value,
        reason=body.reason,
        expected_version=body.expected_version
    )
    return decision


@router.post("/{document_id}/review/comment", response_model=ReviewCommentResponse)
def add_comment(
    document_id: uuid.UUID,
    body: ReviewCommentCreate,
    x_reviewer_id: Annotated[str | None, Header()] = None,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    reviewer_id = uuid.UUID(x_reviewer_id) if x_reviewer_id else org.id
    service = ReviewService(db)
    comment = service.add_comment(
        organization_id=org.id,
        document_id=document_id,
        comment_text=body.comment,
        reviewer_id=reviewer_id,
        validated_field_id=body.validated_field_id
    )
    return comment


@router.post("/{document_id}/review/complete", response_model=ReviewSessionResponse)
def complete_review(
    document_id: uuid.UUID,
    body: ReviewCompleteRequest,
    x_reviewer_id: Annotated[str | None, Header()] = None,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    reviewer_id = uuid.UUID(x_reviewer_id) if x_reviewer_id else org.id
    service = ReviewService(db)
    session = service.complete_review(
        organization_id=org.id,
        document_id=document_id,
        reviewer_id=reviewer_id,
        target_status=body.target_status,
        expected_version=body.expected_version
    )
    return session


@router.get("/{document_id}/review", response_model=ReviewSessionResponse)
def get_review(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    service = ReviewService(db)
    return service.get_review_session(org.id, document_id)


@router.get("/{document_id}/final", response_model=FinalDocumentView)
def get_final_document(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    resolver = FinalDocumentResolver(db)
    return resolver.resolve(org.id, document_id)

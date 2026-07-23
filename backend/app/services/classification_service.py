import json
import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.config import Config
from app.db.models.document import Document
from app.db.models.job import Job
from app.db.models.job_stage import JobStage
from app.db.models.classification import DocumentClassification
from app.db.models.ocr import OCRPageResult, OCRRegion
from app.domain.enums import DocumentStatus, JobStatus, JobStageStatus
from app.core.exceptions import KramaException
from app.storage.base import StorageProvider
from app.classification import (
    ClassificationInput, 
    ClassificationResult, 
    get_classifier, 
    ClassificationNormalizer,
    ProviderUnavailableException
)

logger = logging.getLogger(__name__)

class DocumentNotReadyForClassificationException(KramaException):
    def __init__(self, doc_id: uuid.UUID, status: str):
        super().__init__(
            status_code=400,
            code="DOCUMENT_NOT_READY_FOR_CLASSIFICATION",
            message=f"Document {doc_id} is in status {status} and is not ready for classification."
        )

class ClassificationFailedException(KramaException):
    def __init__(self, doc_id: uuid.UUID, message: str):
        super().__init__(
            status_code=500,
            code="CLASSIFICATION_FAILED",
            message=f"Classification failed for document {doc_id}: {message}"
        )


class ClassificationService:
    def __init__(self, db: Session, storage: StorageProvider):
        self.db = db
        self.storage = storage

    def _get_document(self, org_id: uuid.UUID, doc_id: uuid.UUID) -> Document:
        doc = self.db.query(Document).filter(
            Document.id == doc_id,
            Document.organization_id == org_id
        ).first()
        if not doc:
            raise KramaException(
                status_code=404,
                code="DOCUMENT_NOT_FOUND",
                message="Document not found"
            )
        return doc

    def _get_or_create_job_stage(self, doc: Document) -> JobStage:
        # Find active document processing job
        job = self.db.query(Job).filter(
            Job.document_id == doc.id,
            Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
        ).first()

        if not job:
            # Fallback to creating a new one if somehow missing
            job = Job(
                organization_id=doc.organization_id,
                document_id=doc.id,
                job_type="DOCUMENT_PROCESSING",
                status=JobStatus.RUNNING
            )
            self.db.add(job)
            self.db.flush()

        if job.status == JobStatus.PENDING:
            job.status = JobStatus.RUNNING

        stage = self.db.query(JobStage).filter(
            JobStage.job_id == job.id,
            JobStage.stage_name == "CLASSIFY"
        ).first()

        if not stage:
            # Determine next sequence
            max_seq = 0
            if job.stages:
                max_seq = max(s.sequence for s in job.stages)
            
            stage = JobStage(
                job_id=job.id,
                stage_name="CLASSIFY",
                status=JobStageStatus.PENDING,
                sequence=max_seq + 1
            )
            self.db.add(stage)
            self.db.flush()

        return stage

    def _build_classification_input(self, doc: Document) -> ClassificationInput:
        pages = doc.pages
        # Sort by page number
        pages = sorted(pages, key=lambda p: p.page_number)
        
        full_text_parts = []
        pages_text: Dict[int, str] = {}
        
        for page in pages:
            # Get OCR result for page
            ocr_result = self.db.query(OCRPageResult).filter(OCRPageResult.page_id == page.id).first()
            if ocr_result:
                page_text = ocr_result.full_text or ""
                pages_text[page.page_number] = page_text
                full_text_parts.append(page_text)
            else:
                pages_text[page.page_number] = ""
                
        ocr_text = "\n".join(full_text_parts)
        
        return ClassificationInput(
            document_id=str(doc.id),
            original_filename=doc.original_filename,
            ocr_text=ocr_text,
            pages_text=pages_text,
            metadata={}
        )

    def classify_document(self, org_id: uuid.UUID, doc_id: uuid.UUID) -> DocumentClassification:
        """
        Orchestrates document classification.
        """
        doc = self._get_document(org_id, doc_id)
        
        logger.info(f"classification_started org={org_id} doc_id={doc_id}")

        # Idempotency check
        if doc.status == DocumentStatus.CLASSIFIED:
            existing = self.db.query(DocumentClassification).filter(DocumentClassification.document_id == doc.id).first()
            if existing:
                logger.info(f"classification_already_completed doc_id={doc_id}")
                return existing

        # Eligibility check
        if doc.status != DocumentStatus.OCR_COMPLETED:
            if doc.status in (DocumentStatus.CLASSIFICATION_FAILED, DocumentStatus.CLASSIFICATION_PROCESSING):
                # Allowed to retry
                pass
            else:
                # Includes OCR_PARTIAL, which we reject
                logger.warning(f"classification_rejected_status doc_id={doc_id} status={doc.status}")
                raise DocumentNotReadyForClassificationException(doc_id, doc.status.value)

        # Transition to processing
        doc.status = DocumentStatus.CLASSIFICATION_PROCESSING
        stage = self._get_or_create_job_stage(doc)
        stage.status = JobStageStatus.RUNNING
        stage.started_at = stage.started_at or datetime.now(timezone.utc)
        self.db.commit()

        # Classification Execution
        artifact_key = None
        try:
            # 1. Resolve configured classifier
            classifier = get_classifier(Config.CLASSIFICATION_PROVIDER)
            
            # 2. Build input
            input_data = self._build_classification_input(doc)
            
            # 3. Execute
            raw_result = classifier.classify(input_data)
            
            # 4. Normalize
            result = ClassificationNormalizer.normalize(raw_result)
            
            # 5. Build Artifact
            artifact_key = f"artifacts/{org_id}/{doc.claim_id}/{doc_id}/classification/result.json"
            artifact_data = {
                "schema_version": "1.0",
                "document_id": str(doc_id),
                "document_type": result.document_type,
                "confidence": result.confidence,
                "classifier": {
                    "name": result.classifier_name,
                    "version": result.classifier_version
                },
                "evidence": result.evidence
            }
            artifact_bytes = json.dumps(artifact_data, indent=2).encode('utf-8')
            
            # 6. Save Artifact
            import io
            self.storage.save_stream(artifact_key, io.BytesIO(artifact_bytes))
            
            # 7. Persist to DB
            existing_class = self.db.query(DocumentClassification).filter(DocumentClassification.document_id == doc.id).first()
            if existing_class:
                self.db.delete(existing_class)
                self.db.flush()

            classification = DocumentClassification(
                organization_id=doc.organization_id,
                document_id=doc.id,
                classifier_name=result.classifier_name,
                classifier_version=result.classifier_version,
                document_type=result.document_type,
                confidence=result.confidence,
                evidence_json=result.evidence,
                artifact_storage_key=artifact_key
            )
            self.db.add(classification)
            
            # Synchronize Document Type
            doc.document_type = result.document_type

            # 8. Complete Pipeline
            doc.status = DocumentStatus.CLASSIFIED
            stage.status = JobStageStatus.SUCCEEDED
            stage.progress = 100
            stage.completed_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"classification_completed doc_id={doc_id} type={result.document_type} conf={result.confidence}")
            return classification

        except ProviderUnavailableException as e:
            self.db.rollback()
            logger.error(f"classification_failed doc_id={doc_id} error={str(e)}")
            self._handle_failure(doc_id, stage, str(e), artifact_key)
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"classification_failed doc_id={doc_id} error={str(e)}")
            self._handle_failure(doc_id, stage, str(e), artifact_key)
            raise ClassificationFailedException(doc_id, str(e))

    def _handle_failure(self, doc_id: uuid.UUID, stage: JobStage, error_message: str, artifact_key: str = None):
        """Compensate on failure: delete artifact, set status."""
        if artifact_key:
            try:
                self.storage.delete(artifact_key)
                logger.info(f"classification_compensation_completed doc_id={doc_id} key={artifact_key}")
            except Exception as ce:
                logger.error(f"classification_compensation_failed doc_id={doc_id} key={artifact_key} error={str(ce)}")

        doc = self.db.get(Document, doc_id)
        if doc:
            doc.status = DocumentStatus.CLASSIFICATION_FAILED
            stage.status = JobStageStatus.FAILED
            stage.error_message = error_message[:1024]
            stage.completed_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_classification(self, org_id: uuid.UUID, doc_id: uuid.UUID) -> DocumentClassification:
        doc = self._get_document(org_id, doc_id)
        classification = self.db.query(DocumentClassification).filter(DocumentClassification.document_id == doc.id).first()
        if not classification:
            raise KramaException(
                status_code=404,
                code="CLASSIFICATION_NOT_FOUND",
                message="Classification not found for this document."
            )
        return classification

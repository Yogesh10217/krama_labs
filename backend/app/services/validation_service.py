import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import func

from sqlalchemy.orm import Session

from app.core.config import Config
from app.db.models.document import Document
from app.db.models.ocr import OCRPageResult, OCRRegion
from app.db.models.extraction import ExtractionRun
from app.db.models.job import Job
from app.db.models.job_stage import JobStage
from app.domain.enums import DocumentStatus, JobStageStatus, ValidationStatus
from app.storage.base import StorageProvider
from app.validation.registry import get_validator
from app.validation.base import ValidationInput

from app.db.models.validation import ValidationRun, ValidatedField, ValidationEvidence
from app.core.exceptions import (
    KramaException, 
    DocumentNotReadyForValidationException,
    ValidationFailedException
)

logger = logging.getLogger(__name__)

class ValidationService:
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

    def validate_document(self, org_id: uuid.UUID, doc_id: uuid.UUID) -> ValidationRun:
        doc = self._get_document(org_id, doc_id)
        
        # Idempotency check
        if doc.status == DocumentStatus.VALIDATED:
            existing_run = self.db.query(ValidationRun).filter(ValidationRun.document_id == doc.id).first()
            if existing_run:
                logger.info(f"validation_already_completed doc_id={doc_id}")
                return existing_run

        # Eligibility check
        if doc.status not in (DocumentStatus.EXTRACTED, DocumentStatus.VALIDATION_FAILED):
            logger.warning(f"validation_rejected_status doc_id={doc_id} status={doc.status}")
            raise DocumentNotReadyForValidationException(str(doc_id), doc.status.value)
            
        extraction_run = self.db.query(ExtractionRun).filter(ExtractionRun.document_id == doc.id).first()
        if not extraction_run:
            raise DocumentNotReadyForValidationException(str(doc_id), "MISSING_EXTRACTION")

        # Transition to processing
        doc.status = DocumentStatus.VALIDATION_PROCESSING
        self.db.commit()

        # Job Stage setup
        job = self.db.query(Job).filter(Job.document_id == doc.id).first()
        stage = None
        if job:
            stage = self.db.query(JobStage).filter(
                JobStage.job_id == job.id,
                JobStage.stage_name == "VALIDATE"
            ).first()
            if not stage:
                max_seq = self.db.query(func.max(JobStage.sequence)).filter(JobStage.job_id == job.id).scalar() or 0
                stage = JobStage(
                    job_id=job.id,
                    stage_name="VALIDATE",
                    sequence=max_seq + 1,
                    status=JobStageStatus.RUNNING,
                    started_at=datetime.now(timezone.utc)
                )
                self.db.add(stage)
            else:
                stage.status = JobStageStatus.RUNNING
                stage.started_at = datetime.now(timezone.utc)
            self.db.commit()

        start_time = datetime.now(timezone.utc)
        logger.info(f"validation_started org={org_id} doc_id={doc_id}")

        artifact_key = f"artifacts/{org_id}/{doc.claim_id}/{doc_id}/validation/result.json"
        artifact_saved = False
        
        try:
            # 1. Load OCR data
            pages = self.db.query(OCRPageResult).filter(OCRPageResult.page_id.in_([p.id for p in doc.pages])).all()
            regions = []
            for page in pages:
                regions.extend(page.regions)
                
            # 2. Extract Fields
            extracted_fields = extraction_run.fields
                
            # 3. Validate
            validator = get_validator(Config.VALIDATION_PROVIDER)
            
            input_data = ValidationInput(
                document_id=doc.id,
                document_type=extraction_run.classification.document_type,
                pages=pages,
                regions=regions,
                extracted_fields=extracted_fields
            )
            
            result = validator.validate(input_data)
            
            # 4. Save artifact
            artifact_data = result.model_dump(mode="json")
            
            # Count summary
            summary = {
                "SUPPORTED": 0,
                "PARTIALLY_SUPPORTED": 0,
                "UNSUPPORTED": 0,
                "MISSING_EVIDENCE": 0,
                "AMBIGUOUS": 0
            }
            for f in result.fields:
                if f.validation_status in summary:
                    summary[f.validation_status] += 1
                else:
                    summary[f.validation_status] = 1
            artifact_data["summary"] = summary
            
            artifact_bytes = json.dumps(artifact_data, indent=2).encode('utf-8')
            
            import io
            self.storage.save_stream(artifact_key, io.BytesIO(artifact_bytes))
            artifact_saved = True

            # 5. DB Persistence
            # Handle retry behavior: drop old validation run if it exists
            existing_run = self.db.query(ValidationRun).filter(ValidationRun.document_id == doc.id).first()
            if existing_run:
                self.db.delete(existing_run)
                self.db.flush() # DO NOT commit here to preserve atomicity
            
            completed_time = datetime.now(timezone.utc)
            duration_ms = (completed_time - start_time).total_seconds() * 1000.0

            new_run = ValidationRun(
                organization_id=org_id,
                document_id=doc.id,
                extraction_run_id=extraction_run.id,
                validator_name=result.validator_name,
                validator_version=result.validator_version,
                status="COMPLETED",
                artifact_storage_key=artifact_key,
                started_at=start_time,
                completed_at=completed_time,
                processing_time_ms=duration_ms
            )
            self.db.add(new_run)
            self.db.flush() # get id
            
            for field in result.fields:
                new_field = ValidatedField(
                    validation_run_id=new_run.id,
                    extracted_field_id=field.extracted_field_id,
                    validation_status=field.validation_status,
                    validation_score=field.validation_score,
                    validation_reason=field.validation_reason,
                )
                self.db.add(new_field)
                self.db.flush()
                
                for ev in field.evidence:
                    new_ev = ValidationEvidence(
                        validated_field_id=new_field.id,
                        page_id=ev.page_id,
                        ocr_region_id=ev.ocr_region_id,
                        support_type=ev.support_type,
                        confidence=ev.confidence
                    )
                    self.db.add(new_ev)

            doc = self.db.get(Document, doc_id) # Reload to be safe
            doc.status = DocumentStatus.VALIDATED
            
            if stage:
                stage.status = JobStageStatus.SUCCEEDED
                stage.progress = 100
                stage.completed_at = completed_time
                
            self.db.commit()
            
            logger.info(f"validation_completed doc_id={doc_id} fields={len(result.fields)}")
            return new_run
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"validation_failed doc_id={doc_id} error={str(e)}")
            
            # Compensation: delete ONLY the validation artifact if we failed to save DB and actually created it
            if artifact_saved:
                try:
                    self.storage.delete(artifact_key)
                    logger.info(f"validation_compensation_completed doc_id={doc_id} key={artifact_key}")
                except Exception as ce:
                    logger.error(f"validation_compensation_failed doc_id={doc_id} key={artifact_key} error={str(ce)}")
                
            doc = self.db.get(Document, doc_id)
            if doc:
                doc.status = DocumentStatus.VALIDATION_FAILED
                if stage:
                    stage.status = JobStageStatus.FAILED
                    stage.error_message = str(e)
                    stage.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                
            raise ValidationFailedException(str(doc_id), str(e))

    def get_validation(self, org_id: uuid.UUID, doc_id: uuid.UUID) -> ValidationRun:
        doc = self._get_document(org_id, doc_id)
        run = self.db.query(ValidationRun).filter(ValidationRun.document_id == doc.id).first()
        if not run:
            raise KramaException(
                status_code=404,
                code="VALIDATION_NOT_FOUND",
                message="Validation not found for this document."
            )
        return run

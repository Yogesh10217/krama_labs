import uuid
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import func
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.core.config import Config
from app.db.models.document import Document
from app.db.models.classification import DocumentClassification
from app.db.models.ocr import OCRPageResult, OCRRegion
from app.db.models.extraction import ExtractionRun, ExtractedField, FieldEvidence
from app.db.models.job import Job
from app.db.models.job_stage import JobStage
from app.domain.enums import DocumentStatus, JobStageStatus, ExtractionStatus
from app.storage.base import StorageProvider
from app.extraction.registry import get_extractor
from app.extraction.field_registry import get_schema
from app.extraction.base import ExtractionInput
from app.core.exceptions import (
    KramaException, 
    DocumentNotReadyForExtractionException,
    ExtractionFailedException
)

logger = logging.getLogger(__name__)


class ExtractionService:
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

    def _get_classification(self, doc_id: uuid.UUID) -> DocumentClassification:
        classification = self.db.query(DocumentClassification).filter(DocumentClassification.document_id == doc_id).first()
        if not classification:
            raise KramaException(
                status_code=400,
                code="DOCUMENT_NOT_CLASSIFIED",
                message="Document must be successfully classified before extraction."
            )
        return classification

    def extract_document(self, org_id: uuid.UUID, doc_id: uuid.UUID) -> ExtractionRun:
        doc = self._get_document(org_id, doc_id)
        
        # Idempotency check
        if doc.status == DocumentStatus.EXTRACTED:
            existing_run = self.db.query(ExtractionRun).filter(ExtractionRun.document_id == doc.id).first()
            if existing_run:
                logger.info(f"extraction_already_completed doc_id={doc_id}")
                return existing_run

        # Eligibility
        if doc.status not in (DocumentStatus.CLASSIFIED, DocumentStatus.EXTRACTION_FAILED):
            logger.warning(f"extraction_rejected_status doc_id={doc_id} status={doc.status}")
            raise DocumentNotReadyForExtractionException(doc_id, doc.status.value)
            
        classification = self._get_classification(doc.id)
        schema = get_schema(classification.document_type)

        # Transition to processing
        doc.status = DocumentStatus.EXTRACTION_PROCESSING
        self.db.commit()

        # Job Stage setup
        job = self.db.query(Job).filter(Job.document_id == doc.id).first()
        stage = None
        if job:
            stage = self.db.query(JobStage).filter(
                JobStage.job_id == job.id,
                JobStage.stage_name == "EXTRACT"
            ).first()
            if not stage:
                max_seq = self.db.query(func.max(JobStage.sequence)).filter(JobStage.job_id == job.id).scalar() or 0
                stage = JobStage(
                    job_id=job.id,
                    stage_name="EXTRACT",
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
        logger.info(f"extraction_started org={org_id} doc_id={doc_id} type={classification.document_type}")

        artifact_key = f"artifacts/{org_id}/{doc.claim_id}/{doc_id}/extraction/result.json"
        artifact_saved = False
        
        try:
            # 1. Load OCR data
            pages = self.db.query(OCRPageResult).filter(OCRPageResult.page_id.in_([p.id for p in doc.pages])).all()
            regions = []
            for page in pages:
                regions.extend(page.regions)
                
            # 2. Extract
            extractor = get_extractor(Config.EXTRACTION_PROVIDER)
            
            input_data = ExtractionInput(
                document_id=doc.id,
                document_type=classification.document_type,
                extraction_schema=schema,
                pages=pages,
                regions=regions
            )
            
            result = extractor.extract(input_data)
            
            # 3. Save artifact
            artifact_data = result.model_dump(mode="json")
            artifact_bytes = json.dumps(artifact_data, indent=2).encode('utf-8')
            
            import io
            self.storage.save_stream(artifact_key, io.BytesIO(artifact_bytes))
            artifact_saved = True

            # 4. DB Persistence
            # Handle retry behavior: drop old extraction run if it exists
            existing_run = self.db.query(ExtractionRun).filter(ExtractionRun.document_id == doc.id).first()
            if existing_run:
                self.db.delete(existing_run)
                self.db.flush() # DO NOT commit here to preserve atomicity
            
            completed_time = datetime.now(timezone.utc)
            duration_ms = (completed_time - start_time).total_seconds() * 1000.0

            new_run = ExtractionRun(
                organization_id=org_id,
                document_id=doc.id,
                classification_id=classification.id,
                extractor_name=result.extractor_name,
                extractor_version=result.extractor_version,
                schema_name=result.schema_name,
                schema_version=result.schema_version,
                status=ExtractionStatus.COMPLETED,
                artifact_storage_key=artifact_key,
                started_at=start_time,
                completed_at=completed_time,
                processing_time_ms=duration_ms
            )
            self.db.add(new_run)
            self.db.flush() # get id
            
            for field in result.fields:
                new_field = ExtractedField(
                    extraction_run_id=new_run.id,
                    field_name=field.name,
                    raw_value=field.raw_value,
                    normalized_value=field.normalized_value,
                    data_type=field.data_type,
                    confidence=field.confidence
                )
                self.db.add(new_field)
                self.db.flush()
                
                for ev in field.evidence:
                    new_ev = FieldEvidence(
                        extracted_field_id=new_field.id,
                        page_id=ev.page_id,
                        ocr_region_id=ev.ocr_region_id,
                        evidence_type=ev.rule_id,
                        confidence=ev.confidence
                    )
                    self.db.add(new_ev)

            doc = self.db.get(Document, doc_id) # Reload to be safe
            doc.status = DocumentStatus.EXTRACTED
            
            if stage:
                stage.status = JobStageStatus.SUCCEEDED
                stage.progress = 100
                stage.completed_at = completed_time
                
            self.db.commit()
            
            logger.info(f"extraction_completed doc_id={doc_id} fields={len(result.fields)}")
            return new_run
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"extraction_failed doc_id={doc_id} error={str(e)}")
            
            # Compensation: delete ONLY the extraction artifact if we failed to save DB and actually created it
            if artifact_saved:
                try:
                    self.storage.delete(artifact_key)
                    logger.info(f"extraction_compensation_completed doc_id={doc_id} key={artifact_key}")
                except Exception as ce:
                    logger.error(f"extraction_compensation_failed doc_id={doc_id} key={artifact_key} error={str(ce)}")
                
            doc = self.db.get(Document, doc_id)
            if doc:
                doc.status = DocumentStatus.EXTRACTION_FAILED
                if stage:
                    stage.status = JobStageStatus.FAILED
                    stage.error_message = str(e)
                    stage.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                
            raise ExtractionFailedException(doc_id, str(e))

    def get_extraction(self, org_id: uuid.UUID, doc_id: uuid.UUID) -> ExtractionRun:
        doc = self._get_document(org_id, doc_id)
        run = self.db.query(ExtractionRun).filter(ExtractionRun.document_id == doc.id).first()
        if not run:
            raise KramaException(
                status_code=404,
                code="EXTRACTION_NOT_FOUND",
                message="Extraction not found for this document."
            )
        return run

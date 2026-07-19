"""Document intelligence endpoints: processing, document types, and retrieval."""

import os
import uuid
import json
import base64
import logging
from io import BytesIO
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import Config
from app.core.exceptions import KramaException, ServiceUnavailableException, ValidationException, NotFoundException
from app.engines.classifier import DOCUMENT_TAXONOMY

router = APIRouter()
logger = logging.getLogger(__name__)

# Global processor instance (lazy initialized)
_processor = None


def get_processor():
    """Lazily load the DocumentProcessor service."""
    global _processor
    if _processor is None:
        try:
            from app.services.pipeline import DocumentProcessor
            _processor = DocumentProcessor()
        except ImportError as e:
            logger.error(f"Failed to import DocumentProcessor: {e}")
            raise ServiceUnavailableException(
                message=f"Document processing libraries (e.g. paddleocr) are not installed on the server: {str(e)}",
                code="OCR_LIBRARIES_MISSING"
            )
    return _processor


@router.get("/doc-types")
async def list_document_types():
    """List all supported document types with categories and labels."""
    types = []
    for key, info in DOCUMENT_TAXONOMY.items():
        types.append({
            "type": key,
            "label": info["label"],
            "category": info["category"],
            "description": info["description"],
        })
    return {"document_types": types, "count": len(types)}


@router.post("/process")
async def process_document(file: UploadFile = File(...)):
    """Upload and process a document using OCR-only pipeline. No API key required."""
    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(Config.RESULTS_DIR, exist_ok=True)

    # Validate file
    if not file.filename:
        raise ValidationException("No file provided", "FILE_MISSING")

    allowed_ext = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".gif", ".xlsx", ".xls", ".pptx", ".ppt"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_ext:
        raise ValidationException(f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_ext)}", "UNSUPPORTED_TYPE")

    # Read contents and check size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > Config.MAX_FILE_SIZE_MB:
        raise ValidationException(f"File too large: {size_mb:.1f}MB (max {Config.MAX_FILE_SIZE_MB}MB)", "FILE_TOO_LARGE")

    # Save to temp file
    job_id = str(uuid.uuid4())[:8]
    save_path = os.path.join(Config.UPLOAD_DIR, f"{job_id}_{file.filename}")

    with open(save_path, "wb") as f:
        f.write(contents)

    try:
        # Get processor (this raises ServiceUnavailableException if imports fail)
        proc = get_processor()
        
        # Execute pipeline
        result = proc.process(save_path)

        # Build response JSON
        response = result.to_json()
        response["job_id"] = job_id
        response["filename"] = file.filename
        response["file_size_mb"] = round(size_mb, 2)

        # Generate annotated image preview (first page with bounding boxes)
        if result.pages and result.pages[0].ocr_regions:
            try:
                from app.engines.converter import DocumentConverter
                from PIL import Image, ImageDraw

                images, _ = DocumentConverter.convert(save_path)
                if images:
                    img = images[0].copy()
                    draw = ImageDraw.Draw(img)
                    for region in result.pages[0].ocr_regions:
                        bbox = region.bbox
                        draw.rectangle([bbox.x1, bbox.y1, bbox.x2, bbox.y2], outline="lime", width=2)

                    # Encode as base64
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    response["annotated_image"] = base64.b64encode(buf.read()).decode("utf-8")

                    # Also encode original
                    buf2 = BytesIO()
                    images[0].save(buf2, format="PNG")
                    buf2.seek(0)
                    response["original_image"] = base64.b64encode(buf2.read()).decode("utf-8")
            except Exception as cv_err:
                logger.warning(f"Could not build visual image preview: {cv_err}")

        # Save result JSON
        result_path = os.path.join(Config.RESULTS_DIR, f"{job_id}.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2, ensure_ascii=False)

        return JSONResponse(content=response)

    except KramaException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        # Cleanup temp file
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception as cleanup_err:
            logger.warning(f"Could not delete temp file {save_path}: {cleanup_err}")


@router.get("/results/{job_id}")
async def get_results(job_id: str):
    """Retrieve processing results by job ID."""
    result_path = os.path.join(Config.RESULTS_DIR, f"{job_id}.json")
    if not os.path.exists(result_path):
        raise NotFoundException(f"Results not found for job: {job_id}", "JOB_NOT_FOUND")

    with open(result_path, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))

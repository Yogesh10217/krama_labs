"""V1 Pages API routes.

Endpoints:
    GET /api/v1/pages/{page_id}/content — Stream canonical page PNG content.

Organization context is required via X-Organization-ID header.
"""
import logging
import uuid
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_organization_context
from app.core.config import Config
from app.core.exceptions import DocumentContentNotFoundException, NotFoundException
from app.db.models.organization import Organization
from app.db.session import get_db
from app.repositories.page import PageRepository
from app.storage.base import StorageNotFoundError
from app.storage.factory import get_storage_provider

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/{page_id}/content",
    summary="Stream canonical page PNG content",
    tags=["Pages"],
)
def get_page_content(
    page_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    """Stream the raw canonical PNG representation of the page.

    **Security:** Tenant-isolated (requires valid X-Organization-ID).
    """
    page_repo = PageRepository(db)
    page = page_repo.get_by_id_and_org(page_id, org.id)
    if not page:
        raise NotFoundException("Page not found.")

    if not page.storage_key:
        raise DocumentContentNotFoundException("This page does not have stored file content.")

    storage = get_storage_provider()
    if not storage.exists(page.storage_key):
        raise DocumentContentNotFoundException("Page artifact is not available in storage.")

    try:
        file_stream = storage.open(page.storage_key)
    except StorageNotFoundError:
        raise DocumentContentNotFoundException("Page artifact not found in storage.")

    def _iter_stream():
        try:
            while True:
                chunk = file_stream.read(Config.UPLOAD_CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                yield chunk
        finally:
            file_stream.close()

    return StreamingResponse(
        content=_iter_stream(),
        media_type="image/png",
    )

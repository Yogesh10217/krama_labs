"""Central API router registry."""

from fastapi import APIRouter
from app.api.routes import health, document, chat, demo

# Primary legacy/root router for backward compatibility with frontend
api_router = APIRouter()

# Mount routes under /api
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(document.router, tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(demo.router, tags=["Demo"])

# Versioned V1 router
v1_router = APIRouter()

# Mount legacy health/doc/chat endpoints in v1 for compat (as required by tests)
v1_router.include_router(health.router, tags=["Health"])
v1_router.include_router(document.router, tags=["Legacy Documents"])
v1_router.include_router(chat.router, prefix="/chat", tags=["Legacy Chat"])
v1_router.include_router(demo.router, tags=["Legacy Demo"])

# Mount new Phase 1 production routes
from app.api.routes.v1 import organizations, claims, documents as v1_docs, jobs, pages as v1_pages, providers, review

v1_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
v1_router.include_router(claims.router, prefix="/claims", tags=["Claims"])
v1_router.include_router(v1_docs.router, tags=["Documents"])
v1_router.include_router(jobs.router, tags=["Jobs"])
v1_router.include_router(v1_pages.router, prefix="/pages", tags=["Pages"])
v1_router.include_router(providers.router, prefix="/providers", tags=["Providers"])
v1_router.include_router(review.router, prefix="/documents", tags=["Review & Final Document"])

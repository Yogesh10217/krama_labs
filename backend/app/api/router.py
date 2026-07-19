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

# Mount routes under /api/v1
v1_router.include_router(health.router, tags=["Health"])
v1_router.include_router(document.router, tags=["Documents"])
v1_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
v1_router.include_router(demo.router, tags=["Demo"])

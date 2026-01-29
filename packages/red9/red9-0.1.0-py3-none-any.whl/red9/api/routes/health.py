"""Health check endpoint for RED9 API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    timestamp: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Health check endpoint that returns the status of the service."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
    )

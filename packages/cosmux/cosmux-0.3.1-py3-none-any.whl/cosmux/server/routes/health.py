"""Health check endpoint"""

import os
from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "workspace": os.environ.get("COSMUX_WORKSPACE", "not set"),
    }


@router.get("/")
async def root() -> dict:
    """Root endpoint - API info"""
    return {
        "name": "Cosmux API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }

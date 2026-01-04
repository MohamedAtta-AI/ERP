"""
Health check endpoint.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check for load balancers and monitoring."""
    return {
        "status": "healthy",
        "service": "ontime-erp-api",
        "version": "0.1.0",
    }


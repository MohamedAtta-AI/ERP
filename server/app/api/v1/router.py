"""
Main API v1 router aggregating all endpoint routers.
"""

from fastapi import APIRouter

from .attendance import router as attendance_router
from .persons import router as persons_router
from .health import router as health_router

router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(health_router, tags=["Health"])
router.include_router(persons_router, prefix="/employees", tags=["Employees"])
router.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])


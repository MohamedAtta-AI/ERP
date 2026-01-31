from fastapi import APIRouter

from server.app.api.v1.people import router as people_router
from server.app.api.v1.locations import router as locations_router
from server.app.api.v1.shifts import router as shifts_router
from server.app.api.v1.assignments import router as assignments_router
from server.app.api.v1.attendance import router as attendance_router
from server.app.api.v1.auth import router as auth_router

router = APIRouter()

router.include_router(people_router, prefix="/employees", tags=["Employees"])
router.include_router(locations_router, prefix="/locations", tags=["Locations"])
router.include_router(shifts_router, prefix="/shifts", tags=["Shifts"])
router.include_router(assignments_router, prefix="/assignments", tags=["Assignments"])
router.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])

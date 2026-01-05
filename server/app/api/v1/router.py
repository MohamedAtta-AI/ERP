"""
Main API v1 router aggregating all endpoint routers.
"""

from fastapi import APIRouter

from .attendance import router as attendance_router
from .persons import router as persons_router
from .health import router as health_router
from .locations import router as locations_router
from .shifts import router as shifts_router
from .skills import router as skills_router
from .assignments import router as assignments_router
from .overtime import router as overtime_router
from .payroll import router as payroll_router
from .auth import router as auth_router
from .salary_advances import router as salary_advances_router
from .loans import router as loans_router
from .payslips import router as payslips_router
from .reports import router as reports_router
from .bank_transfers import router as bank_transfers_router
from .settlements import router as settlements_router

router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(health_router, tags=["Health"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(persons_router, prefix="/employees", tags=["Employees"])
router.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
router.include_router(locations_router, prefix="/locations", tags=["Locations"])
router.include_router(shifts_router, prefix="/shifts", tags=["Shifts"])
router.include_router(skills_router, prefix="/skills", tags=["Skills"])
router.include_router(assignments_router, prefix="/assignments", tags=["Assignments"])
router.include_router(overtime_router, prefix="/overtime", tags=["Overtime"])
router.include_router(payroll_router, prefix="/payroll", tags=["Payroll"])
router.include_router(salary_advances_router, prefix="/salary-advances", tags=["Salary Advances"])
router.include_router(loans_router, prefix="/loans", tags=["Loans"])
router.include_router(payslips_router, prefix="/payslips", tags=["Payslips"])
router.include_router(reports_router, prefix="/reports", tags=["Reports"])
router.include_router(bank_transfers_router, prefix="/bank-transfers", tags=["Bank Transfers"])
router.include_router(settlements_router, prefix="/settlements", tags=["Settlements"])



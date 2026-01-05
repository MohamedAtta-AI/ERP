"""
Attendance Automation Service

Handles automatic reconciliation of attendance records:
- Mark absent if no check-in by shift end
- Create overtime requests for missing check-outs
"""

from datetime import date, datetime, time
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from server.db.models import (
    Attendance, AttendanceStatus, Shift, Assignment,
    OvertimeRequest, OvertimeRequestStatus,
)


async def reconcile_attendance(
    target_date: date,
    session: AsyncSession,
) -> dict:
    """
    Reconcile attendance for a specific date.
    
    Rules:
    1. If check_in exists but check_out is missing and shift has ended -> 
       status=overtime_pending, create OvertimeRequest
    2. If no check_in by shift end -> status=absent
    
    Returns:
        dict with counts of updated records
    """
    stats = {
        "absent_marked": 0,
        "overtime_pending_marked": 0,
        "overtime_requests_created": 0,
    }
    
    # Get all attendance records for the date
    stmt = select(Attendance).where(Attendance.attendance_date == target_date)
    result = await session.execute(stmt)
    attendances = result.scalars().all()
    
    now = datetime.utcnow()
    current_time = now.time()
    
    for attendance in attendances:
        # Skip if already processed
        if attendance.status in [AttendanceStatus.ABSENT, AttendanceStatus.OVERTIME_PENDING]:
            continue
        
        # Get shift info if available
        shift = None
        if attendance.shift_id:
            shift_stmt = select(Shift).where(Shift.id == attendance.shift_id)
            shift_result = await session.execute(shift_stmt)
            shift = shift_result.scalar_one_or_none()
        
        # Rule 1: No check-in by shift end -> mark absent
        if not attendance.check_in:
            if shift:
                shift_end = shift.ends_at
                # For overnight shifts, check if we're past the end time
                if shift.is_overnight:
                    # Overnight shift: ends_at is next day, so check if current time < ends_at
                    # This is simplified - in production, handle date boundaries properly
                    if current_time < shift.ends_at:
                        continue  # Still within shift window
                else:
                    # Regular shift: if current time > shift end, mark absent
                    if current_time > shift.ends_at:
                        attendance.status = AttendanceStatus.ABSENT
                        attendance.updated_at = now
                        session.add(attendance)
                        stats["absent_marked"] += 1
            else:
                # No shift info - mark absent if it's past end of day
                if current_time > time(23, 59):
                    attendance.status = AttendanceStatus.ABSENT
                    attendance.updated_at = now
                    session.add(attendance)
                    stats["absent_marked"] += 1
        
        # Rule 2: Check-in exists, check-out missing, shift ended -> overtime_pending
        elif attendance.check_in and not attendance.check_out:
            if shift:
                shift_end = shift.ends_at
                # Check if shift has ended
                if shift.is_overnight:
                    # Simplified: assume shift ended if we're past ends_at
                    shift_ended = current_time < shift.ends_at  # Overnight logic
                else:
                    shift_ended = current_time > shift.ends_at
                
                if shift_ended:
                    # Mark as overtime_pending
                    attendance.status = AttendanceStatus.OVERTIME_PENDING
                    attendance.updated_at = now
                    session.add(attendance)
                    stats["overtime_pending_marked"] += 1
                    
                    # Create overtime request if one doesn't exist
                    existing_ot_stmt = select(OvertimeRequest).where(
                        and_(
                            OvertimeRequest.attendance_id == attendance.id,
                            OvertimeRequest.status == OvertimeRequestStatus.PENDING,
                        )
                    )
                    existing_ot_result = await session.execute(existing_ot_stmt)
                    if not existing_ot_result.scalar_one_or_none():
                        # Calculate overtime hours (simplified)
                        check_in_time = attendance.check_in.time()
                        if shift.is_overnight:
                            # Handle overnight shift calculation
                            hours = 0  # Simplified
                        else:
                            # Calculate hours from shift end to now
                            from datetime import timedelta
                            shift_end_dt = datetime.combine(target_date, shift.ends_at)
                            if now > shift_end_dt:
                                delta = now - shift_end_dt
                                hours = round(delta.total_seconds() / 3600, 2)
                            else:
                                hours = 0
                        
                        if hours > 0:
                            overtime = OvertimeRequest(
                                person_id=attendance.person_id,
                                attendance_id=attendance.id,
                                overtime_date=target_date,
                                hours=hours,
                                status=OvertimeRequestStatus.PENDING,
                            )
                            session.add(overtime)
                            stats["overtime_requests_created"] += 1
    
    await session.flush()
    return stats


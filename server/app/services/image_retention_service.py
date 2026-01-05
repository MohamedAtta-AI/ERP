"""
Image Retention Service

Handles deletion of old attendance images based on retention policy.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from server.db.models import Attendance


async def delete_old_images(
    session: AsyncSession,
    retention_months: int = 6,
) -> dict:
    """
    Delete old attendance images based on retention policy.
    
    Queries Attendance records where attendance_date < (now - retention_months).
    Deletes image files from data/uploads/.
    Updates Attendance records to set image_url = None.
    
    Returns summary of deleted images.
    """
    cutoff_date = date.today() - timedelta(days=retention_months * 30)
    
    # Find old attendance records with images
    stmt = select(Attendance).where(
        and_(
            Attendance.attendance_date < cutoff_date,
            Attendance.image_url.isnot(None),
        )
    )
    result = await session.execute(stmt)
    old_attendances = result.scalars().all()
    
    deleted_count = 0
    failed_count = 0
    
    for attendance in old_attendances:
        if attendance.image_url:
            try:
                # Delete image file
                image_path = Path(attendance.image_url)
                if image_path.exists():
                    image_path.unlink()
                    deleted_count += 1
                else:
                    # File doesn't exist, just update record
                    deleted_count += 1
            except Exception as e:
                # Log error but continue
                print(f"Error deleting image {attendance.image_url}: {e}")
                failed_count += 1
            
            # Update record to remove image_url
            attendance.image_url = None
            session.add(attendance)
    
    await session.flush()
    
    return {
        "cutoff_date": cutoff_date.isoformat(),
        "records_processed": len(old_attendances),
        "images_deleted": deleted_count,
        "failed_deletions": failed_count,
    }


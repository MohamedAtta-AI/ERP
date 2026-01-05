"""
Audit Logging Service

Logs all changes to payroll-related tables for audit trail.
"""

import json
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from server.db.models import AuditLog


async def log_change(
    table_name: str,
    record_id: str,
    action: str,  # CREATE, UPDATE, DELETE
    changed_by_person_id: Optional[str],
    session: AsyncSession,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Log a change to a database record.
    
    Creates AuditLog record with old_values and new_values as JSON.
    Called from all update/create/delete operations.
    """
    audit_log = AuditLog(
        table_name=table_name,
        record_id=str(record_id),
        action=action.upper(),
        changed_by_person_id=changed_by_person_id,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
    )
    
    session.add(audit_log)
    await session.flush()
    await session.refresh(audit_log)
    
    return audit_log


async def get_audit_trail(
    table_name: str,
    record_id: str,
    session: AsyncSession,
) -> List[AuditLog]:
    """
    Get audit trail for a specific record.
    
    Queries AuditLog filtered by table_name and record_id.
    Returns chronological list of changes.
    """
    stmt = select(AuditLog).where(
        and_(
            AuditLog.table_name == table_name,
            AuditLog.record_id == str(record_id),
        )
    ).order_by(AuditLog.timestamp.asc())
    
    result = await session.execute(stmt)
    logs = result.scalars().all()
    
    return list(logs)


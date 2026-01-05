"""
Bank Transfer File Service

Generates bank transfer files (CSV/Excel) with employee payment information.
"""

from pathlib import Path
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.db.models import PayrollRun, PayrollRunEmployee, Person


async def generate_bank_file(
    payroll_run_id: UUID,
    session: AsyncSession,
    format: str = "csv",  # "csv" or "excel"
) -> Path:
    """
    Generate bank transfer file (CSV or Excel).
    
    Format: Name, National ID (identity_number), Bank ID (account_number or IBAN), Salary (net)
    Saves to data/uploads/bank_transfers/
    Returns file path.
    """
    # Get payroll run with employees and period relationship loaded
    stmt = select(PayrollRun).options(
        selectinload(PayrollRun.period),
        selectinload(PayrollRun.employees).selectinload(PayrollRunEmployee.person)
    ).where(PayrollRun.id == payroll_run_id)
    
    result = await session.execute(stmt)
    payroll_run = result.scalar_one_or_none()
    
    if not payroll_run:
        raise ValueError(f"PayrollRun {payroll_run_id} not found")
    
    # Create bank transfers directory
    transfers_dir = Path("data/uploads/bank_transfers")
    transfers_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    period_end = payroll_run.period.end_date
    filename = f"bank_transfer_{payroll_run_id}_{period_end}.{format}"
    filepath = transfers_dir / filename
    
    # Prepare data
    rows = []
    for emp in payroll_run.employees:
        person = emp.person
        bank_id = person.account_number or person.iban or ""
        
        rows.append({
            "Name": person.full_name,
            "National_ID": person.identity_number or "",
            "Bank_ID": bank_id,
            "Salary": emp.net,
        })
    
    # Generate file
    if format == "csv":
        await _generate_csv(filepath, rows)
    elif format == "excel":
        await _generate_excel(filepath, rows)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'excel'")
    
    return filepath


async def _generate_csv(
    filepath: Path,
    rows: list,
) -> None:
    """Generate CSV file."""
    import csv
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        if not rows:
            return
        
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


async def _generate_excel(
    filepath: Path,
    rows: list,
) -> None:
    """Generate Excel file."""
    try:
        from openpyxl import Workbook
    except ImportError:
        raise ImportError("openpyxl is required for Excel generation. Install with: uv add openpyxl")
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Bank Transfer"
    
    if not rows:
        wb.save(filepath)
        return
    
    # Write headers
    headers = list(rows[0].keys())
    ws.append(headers)
    
    # Write data
    for row in rows:
        ws.append([row[h] for h in headers])
    
    wb.save(filepath)


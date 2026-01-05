"""
Report Generation Service

Generates attendance and payroll reports with PDF/Excel export.
"""

from datetime import date
from pathlib import Path
from typing import Optional, Dict, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from server.db.models import (
    Attendance, PayrollRun, PayrollRunEmployee, Person, Location, PayrollPeriod
)


async def generate_attendance_report(
    start_date: date,
    end_date: date,
    session: AsyncSession,
    location_id: Optional[UUID] = None,
) -> Dict:
    """
    Generate attendance report.
    
    Queries Attendance records with filters and aggregates by person:
    - total days
    - total hours
    - present/absent counts
    
    Returns report data dictionary.
    """
    # Build query
    stmt = select(
        Attendance.person_id,
        Person.full_name,
        func.count(Attendance.id).label("total_days"),
        func.sum(
            func.extract("epoch", Attendance.check_out - Attendance.check_in) / 3600
        ).label("total_hours"),
        func.sum(
            func.case((Attendance.status == "present", 1), else_=0)
        ).label("present_days"),
        func.sum(
            func.case((Attendance.status == "absent", 1), else_=0)
        ).label("absent_days"),
    ).join(
        Person, Attendance.person_id == Person.id
    ).where(
        and_(
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date,
        )
    ).group_by(Attendance.person_id, Person.full_name)
    
    if location_id:
        stmt = stmt.where(Attendance.location_id == location_id)
    
    result = await session.execute(stmt)
    rows = result.all()
    
    # Format report data
    report_data = {
        "start_date": start_date,
        "end_date": end_date,
        "location_id": location_id,
        "employees": [],
    }
    
    for row in rows:
        report_data["employees"].append({
            "person_id": row.person_id,
            "full_name": row.full_name,
            "total_days": row.total_days or 0,
            "total_hours": float(row.total_hours or 0),
            "present_days": row.present_days or 0,
            "absent_days": row.absent_days or 0,
        })
    
    return report_data


async def generate_payroll_report(
    session: AsyncSession,
    payroll_run_id: Optional[UUID] = None,
    period_id: Optional[UUID] = None,
) -> Dict:
    """
    Generate payroll report.
    
    Gets PayrollRun with all employees and aggregates totals by location, payroll group.
    Returns report data dictionary.
    """
    if payroll_run_id:
        stmt = select(PayrollRun).options(
            selectinload(PayrollRun.period),
            selectinload(PayrollRun.employees).selectinload(PayrollRunEmployee.person),
            selectinload(PayrollRun.location),
        ).where(PayrollRun.id == payroll_run_id)
    elif period_id:
        stmt = select(PayrollRun).options(
            selectinload(PayrollRun.period),
            selectinload(PayrollRun.employees).selectinload(PayrollRunEmployee.person),
            selectinload(PayrollRun.location),
        ).where(PayrollRun.payroll_period_id == period_id)
    else:
        raise ValueError("Either payroll_run_id or period_id must be provided")
    
    result = await session.execute(stmt)
    payroll_runs = result.scalars().all()
    
    if not payroll_runs:
        raise ValueError("No payroll runs found")
    
    # Aggregate data
    report_data = {
        "payroll_runs": [],
        "totals": {
            "total_employees": 0,
            "total_gross": 0.0,
            "total_deductions": 0.0,
            "total_net": 0.0,
        },
    }
    
    for run in payroll_runs:
        run_data = {
            "run_id": str(run.id),
            "period": {
                "start": run.period.start_date,
                "end": run.period.end_date,
            },
            "location": run.location.name if run.location else "All Locations",
            "status": run.status.value,
            "employees": [],
            "totals": {
                "count": len(run.employees),
                "gross": sum(emp.gross for emp in run.employees),
                "deductions": sum(emp.deductions for emp in run.employees),
                "net": sum(emp.net for emp in run.employees),
            },
        }
        
        for emp in run.employees:
            run_data["employees"].append({
                "person_id": emp.person_id,
                "full_name": emp.person.full_name,
                "gross": emp.gross,
                "deductions": emp.deductions,
                "net": emp.net,
                "total_hours": emp.total_hours,
                "total_days": emp.total_days,
            })
        
        report_data["payroll_runs"].append(run_data)
        
        # Update overall totals
        report_data["totals"]["total_employees"] += run_data["totals"]["count"]
        report_data["totals"]["total_gross"] += run_data["totals"]["gross"]
        report_data["totals"]["total_deductions"] += run_data["totals"]["deductions"]
        report_data["totals"]["total_net"] += run_data["totals"]["net"]
    
    return report_data


async def export_to_pdf(
    report_data: Dict,
    output_path: Path,
    template: str = "default",
) -> None:
    """
    Export report to PDF using reportlab.
    
    Applies template formatting and saves to output_path.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:
        raise ImportError("reportlab is required for PDF export. Install with: uv add reportlab")
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    story.append(Paragraph("Payroll Report", styles["Title"]))
    story.append(Spacer(1, 12))
    
    # Report data table
    if "employees" in report_data:
        # Attendance report format
        data = [["Employee", "Total Days", "Total Hours", "Present", "Absent"]]
        for emp in report_data["employees"]:
            data.append([
                emp["full_name"],
                str(emp["total_days"]),
                f"{emp['total_hours']:.2f}",
                str(emp["present_days"]),
                str(emp["absent_days"]),
            ])
    else:
        # Payroll report format
        data = [["Employee", "Gross", "Deductions", "Net"]]
        for run in report_data.get("payroll_runs", []):
            for emp in run["employees"]:
                data.append([
                    emp["full_name"],
                    f"{emp['gross']:.2f}",
                    f"{emp['deductions']:.2f}",
                    f"{emp['net']:.2f}",
                ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    
    doc.build(story)


async def export_to_excel(
    report_data: Dict,
    output_path: Path,
) -> None:
    """
    Export report to Excel using openpyxl.
    
    Creates worksheets for different sections and saves to output_path.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        raise ImportError("openpyxl is required for Excel export. Install with: uv add openpyxl")
    
    wb = Workbook()
    ws = wb.active
    
    if "employees" in report_data:
        # Attendance report
        ws.title = "Attendance Report"
        headers = ["Employee", "Total Days", "Total Hours", "Present", "Absent"]
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        for emp in report_data["employees"]:
            ws.append([
                emp["full_name"],
                emp["total_days"],
                emp["total_hours"],
                emp["present_days"],
                emp["absent_days"],
            ])
    else:
        # Payroll report
        ws.title = "Payroll Report"
        headers = ["Employee", "Gross", "Deductions", "Net", "Hours", "Days"]
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        for run in report_data.get("payroll_runs", []):
            for emp in run["employees"]:
                ws.append([
                    emp["full_name"],
                    emp["gross"],
                    emp["deductions"],
                    emp["net"],
                    emp["total_hours"],
                    emp["total_days"],
                ])
    
    wb.save(output_path)


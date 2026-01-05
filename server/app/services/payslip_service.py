"""
Payslip Generation Service

Generates payslips in Arabic and English PDF format.
"""

from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.db.models import (
    PayrollRunEmployee, PayrollRunLine, Payslip, Person, PayrollRun
)
from server.config import config


async def get_payslip_data(
    payroll_run_employee_id: UUID,
    session: AsyncSession,
) -> Dict:
    """
    Get payroll data formatted for payslip PDF.
    
    Returns structured data dictionary with all payslip information.
    """
    stmt = select(PayrollRunEmployee).options(
        selectinload(PayrollRunEmployee.payroll_run).selectinload(PayrollRun.period),
        selectinload(PayrollRunEmployee.lines),
        selectinload(PayrollRunEmployee.person),
    ).where(PayrollRunEmployee.id == payroll_run_employee_id)
    
    result = await session.execute(stmt)
    payroll_employee = result.scalar_one_or_none()
    
    if not payroll_employee:
        raise ValueError(f"PayrollRunEmployee {payroll_run_employee_id} not found")
    
    # Format data for payslip
    earnings = []
    deductions = []
    
    for line in payroll_employee.lines:
        line_data = {
            "name": line.component_name_snapshot or "Unknown",
            "amount": line.amount,
        }
        
        if line.kind.value == "earning":
            earnings.append(line_data)
        else:
            deductions.append(line_data)
    
    return {
        "person": {
            "id": payroll_employee.person_id,
            "name": payroll_employee.person.full_name,
            "identity_number": payroll_employee.person.identity_number,
            "bank_account": payroll_employee.person.account_number or payroll_employee.person.iban,
        },
        "period": {
            "start": payroll_employee.payroll_run.period.start_date,
            "end": payroll_employee.payroll_run.period.end_date,
        },
        "summary": {
            "base_salary": payroll_employee.base_salary_amount or 0,
            "gross": payroll_employee.gross,
            "deductions": payroll_employee.deductions,
            "net": payroll_employee.net,
            "total_hours": payroll_employee.total_hours,
            "total_days": payroll_employee.total_days,
        },
        "earnings": earnings,
        "deductions": deductions,
        "generated_at": datetime.utcnow(),
    }


async def generate_payslip(
    payroll_run_employee_id: UUID,
    session: AsyncSession,
    language: str = "ar",
) -> Payslip:
    """
    Generate payslip PDF in Arabic or English.
    
    Uses reportlab to generate PDF.
    Saves to data/uploads/payslips/
    Creates Payslip record with PDF URLs.
    """
    # Get payslip data
    payslip_data = await get_payslip_data(payroll_run_employee_id, session)
    
    # Generate PDF
    pdf_path = await _generate_pdf(payslip_data, language)
    
    # Create Payslip record
    payslip = Payslip(
        payroll_run_employee_id=payroll_run_employee_id,
        person_id=payslip_data["person"]["id"],
        generated_at=datetime.utcnow(),
        language=language,
    )
    
    # Set PDF URL based on language
    if language == "ar":
        payslip.pdf_url_ar = str(pdf_path)
    else:
        payslip.pdf_url_en = str(pdf_path)
    
    session.add(payslip)
    await session.flush()
    await session.refresh(payslip)
    
    return payslip


async def _generate_pdf(
    payslip_data: Dict,
    language: str,
) -> Path:
    """
    Generate PDF file using reportlab.
    
    Returns Path to generated PDF file.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except ImportError:
        raise ImportError("reportlab is required for payslip generation. Install with: uv add reportlab")
    
    # Create payslips directory
    payslips_dir = Path("data/uploads/payslips")
    payslips_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    person_id = payslip_data["person"]["id"]
    period_end = payslip_data["period"]["end"]
    filename = f"payslip_{person_id}_{period_end}_{language}.pdf"
    filepath = payslips_dir / filename
    
    # Create PDF
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )
    
    # Build content
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_text = "Payslip" if language == "en" else "كشف الراتب"
    story.append(Paragraph(title_text, styles["Title"]))
    story.append(Spacer(1, 12))
    
    # Employee info
    emp_name = payslip_data["person"]["name"]
    emp_id = payslip_data["person"]["id"]
    story.append(Paragraph(f"<b>Employee:</b> {emp_name} ({emp_id})", styles["Normal"]))
    story.append(Spacer(1, 6))
    
    # Period
    period_start = payslip_data["period"]["start"]
    period_end = payslip_data["period"]["end"]
    story.append(Paragraph(f"<b>Period:</b> {period_start} to {period_end}", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    # Earnings table
    earnings_data = [["Description", "Amount"]]
    for earning in payslip_data["earnings"]:
        earnings_data.append([earning["name"], f"{earning['amount']:.2f}"])
    
    earnings_table = Table(earnings_data)
    earnings_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(Paragraph("<b>Earnings</b>", styles["Heading2"]))
    story.append(earnings_table)
    story.append(Spacer(1, 12))
    
    # Deductions table
    deductions_data = [["Description", "Amount"]]
    for deduction in payslip_data["deductions"]:
        deductions_data.append([deduction["name"], f"{deduction['amount']:.2f}"])
    
    deductions_table = Table(deductions_data)
    deductions_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(Paragraph("<b>Deductions</b>", styles["Heading2"]))
    story.append(deductions_table)
    story.append(Spacer(1, 12))
    
    # Summary
    summary = payslip_data["summary"]
    summary_data = [
        ["Gross Salary", f"{summary['gross']:.2f}"],
        ["Total Deductions", f"{summary['deductions']:.2f}"],
        ["Net Salary", f"<b>{summary['net']:.2f}</b>"],
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 2), (1, 2), "Helvetica-Bold"),
    ]))
    story.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
    story.append(summary_table)
    
    # Build PDF
    doc.build(story)
    
    return filepath


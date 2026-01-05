"""
Payroll Calculation Service

Calculates payroll for employees based on:
- Attendance hours (present + approved overtime)
- Salary components (base salary, allowances, deductions)
- Overtime pay
"""

from datetime import date
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from server.db.models import (
    Person, Attendance, AttendanceStatus, Assignment,
    PayrollPeriod, PayrollRun, PayrollRunEmployee, PayrollRunLine,
    PayrollRunStatus, SalaryComponent, EmployeeComponent,
    ComponentKind, ComponentType, AmountType,
    OvertimeRequest, OvertimeRequestStatus,
)


async def calculate_payroll(
    payroll_period_id: UUID,
    location_id: Optional[UUID],
    session: AsyncSession,
) -> PayrollRun:
    """
    Calculate payroll for a payroll period and location.
    
    For each person:
    1. Sum attendance hours (present + approved overtime)
    2. Apply base salary component
    3. Apply allowances, incentives
    4. Apply deductions
    5. Calculate overtime pay
    6. Store in payroll_run_employee + payroll_run_line
    """
    # Get payroll period
    period_stmt = select(PayrollPeriod).where(PayrollPeriod.id == payroll_period_id)
    period_result = await session.execute(period_stmt)
    period = period_result.scalar_one_or_none()
    
    if not period:
        raise ValueError(f"Payroll period {payroll_period_id} not found")
    
    # Create payroll run
    payroll_run = PayrollRun(
        payroll_period_id=payroll_period_id,
        location_id=location_id,
        status=PayrollRunStatus.DRAFT,
    )
    session.add(payroll_run)
    await session.flush()
    
    # Get all active persons (optionally filtered by location via assignments)
    person_stmt = select(Person).where(Person.status == "active")
    person_result = await session.execute(person_stmt)
    persons = person_result.scalars().all()
    
    # Get all salary components
    component_stmt = select(SalaryComponent).where(SalaryComponent.active == True)
    component_result = await session.execute(component_stmt)
    components = {c.id: c for c in component_result.scalars().all()}
    
    for person in persons:
        # Filter by location if specified (via assignments)
        if location_id:
            assignment_stmt = select(Assignment).where(
                and_(
                    Assignment.person_id == person.id,
                    Assignment.location_id == location_id,
                    Assignment.is_active == True,
                )
            )
            assignment_result = await session.execute(assignment_stmt)
            if not assignment_result.scalar_one_or_none():
                continue  # Skip person if not assigned to this location
        
        # Calculate attendance hours
        attendance_stmt = select(
            func.sum(
                func.extract('epoch', Attendance.check_out - Attendance.check_in) / 3600
            ).label('total_hours'),
            func.count(Attendance.id).label('total_days'),
        ).where(
            and_(
                Attendance.person_id == person.id,
                Attendance.attendance_date >= period.start_date,
                Attendance.attendance_date <= period.end_date,
                Attendance.status == AttendanceStatus.PRESENT,
                Attendance.check_in.isnot(None),
                Attendance.check_out.isnot(None),
            )
        )
        attendance_result = await session.execute(attendance_stmt)
        attendance_row = attendance_result.first()
        
        total_hours = float(attendance_row.total_hours or 0)
        total_days = int(attendance_row.total_days or 0)
        
        # Add approved overtime hours
        overtime_stmt = select(func.sum(OvertimeRequest.hours)).where(
            and_(
                OvertimeRequest.person_id == person.id,
                OvertimeRequest.overtime_date >= period.start_date,
                OvertimeRequest.overtime_date <= period.end_date,
                OvertimeRequest.status == OvertimeRequestStatus.APPROVED,
            )
        )
        overtime_result = await session.execute(overtime_stmt)
        overtime_hours = float(overtime_result.scalar() or 0)
        total_hours += overtime_hours
        
        # Get employee-specific component overrides
        emp_component_stmt = select(EmployeeComponent).where(
            EmployeeComponent.person_id == person.id
        )
        emp_component_result = await session.execute(emp_component_stmt)
        emp_components = {
            ec.component_id: ec.value_override
            for ec in emp_component_result.scalars().all()
        }
        
        # Calculate payroll
        gross = 0.0
        deductions = 0.0
        
        # Create payroll run employee record
        payroll_employee = PayrollRunEmployee(
            payroll_run_id=payroll_run.id,
            person_id=person.id,
            total_hours=total_hours,
            total_days=total_days,
        )
        session.add(payroll_employee)
        await session.flush()
        
        # Process each component
        for component_id, component in components.items():
            # Get amount (use override if available)
            amount = emp_components.get(component_id, component.amount)
            
            # Calculate component value based on amount_type
            if component.amount_type == AmountType.FIXED:
                value = amount
            elif component.amount_type == AmountType.PER_DAY:
                value = amount * total_days
            elif component.amount_type == AmountType.PER_HOUR:
                value = amount * total_hours
            elif component.amount_type == AmountType.PERCENTAGE:
                # Percentage of base salary (find base salary first)
                base_salary = 0
                for cid, c in components.items():
                    if c.type == ComponentType.BASE_SALARY:
                        base_salary = emp_components.get(cid, c.amount)
                        break
                value = (amount / 100) * base_salary
            else:
                value = 0
            
            # Handle overtime pay separately
            if component.type == ComponentType.OVERTIME:
                # Overtime pay = overtime hours * rate
                value = overtime_hours * amount
            
            # Add to gross or deductions
            if component.kind == ComponentKind.EARNING:
                gross += value
            else:
                deductions += value
            
            # Store line item
            line = PayrollRunLine(
                payroll_run_employee_id=payroll_employee.id,
                component_id=component_id,
                component_name_snapshot=component.name,
                kind=component.kind,
                amount=value,
            )
            session.add(line)
            
            # Store base salary amount for reference
            if component.type == ComponentType.BASE_SALARY:
                payroll_employee.base_salary_amount = value
        
        # Calculate net
        net = gross - deductions
        
        # Update payroll employee totals
        payroll_employee.gross = gross
        payroll_employee.deductions = deductions
        payroll_employee.net = net
        session.add(payroll_employee)
    
    await session.flush()
    await session.refresh(payroll_run)
    return payroll_run


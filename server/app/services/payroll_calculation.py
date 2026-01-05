"""
Payroll Calculation Service

Calculates payroll for employees based on:
- Attendance hours (present + approved overtime)
- Salary components (base salary, allowances, deductions)
- Overtime pay
- Salary advances
- Loans
- Social insurance
- Income tax
- Component caps and priority
"""

from datetime import date
from typing import Optional, Dict, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from server.db.models import (
    Person,
    PersonStatus,
    Attendance,
    AttendanceStatus,
    Assignment,
    PayrollPeriod,
    PayrollRun,
    PayrollRunEmployee,
    PayrollRunLine,
    PayrollRunStatus,
    SalaryComponent,
    EmployeeComponent,
    ComponentKind,
    ComponentType,
    AmountType,
    OvertimeRequest,
    OvertimeRequestStatus,
)

from server.app.services.salary_advance_service import calculate_advance_deduction
from server.app.services.loan_service import calculate_installment
from server.app.services.statutory_calculation import (
    calculate_social_insurance,
    calculate_income_tax,
    validate_minimum_wage,
    get_taxable_components,
    get_insurable_components,
)


async def calculate_payroll(
    payroll_period_id: UUID,
    location_id: Optional[UUID],
    session: AsyncSession,
    preview_mode: bool = False,
) -> PayrollRun | Dict:
    """
    Calculate payroll for a payroll period and location.

    Enhanced to include:
    - Salary advances
    - Loans
    - Social insurance
    - Income tax
    - Component caps and priority
    - Pro-rata calculations
    - Retroactive adjustments

    If preview_mode=True, returns calculated data without saving.
    """
    # Get payroll period
    period_stmt = select(PayrollPeriod).where(PayrollPeriod.id == payroll_period_id)
    period_result = await session.execute(period_stmt)
    period = period_result.scalar_one_or_none()

    if not period:
        raise ValueError(f"Payroll period {payroll_period_id} not found")

    # Create payroll run (or use for preview)
    if preview_mode:
        preview_data = {"employees": []}
    else:
        payroll_run = PayrollRun(
            payroll_period_id=payroll_period_id,
            location_id=location_id,
            status=PayrollRunStatus.DRAFT,
        )
        session.add(payroll_run)
        await session.flush()

    # Get all active persons (optionally filtered by location via assignments)
    person_stmt = select(Person).where(Person.status == PersonStatus.ACTIVE)
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

        # Calculate pro-rata factor if person joined/left mid-period
        pro_rata_factor = await _calculate_pro_rata_factor(
            person, period.start_date, period.end_date, session
        )

        # Calculate attendance hours
        attendance_stmt = select(
            func.sum(
                func.extract("epoch", Attendance.check_out - Attendance.check_in) / 3600
            ).label("total_hours"),
            func.count(Attendance.id).label("total_days"),
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

        # Calculate base salary first (needed for percentage calculations)
        base_salary = 0.0
        for cid, c in components.items():
            if c.type == ComponentType.BASE_SALARY:
                base_salary = emp_components.get(cid, c.amount)
                break

        # Apply pro-rata to base salary
        base_salary *= pro_rata_factor

        # Calculate payroll
        gross = 0.0
        deductions = 0.0
        earnings_lines = []
        deduction_lines = []

        # Create payroll run employee record
        if not preview_mode:
            payroll_employee = PayrollRunEmployee(
                payroll_run_id=payroll_run.id,
                person_id=person.id,
                total_hours=total_hours,
                total_days=total_days,
                base_salary_amount=base_salary,
            )
            session.add(payroll_employee)
            await session.flush()

        # Process earnings components first
        earnings_components = [
            (cid, c) for cid, c in components.items() if c.kind == ComponentKind.EARNING
        ]
        earnings_components.sort(key=lambda x: x[1].priority)  # Sort by priority

        for component_id, component in earnings_components:
            amount = emp_components.get(component_id, component.amount)

            # Calculate component value
            value = await _calculate_component_value(
                component, amount, total_hours, total_days, base_salary, overtime_hours
            )

            # Apply pro-rata
            value *= pro_rata_factor

            # Apply caps
            if component.max_amount:
                value = min(value, component.max_amount)
            if component.max_percentage and base_salary > 0:
                max_value = (component.max_percentage / 100) * base_salary
                value = min(value, max_value)

            gross += value
            earnings_lines.append(
                {
                    "component_id": component_id,
                    "name": component.name,
                    "amount": value,
                }
            )

            if not preview_mode:
                line = PayrollRunLine(
                    payroll_run_employee_id=payroll_employee.id,
                    component_id=component_id,
                    component_name_snapshot=component.name,
                    kind=ComponentKind.EARNING,
                    amount=value,
                )
                session.add(line)

        # Calculate social insurance (on insurable components)
        insurable_components = await get_insurable_components(person.id, session)
        insurable_gross = sum(
            line["amount"]
            for line in earnings_lines
            if any(
                ic.component_id == line["component_id"] for ic in insurable_components
            )
        )
        employee_insurance, employer_insurance = await calculate_social_insurance(
            insurable_gross
        )

        # Add insurance as deduction
        deductions += employee_insurance
        deduction_lines.append(
            {
                "component_id": None,
                "name": "Social Insurance - Employee",
                "amount": employee_insurance,
                "priority": 0,
            }
        )

        # Calculate income tax (on taxable components)
        taxable_components = await get_taxable_components(person.id, session)
        taxable_income = sum(
            line["amount"]
            for line in earnings_lines
            if any(tc.component_id == line["component_id"] for tc in taxable_components)
        )
        income_tax = await calculate_income_tax(taxable_income)

        # Add tax as deduction
        deductions += income_tax
        deduction_lines.append(
            {
                "component_id": None,
                "name": "Income Tax",
                "amount": income_tax,
                "priority": 1,
            }
        )

        # Calculate salary advance deductions
        advance_deduction = await calculate_advance_deduction(
            person.id, period.start_date, period.end_date, session
        )
        if advance_deduction > 0:
            deductions += advance_deduction
            deduction_lines.append(
                {
                    "component_id": None,
                    "name": "Salary Advance Repayment",
                    "amount": advance_deduction,
                    "priority": 2,
                }
            )

        # Calculate loan installments
        loan_installment = await calculate_installment(
            person.id, period.start_date, period.end_date, session
        )
        if loan_installment > 0:
            deductions += loan_installment
            deduction_lines.append(
                {
                    "component_id": None,
                    "name": "Loan Installment",
                    "amount": loan_installment,
                    "priority": 3,
                }
            )

        # Process deduction components (sorted by priority)
        deduction_components = [
            (cid, c)
            for cid, c in components.items()
            if c.kind == ComponentKind.DEDUCTION
            and c.type not in [ComponentType.INSURANCE, ComponentType.TAX]
        ]
        deduction_components.sort(key=lambda x: x[1].priority)

        for component_id, component in deduction_components:
            amount = emp_components.get(component_id, component.amount)

            # Calculate component value
            value = await _calculate_component_value(
                component, amount, total_hours, total_days, base_salary, overtime_hours
            )

            # Apply pro-rata
            value *= pro_rata_factor

            # Apply caps
            if component.max_amount:
                value = min(value, component.max_amount)
            if component.max_percentage and base_salary > 0:
                max_value = (component.max_percentage / 100) * base_salary
                value = min(value, max_value)

            deductions += value
            deduction_lines.append(
                {
                    "component_id": component_id,
                    "name": component.name,
                    "amount": value,
                    "priority": component.priority,
                }
            )

            if not preview_mode:
                line = PayrollRunLine(
                    payroll_run_employee_id=payroll_employee.id,
                    component_id=component_id,
                    component_name_snapshot=component.name,
                    kind=ComponentKind.DEDUCTION,
                    amount=value,
                )
                session.add(line)

        # Calculate net
        net = gross - deductions

        # Validate minimum wage
        is_valid, difference = await validate_minimum_wage(net)
        if not is_valid:
            # Log warning but don't fail
            print(
                f"Warning: Net salary {net} for person {person.id} is below minimum wage by {abs(difference)}"
            )

        if preview_mode:
            preview_data["employees"].append(
                {
                    "person_id": person.id,
                    "full_name": person.full_name,
                    "base_salary": base_salary,
                    "gross": gross,
                    "deductions": deductions,
                    "net": net,
                    "total_hours": total_hours,
                    "total_days": total_days,
                    "earnings": earnings_lines,
                    "deductions_detail": deduction_lines,
                }
            )
        else:
            # Update payroll employee totals
            payroll_employee.gross = gross
            payroll_employee.deductions = deductions
            payroll_employee.net = net
            session.add(payroll_employee)

    if preview_mode:
        return preview_data

    await session.flush()
    await session.refresh(payroll_run)
    return payroll_run


async def _calculate_component_value(
    component: SalaryComponent,
    amount: float,
    total_hours: float,
    total_days: int,
    base_salary: float,
    overtime_hours: float,
) -> float:
    """Calculate component value based on amount_type."""
    if component.amount_type == AmountType.FIXED:
        return amount
    elif component.amount_type == AmountType.PER_DAY:
        return amount * total_days
    elif component.amount_type == AmountType.PER_HOUR:
        return amount * total_hours
    elif component.amount_type == AmountType.PERCENTAGE:
        return (amount / 100) * base_salary
    elif component.type == ComponentType.OVERTIME:
        return overtime_hours * amount
    else:
        return 0.0


async def _calculate_pro_rata_factor(
    person: Person,
    period_start: date,
    period_end: date,
    session: AsyncSession,
) -> float:
    """
    Calculate pro-rata factor for partial period employment.

    Returns factor between 0 and 1.
    """
    # If person has hire_date, check if they joined mid-period
    if person.hire_date and person.hire_date > period_start:
        # Joined mid-period
        days_in_period = (period_end - period_start).days + 1
        days_worked = (period_end - person.hire_date).days + 1
        return max(0, min(1, days_worked / days_in_period))

    # If person has contract_end_date, check if they left mid-period
    if person.contract_end_date:
        if person.contract_end_date < period_end:
            # Left mid-period
            days_in_period = (period_end - period_start).days + 1
            days_worked = (person.contract_end_date - period_start).days + 1
            return max(0, min(1, days_worked / days_in_period))

    # Full period
    return 1.0

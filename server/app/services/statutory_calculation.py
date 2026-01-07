"""
Statutory Calculation Service

Handles social insurance, income tax, and minimum wage calculations.
"""

from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from server.db.models import (
    Person, EmployeeComponent, SalaryComponent, ComponentType
)


async def calculate_social_insurance(
    gross_salary: float,
    employee_rate: float = 0.11,  # 11% default
    employer_rate: float = 0.26,  # 26% default
) -> Tuple[float, float]:
    """
    Calculate social insurance contributions.
    
    Returns:
        Tuple of (employee_amount, employer_amount)
    """
    employee_amount = gross_salary * employee_rate
    employer_amount = gross_salary * employer_rate
    
    return (employee_amount, employer_amount)


async def calculate_income_tax(
    taxable_income: float,
    tax_brackets: Optional[List[dict]] = None,
) -> float:
    """
    Calculate income tax using progressive tax brackets.
    
    tax_brackets format: [
        {"min": 0, "max": 15000, "rate": 0.0},
        {"min": 15000, "max": 30000, "rate": 0.10},
        {"min": 30000, "max": 45000, "rate": 0.15},
        {"min": 45000, "max": None, "rate": 0.20},
    ]
    
    If tax_brackets not provided, uses default Egyptian tax brackets.
    """
    if tax_brackets is None:
        # Default Egyptian tax brackets (simplified)
        tax_brackets = [
            {"min": 0, "max": 15000, "rate": 0.0},
            {"min": 15000, "max": 30000, "rate": 0.10},
            {"min": 30000, "max": 45000, "rate": 0.15},
            {"min": 45000, "max": None, "rate": 0.20},
        ]
    
    total_tax = 0.0
    remaining_income = taxable_income
    
    for bracket in tax_brackets:
        if remaining_income <= 0:
            break
        
        min_income = bracket["min"]
        max_income = bracket["max"]
        rate = bracket["rate"]
        
        if max_income is None:
            # Top bracket - apply to all remaining income
            taxable_in_bracket = remaining_income - min_income
            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * rate
            break
        else:
            # Calculate tax for this bracket
            bracket_range = max_income - min_income
            income_in_bracket = min(remaining_income, bracket_range)
            
            if income_in_bracket > 0:
                total_tax += income_in_bracket * rate
                remaining_income -= income_in_bracket
    
    return total_tax


async def validate_minimum_wage(
    net_salary: float,
    minimum_wage_config: Optional[float] = None,
) -> Tuple[bool, float]:
    """
    Validate if net salary meets minimum wage requirements.
    
    Returns:
        Tuple of (is_valid, difference)
        difference is positive if salary is above minimum, negative if below
    """
    if minimum_wage_config is None:
        # Default Egyptian minimum wage (2024) - adjust as needed
        minimum_wage_config = 6000.0  # EGP per month
    
    is_valid = net_salary >= minimum_wage_config
    difference = net_salary - minimum_wage_config
    
    return (is_valid, difference)


async def get_taxable_components(
    person_id: str,
    session: AsyncSession,
) -> List[EmployeeComponent]:
    """
    Get all taxable components for a person.
    
    Returns list of EmployeeComponent where component.taxable == True.
    """
    stmt = select(EmployeeComponent, SalaryComponent).join(
        SalaryComponent, EmployeeComponent.component_id == SalaryComponent.id
    ).where(
        and_(
            EmployeeComponent.person_id == person_id,
            SalaryComponent.taxable == True,
            SalaryComponent.active == True,
        )
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [ec for ec, sc in rows]


async def get_insurable_components(
    person_id: str,
    session: AsyncSession,
) -> List[EmployeeComponent]:
    """
    Get all insurable components for a person.
    
    Returns list of EmployeeComponent where component.insurable == True.
    """
    stmt = select(EmployeeComponent, SalaryComponent).join(
        SalaryComponent, EmployeeComponent.component_id == SalaryComponent.id
    ).where(
        and_(
            EmployeeComponent.person_id == person_id,
            SalaryComponent.insurable == True,
            SalaryComponent.active == True,
        )
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [ec for ec, sc in rows]




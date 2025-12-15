"""Employee ID generator - generates unique 5-character alphanumeric codes."""
import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.employee import Employee


def generate_employee_id() -> str:
    """Generate a random 5-character alphanumeric ID."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(5))


async def get_unique_employee_id(db: AsyncSession, max_attempts: int = 10) -> str:
    """Generate a unique employee ID that doesn't exist in the database."""
    for _ in range(max_attempts):
        employee_id = generate_employee_id()
        
        # Check if ID already exists
        result = await db.execute(
            select(Employee).where(Employee.employee_id == employee_id)
        )
        if result.scalar_one_or_none() is None:
            return employee_id
    
    raise ValueError("Failed to generate unique employee ID after multiple attempts")

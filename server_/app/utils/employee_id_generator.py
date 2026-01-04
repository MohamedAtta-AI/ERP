"""Employee ID generator - generates unique numeric codes."""
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from ..models.employee import Employee


def generate_employee_id() -> str:
    """Generate a random 6-digit numeric ID."""
    # Generate 6-digit number (100000 to 999999)
    return str(random.randint(100000, 999999))


async def get_unique_employee_id(db: AsyncSession, max_attempts: int = 10) -> str:
    """Generate a unique employee ID that doesn't exist in the database."""
    for _ in range(max_attempts):
        employee_id = generate_employee_id()
        
        # Check if ID already exists
        result = await db.exec(select(Employee).where(Employee.employee_id == employee_id))
        if result.first() is None:
            return employee_id
    
    raise ValueError("Failed to generate unique employee ID after multiple attempts")

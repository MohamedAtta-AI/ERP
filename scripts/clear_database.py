"""
Clear all data from the database tables.

This script deletes all records from:
- attendance
- face_embeddings  
- employees

Usage:
    python scripts/clear_database.py
"""

import asyncio
import asyncpg
from pathlib import Path
import sys

# Add parent directory to path to import settings
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "server"))

from app.settings import settings


async def clear_database():
    """Clear all data from all tables."""
    # Parse database URL to get connection params
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    # Connect to database
    conn = await asyncpg.connect(db_url)
    
    try:
        print("Clearing database...")
        
        # Disable foreign key checks temporarily (PostgreSQL doesn't have this, but we'll delete in order)
        # Delete in order: attendance -> face_embeddings -> employees
        # (Actually, CASCADE will handle it, but let's be explicit)
        
        # Clear attendance records
        result = await conn.execute("DELETE FROM attendance")
        print("Deleted all attendance records")
        
        # Clear face embeddings
        result = await conn.execute("DELETE FROM face_embeddings")
        print("Deleted all face embeddings")
        
        # Clear employees (this will cascade delete related records if any remain)
        result = await conn.execute("DELETE FROM employees")
        print("Deleted all employees")
        
        # Reset sequences (optional, but good practice)
        await conn.execute("ALTER SEQUENCE employees_id_seq RESTART WITH 1")
        await conn.execute("ALTER SEQUENCE face_embeddings_id_seq RESTART WITH 1")
        await conn.execute("ALTER SEQUENCE attendance_id_seq RESTART WITH 1")
        print("Reset auto-increment sequences")
        
        print("\nDatabase cleared successfully!")
        
    except Exception as e:
        print(f"Error clearing database: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(clear_database())


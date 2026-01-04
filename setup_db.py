"""Setup database tables."""
import asyncio
from sqlalchemy import text
from server.app.database import engine, init_db


async def setup_database():
    """Create database tables and enable pgvector."""
    try:
        await init_db()
        print("SUCCESS: Database setup complete!")
        print("   - pgvector extension enabled")
        print("   - All tables created")
    except Exception as e:
        print(f"ERROR: Database setup failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_database())
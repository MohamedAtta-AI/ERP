"""Setup database tables."""
import asyncio
from sqlalchemy import text
from server.app.database import engine, Base
from server.app.models import Employee, FaceEmbedding, Attendance


async def setup_database():
    """Create database tables and enable pgvector."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
    
    print("SUCCESS: Database setup complete!")
    print("   - pgvector extension enabled")
    print("   - All tables created")


if __name__ == "__main__":
    asyncio.run(setup_database())
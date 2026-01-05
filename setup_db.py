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
    # Check if we're already in an event loop
    try:
        loop = asyncio.get_running_loop()
        # If we get here, we're in an event loop - can't use asyncio.run()
        # This shouldn't happen when run as a script, but handle it gracefully
        import sys
        print("ERROR: Cannot run setup_db.py from within an async context")
        print("   Run this script directly: python setup_db.py")
        sys.exit(1)
    except RuntimeError:
        # No event loop running - safe to use asyncio.run()
    asyncio.run(setup_database())
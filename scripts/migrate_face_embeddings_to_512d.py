"""
Migrate face embeddings from 128-dimensional (SFace) to 512-dimensional (FaceNet512).

This script:
1. Drops the old face_embeddings table
2. Recreates it with 512-dimensional vectors
3. Note: Existing embeddings will be lost - re-enrollment required

Usage:
    python scripts/migrate_face_embeddings_to_512d.py
"""

import asyncio
import asyncpg
from pathlib import Path
import sys

# Add parent directory to path to import settings
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "server"))

from app.settings import settings


async def migrate_embeddings():
    """Migrate face_embeddings table from 128d to 512d vectors."""
    # Parse database URL to get connection params
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    # Connect to database
    conn = await asyncpg.connect(db_url)
    
    try:
        print("Migrating face_embeddings table from 128d to 512d...")
        print("WARNING: This will delete all existing embeddings!")
        print("Employees will need to re-enroll their faces after migration.")
        
        # Check if table exists and has data
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'face_embeddings'
            );
        """)
        
        if table_exists:
            count = await conn.fetchval("SELECT COUNT(*) FROM face_embeddings")
            print(f"Found {count} existing embeddings (will be deleted)")
        
        # Drop the old table (CASCADE will handle foreign key constraints)
        await conn.execute("DROP TABLE IF EXISTS face_embeddings CASCADE")
        print("Dropped old face_embeddings table")
        
        # Recreate table with 512-dimensional vectors
        await conn.execute("""
            CREATE TABLE face_embeddings (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL,
                embedding vector(512) NOT NULL,
                image_path TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
        """)
        print("Created new face_embeddings table with 512-dimensional vectors")
        
        # Create indexes
        await conn.execute("CREATE INDEX idx_face_embeddings_employee_id ON face_embeddings(employee_id);")
        print("Created indexes")
        
        print("\nMigration completed successfully!")
        print("Note: All employees need to re-enroll their faces.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_embeddings())

import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from sqlmodel import Session, SQLModel, text
from server.config import config
from server.db.session import engine
from server.db.models import FaceEmbedding

def reset_face_db():
    print(f"Connecting to {config.DB_URL}...")
    with Session(engine) as session:
        print("Dropping 'face_embedding' table...")
        try:
            session.execute(text("DROP TABLE IF EXISTS face_embedding CASCADE"))
            session.commit()
            print("Table dropped successfully.")
        except Exception as e:
            print(f"Error dropping table: {e}")
            session.rollback()
            return

    print("Recreating tables...")
    try:
        # This will recreate all missing tables, including face_embedding with the new schema
        SQLModel.metadata.create_all(engine)
        print("Face database reset complete with new schema (UUID PK).")
    except Exception as e:
        print(f"Error recreating table: {e}")

if __name__ == "__main__":
    reset_face_db()

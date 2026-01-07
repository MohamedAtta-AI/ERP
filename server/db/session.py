from sqlmodel import SQLModel, Session, create_engine
from ..config import config
import sqlmodel

sqlmodel.

engine = create_engine(config.DB_URL, echo=(not config.PRODUCTION))


def init_db():
    # Drops schema (for dev experiments only)
    # SQLModel.metadata.drop_all(engine)

    # Enable pgvector extension in the database
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()
    
    # Create schema
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

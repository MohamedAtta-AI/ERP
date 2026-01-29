from sqlalchemy import text
from sqlmodel import SQLModel, create_engine
from . import models # this import initializes the MetaData object
from ..config import config

engine = create_engine(
    config.DB_URL, echo=(not config.PRODUCTION)
)

async def init_db():
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
    SQLModel.metadata.create_all(engine)

async def get_session():
    with Session(engine) as session:
        yield session


# from sqlalchemy.ext.asyncio import create_async_engine
# from sqlmodel.ext.asyncio.session import AsyncSession

# engine = create_async_engine(
#     config.DB_URL, echo=(not config.PRODUCTION)
# )


# async def init_db():
    # Drops schema (for dev experiments only)
    # SQLModel.metadata.drop_all(engine)

    # Enable pgvector extension in the database
    # async with engine.begin() as conn:
    #     await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    #     await conn.run_sync(SQLModel.metadata.create_all)


# async def get_session():
    # async with AsyncSession(engine, expire_on_commit=False) as session:
    #     yield session
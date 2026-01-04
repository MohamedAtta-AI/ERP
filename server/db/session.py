from sqlmodel import SQLModel, Session, create_engine
from ..config import config


engine = create_engine(config.DB_URL, echo=(not config.PRODUCTION))


def init_db():
    # SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

import os
from contextlib import contextmanager
from sqlmodel import Session, SQLModel, create_engine

from litepolis import get_config

DEFAULT_CONFIG = {
    "database_url": "sqlite:///database.db"
}

if ("PYTEST_CURRENT_TEST" not in os.environ and
    "PYTEST_VERSION" not in os.environ):
    database_url = get_config("litepolis_database_default", "database_url")
else:
    database_url = DEFAULT_CONFIG.get("database_url")
engine = create_engine(database_url,
                        pool_size=5,
                        max_overflow=10,
                        pool_timeout=30,
                        pool_pre_ping=True)

def connect_db():
    engine = create_engine(database_url,
                            pool_size=5,
                            max_overflow=10,
                            pool_timeout=30,
                            pool_pre_ping=True)

def create_db_and_tables():
    # SQLModel.metadata.create_all() has checkfirst=True by default
    # so tables will only be created if they don't exist
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    yield Session(engine)
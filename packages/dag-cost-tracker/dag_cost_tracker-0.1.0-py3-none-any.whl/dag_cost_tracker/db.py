import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dag_cost_tracker.models import Base

# Default DB Path
DEFAULT_DB_PATH = os.path.expanduser("~/.dag_cost_tracker/dag_cost.db")

def get_db_url(db_path=None):
    path = db_path or DEFAULT_DB_PATH
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return f"sqlite:///{path}"

def init_db(db_path=None):
    """Initialize the database and create tables."""
    engine = create_engine(get_db_url(db_path))
    Base.metadata.create_all(engine)
    return engine

def get_session(db_path=None):
    """Get a new database session."""
    engine = create_engine(get_db_url(db_path))
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)

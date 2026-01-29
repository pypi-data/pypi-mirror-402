"""Database engine and session management"""

import os
from pathlib import Path
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine

from cosmux.config import settings

# Global engine instance
_engine = None


def get_engine():
    """Get or create the database engine"""
    global _engine

    if _engine is None:
        # Get workspace from environment
        workspace = Path(os.environ.get("COSMUX_WORKSPACE", "."))
        db_path = settings.get_db_path(workspace)

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create engine
        sqlite_url = f"sqlite:///{db_path}"
        _engine = create_engine(
            sqlite_url,
            echo=settings.log_level == "DEBUG",
            connect_args={"check_same_thread": False},
        )

    return _engine


def create_db_and_tables() -> None:
    """Create all database tables"""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get a database session (dependency injection)"""
    engine = get_engine()
    with Session(engine) as session:
        yield session


# Type alias for FastAPI dependency
SessionDep = Session

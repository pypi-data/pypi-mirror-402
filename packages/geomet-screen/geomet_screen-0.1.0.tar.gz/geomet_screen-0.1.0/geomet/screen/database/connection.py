"""SQLAlchemy database connection for screen deck layouts."""

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

Base = declarative_base()


class DatabaseConnection:
    """Database connection manager for screen deck layouts."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses in-memory database.
        """
        if db_path is None:
            self.db_url = "sqlite:///:memory:"
        else:
            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            self.db_url = f"sqlite:///{db_file}"

        self.engine: Engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """
        Get a database session.

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()

    def close(self):
        """Close the database connection."""
        self.engine.dispose()

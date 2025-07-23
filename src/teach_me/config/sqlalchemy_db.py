"""SQLAlchemy database configuration and session management."""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ..dao.models.job import Base

load_dotenv()
logger = logging.getLogger(__name__)


class Database:
    """Manages database connection, engine, and sessions."""

    def __init__(self, db_url: str):
        if not db_url or "this_is_a_test_url" in db_url:
            raise ValueError("DATABASE_URL is not properly configured.")

        logger.info(f"Initializing database with URL: {db_url[:50]}...")
        self.engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "connect_timeout": 30,
                "application_name": "teach_me_app",
                "keepalives_idle": 600,
                "keepalives_interval": 30,
                "keepalives_count": 3,
            },
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info("SQLAlchemy engine and session factory created.")

    def check_connection(self) -> None:
        """Tests the database connection and logs the result."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful.")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")

    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully.")

    def get_db_session(self) -> Generator[Session, None, None]:
        """Context manager for a session, used as a FastAPI dependency."""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            logger.error(f"Session rollback due to exception: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def transactional_session(self) -> Generator[Session, None, None]:
        """Context manager for a session that commits on success."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


db: Database | None = None
try:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        db = Database(DATABASE_URL)
        db.check_connection()
    else:
        logger.critical("DATABASE_URL environment variable is not set")
except (ValueError, Exception) as e:
    logger.critical(f"Failed to initialize database, application cannot start: {e}")

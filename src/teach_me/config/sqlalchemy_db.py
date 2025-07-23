"""SQLAlchemy database configuration and session management."""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ..dao.models.job import Base

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Supabase connection string format
DATABASE_URL = os.getenv("DATABASE_URL", "this_is_a_test_url")

logger.info(f"Database URL configured: {DATABASE_URL[:50]}...")
# Create engine with connection pooling and timeouts
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections every 5 minutes
    connect_args={
        "connect_timeout": 30,
        "application_name": "teach_me_app",
        "keepalives_idle": 600,
        "keepalives_interval": 30,
        "keepalives_count": 3,
    },
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
)

logger.info("SQLAlchemy engine created successfully")

# Test database connectivity at startup
try:
    logger.info("Testing database connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
except Exception as e:
    logger.error(f"Database connection test failed: {e}")
    # Don't raise here to allow app to start, but log the issue

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get a database session.
    It does NOT commit the session; the calling code is responsible for that.
    """
    logger.debug("Creating new database session")
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Session rollback due to exception: {e}")
        session.rollback()
        raise
    finally:
        logger.debug("Closing database session")
        session.close()


@contextmanager
def transactional_session() -> Generator[Session, None, None]:
    """
    Context manager for a session that commits on success and rolls back on error.
    Use this for scripts, background jobs, or operations outside a web request.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

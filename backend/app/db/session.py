"""SQLAlchemy database session management."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import Config

logger = logging.getLogger(__name__)

# Validate SQLite in prod
if Config.ENV == "production" and Config.DATABASE_URL.startswith("sqlite"):
    logger.warning("Using SQLite database in production environment!")

# Configure engine arguments
engine_kwargs = {
    "echo": Config.DATABASE_ECHO,
}
if Config.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = Config.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = Config.DB_MAX_OVERFLOW

try:
    engine = create_engine(Config.DATABASE_URL, **engine_kwargs)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.critical(f"Failed to initialize database engine: {e}")
    raise

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session management.
    Ensures rollback on exceptions and proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

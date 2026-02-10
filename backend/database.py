"""
Database connection and session management.
Uses SQLAlchemy with support for SQLite (dev) and PostgreSQL (prod).
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from config import settings

# Create engine based on database URL
# SQLite needs special handling for multithreading
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL or other databases
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes to get a database session.
    Ensures proper cleanup after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for non-FastAPI database access.
    Use this in scrapers and scheduled tasks.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Call this on application startup.
    """
    from models import Base  # Import here to avoid circular imports
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Drop all database tables.
    Use with caution - primarily for testing.
    """
    from models import Base
    Base.metadata.drop_all(bind=engine)

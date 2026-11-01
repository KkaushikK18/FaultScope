"""
Database connection and session management.

Provides database engine, session factory, and dependency injection for FastAPI.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import get_settings

settings = get_settings()

# Create database engine
# echo=True would log all SQL queries (useful for debugging)
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before using them
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions in FastAPI.
    
    Yields:
        Session: SQLAlchemy database session
    
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in models if they don't exist.
    For production, use Alembic migrations instead.
    """
    from app.database.base import Base
    
    # Import all models so they're registered with Base
    from app.database.models import service, telemetry, anomaly, incident
    
    Base.metadata.create_all(bind=engine)

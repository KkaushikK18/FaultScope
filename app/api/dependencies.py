"""
API dependencies for dependency injection.

Provides common dependencies used across route handlers.
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_database_session() -> Generator[Session, None, None]:
    """
    Get database session dependency.
    
    This is a wrapper around get_db() that provides better error handling
    for API endpoints.
    
    Yields:
        Session: SQLAlchemy database session
        
    Raises:
        HTTPException: If database connection fails
    """
    try:
        db = next(get_db())
        yield db
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )
    finally:
        db.close()

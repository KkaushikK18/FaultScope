"""
Database initialization script.

Creates all database tables and optionally seeds initial data.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.connection import init_db, engine
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Initialize database tables"""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"Created tables: {', '.join(tables)}")
        
        expected_tables = {'services', 'telemetry_records', 'anomaly_results', 'incidents'}
        if expected_tables.issubset(set(tables)):
            logger.info("All expected tables created successfully")
        else:
            missing = expected_tables - set(tables)
            logger.warning(f"Missing tables: {', '.join(missing)}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

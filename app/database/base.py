"""
SQLAlchemy declarative base.

All database models inherit from this base class.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

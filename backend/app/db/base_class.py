"""
SQLAlchemy 2.0 declarative base class.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Provides a shared metadata and common configuration.
    """
    pass
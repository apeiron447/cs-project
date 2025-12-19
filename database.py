"""
Database configuration and session management for the Course Selection System.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os

# Database URL - SQLite for development, can switch to PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///course_selection.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for thread safety
db_session = scoped_session(SessionLocal)

# Base class for models
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """Initialize the database, creating all tables."""
    from models import (
        User, Department, Programme, Batch, Student, Teacher,
        Course, SeatMatrix, CoursePool, Preference, Allocation
    )
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def get_db():
    """Get a database session. Use as context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def shutdown_session(exception=None):
    """Remove the session at the end of request."""
    db_session.remove()

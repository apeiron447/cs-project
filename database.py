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


# ===========================================
# SEED DATA - Departments from original templates
# ===========================================
SEED_DEPARTMENTS = [
    ("ENG", "Department of English"),
    ("ECO", "Department of Economics"),
    ("JMC", "Department of Journalism & Mass Communication"),
    ("HIS", "Department of History"),
    ("PA", "Department of Public Administration"),
    ("BCH", "Department of Biochemistry"),
    ("BIO", "Department of Biotechnology"),
    ("PHY", "Department of Physics"),
    ("CHE", "Department of Chemistry"),
    ("CSAI", "Department of Computer Science & AI"),
    ("CA", "Department of Computer Application"),
    ("MAT", "Department of Mathematics"),
    ("MIC", "Department of Microbiology"),
    ("PSY", "Department of Psychology"),
    ("COMIF", "Department of Commerce(IF)"),
    ("COM", "Department of Commerce"),
    ("MS", "Department of Management Studies"),
    ("MM", "Department of Multimedia"),
    ("FST", "Department of Food Science & Technology"),
    ("IS", "Department of Islamic Studies"),
]

# Common programmes per department
SEED_PROGRAMMES = {
    "CSAI": ["B.Sc Computer Science", "M.Sc Computer Science", "BCA"],
    "CA": ["BCA", "MCA"],
    "COM": ["B.Com", "M.Com"],
    "COMIF": ["B.Com (Integrated Finance)"],
    "MS": ["BBA", "MBA"],
    "ENG": ["BA English", "MA English"],
    "ECO": ["BA Economics", "MA Economics"],
    "PHY": ["B.Sc Physics", "M.Sc Physics"],
    "CHE": ["B.Sc Chemistry", "M.Sc Chemistry"],
    "MAT": ["B.Sc Mathematics", "M.Sc Mathematics"],
    "BCH": ["B.Sc Biochemistry", "M.Sc Biochemistry"],
    "BIO": ["B.Sc Biotechnology", "M.Sc Biotechnology"],
    "MIC": ["B.Sc Microbiology", "M.Sc Microbiology"],
    "PSY": ["BA Psychology", "MA Psychology"],
    "JMC": ["BA Journalism", "MA Mass Communication"],
    "HIS": ["BA History", "MA History"],
    "PA": ["BA Public Administration", "MA Public Administration"],
    "MM": ["B.Sc Multimedia", "M.Sc Multimedia"],
    "FST": ["B.Sc Food Science", "M.Sc Food Technology"],
    "IS": ["BA Islamic Studies", "MA Islamic Studies"],
}


def seed_initial_data():
    """Seed the database with initial departments and programmes on first run."""
    from models import Department, Programme
    
    # Check if already seeded (departments exist)
    existing = db_session.query(Department).first()
    if existing:
        return False  # Already seeded
    
    print("🌱 First run detected - seeding initial data...")
    
    # Seed departments
    dept_map = {}
    for code, name in SEED_DEPARTMENTS:
        dept = Department(code=code, name=name)
        db_session.add(dept)
        db_session.flush()
        dept_map[code] = dept
        print(f"  ✓ Department: {name}")
    
    # Seed programmes
    for dept_code, prog_list in SEED_PROGRAMMES.items():
        dept = dept_map.get(dept_code)
        if dept:
            for prog_name in prog_list:
                prog = Programme(name=prog_name, department_id=dept.id)
                db_session.add(prog)
    
    db_session.commit()
    print(f"  ✓ Seeded {len(SEED_DEPARTMENTS)} departments and programmes")
    return True


def init_db():
    """Initialize the database, creating all tables and seeding if needed."""
    from models import (
        User, Department, Programme, Batch, Student, Teacher,
        Course, SeatMatrix, CoursePool, Preference, Allocation
    )
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")
    
    # Seed initial data on first run
    seed_initial_data()


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


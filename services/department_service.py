"""
Department Service - CRUD operations for departments.
"""
from sqlalchemy.orm import Session
from models import Department
from typing import List, Optional


class DepartmentService:
    """Service for managing departments."""
    
    @staticmethod
    def create(db: Session, code: str, name: str, head_name: str = None) -> Department:
        """Create a new department."""
        department = Department(
            code=code.upper(),
            name=name,
            head_name=head_name
        )
        db.add(department)
        db.commit()
        db.refresh(department)
        return department
    
    @staticmethod
    def get_by_id(db: Session, dept_id: int) -> Optional[Department]:
        """Get department by ID."""
        return db.query(Department).filter(Department.id == dept_id).first()
    
    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Department]:
        """Get department by code."""
        return db.query(Department).filter(Department.code == code.upper()).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Department]:
        """Get all departments."""
        return db.query(Department).order_by(Department.name).all()
    
    @staticmethod
    def update(db: Session, dept_id: int, **kwargs) -> Optional[Department]:
        """Update department fields."""
        department = db.query(Department).filter(Department.id == dept_id).first()
        if department:
            for key, value in kwargs.items():
                if hasattr(department, key):
                    setattr(department, key, value)
            db.commit()
            db.refresh(department)
        return department
    
    @staticmethod
    def delete(db: Session, dept_id: int) -> bool:
        """Delete a department."""
        department = db.query(Department).filter(Department.id == dept_id).first()
        if department:
            db.delete(department)
            db.commit()
            return True
        return False

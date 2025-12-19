"""
Programme Service - CRUD operations for programmes.
"""
from sqlalchemy.orm import Session
from models import Programme, Department
from typing import List, Optional


class ProgrammeService:
    """Service for managing programmes."""
    
    @staticmethod
    def create(db: Session, name: str, department_id: int, duration_years: int = 3) -> Programme:
        """Create a new programme."""
        programme = Programme(
            name=name,
            department_id=department_id,
            duration_years=duration_years
        )
        db.add(programme)
        db.commit()
        db.refresh(programme)
        return programme
    
    @staticmethod
    def get_by_id(db: Session, prog_id: int) -> Optional[Programme]:
        """Get programme by ID."""
        return db.query(Programme).filter(Programme.id == prog_id).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Programme]:
        """Get all programmes."""
        return db.query(Programme).order_by(Programme.name).all()
    
    @staticmethod
    def get_by_department(db: Session, department_id: int) -> List[Programme]:
        """Get programmes by department."""
        return db.query(Programme).filter(
            Programme.department_id == department_id
        ).order_by(Programme.name).all()
    
    @staticmethod
    def update(db: Session, prog_id: int, **kwargs) -> Optional[Programme]:
        """Update programme fields."""
        programme = db.query(Programme).filter(Programme.id == prog_id).first()
        if programme:
            for key, value in kwargs.items():
                if hasattr(programme, key):
                    setattr(programme, key, value)
            db.commit()
            db.refresh(programme)
        return programme
    
    @staticmethod
    def delete(db: Session, prog_id: int) -> bool:
        """Delete a programme."""
        programme = db.query(Programme).filter(Programme.id == prog_id).first()
        if programme:
            db.delete(programme)
            db.commit()
            return True
        return False

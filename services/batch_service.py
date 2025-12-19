"""
Batch Service - CRUD operations for batches.
"""
from sqlalchemy.orm import Session
from models import Batch
from typing import List, Optional


class BatchService:
    """Service for managing batches."""
    
    @staticmethod
    def create(
        db: Session, 
        programme_id: int, 
        start_year: int, 
        end_year: int, 
        current_semester: int = 1
    ) -> Batch:
        """Create a new batch."""
        batch = Batch(
            programme_id=programme_id,
            start_year=start_year,
            end_year=end_year,
            current_semester=current_semester
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch
    
    @staticmethod
    def get_by_id(db: Session, batch_id: int) -> Optional[Batch]:
        """Get batch by ID."""
        return db.query(Batch).filter(Batch.id == batch_id).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Batch]:
        """Get all batches."""
        return db.query(Batch).order_by(Batch.start_year.desc()).all()
    
    @staticmethod
    def get_by_programme(db: Session, programme_id: int) -> List[Batch]:
        """Get batches by programme."""
        return db.query(Batch).filter(
            Batch.programme_id == programme_id
        ).order_by(Batch.start_year.desc()).all()
    
    @staticmethod
    def get_active_batches(db: Session, current_year: int) -> List[Batch]:
        """Get currently active batches."""
        return db.query(Batch).filter(
            Batch.start_year <= current_year,
            Batch.end_year >= current_year
        ).all()
    
    @staticmethod
    def update_semester(db: Session, batch_id: int, semester: int) -> Optional[Batch]:
        """Update batch semester."""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch:
            batch.current_semester = semester
            db.commit()
            db.refresh(batch)
        return batch
    
    @staticmethod
    def delete(db: Session, batch_id: int) -> bool:
        """Delete a batch."""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch:
            db.delete(batch)
            db.commit()
            return True
        return False

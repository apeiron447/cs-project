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
        """Delete a batch and all related records including students."""
        from models import CoursePool, Preference, Allocation, Student, User
        
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch:
            # Delete course pools for this batch
            db.query(CoursePool).filter(CoursePool.batch_id == batch_id).delete()
            
            # Get students in this batch
            students = db.query(Student).filter(Student.batch_id == batch_id).all()
            student_ids = [s.id for s in students]
            user_ids = [s.user_id for s in students if s.user_id]
            
            if student_ids:
                # Delete allocations for these students
                db.query(Allocation).filter(Allocation.student_id.in_(student_ids)).delete(synchronize_session='fetch')
                # Delete preferences for these students
                db.query(Preference).filter(Preference.student_id.in_(student_ids)).delete(synchronize_session='fetch')
                # Delete students
                db.query(Student).filter(Student.id.in_(student_ids)).delete(synchronize_session='fetch')
            
            # Delete user accounts for the students
            if user_ids:
                db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session='fetch')
            
            # Now delete the batch
            db.delete(batch)
            db.commit()
            return True
        return False


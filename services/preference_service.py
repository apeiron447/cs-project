"""
Preference Service - Student course preference management.
"""
from sqlalchemy.orm import Session
from models import Preference, Student, Course, CoursePool
from typing import List, Optional
from datetime import datetime


class PreferenceService:
    """Service for managing student course preferences."""
    
    @staticmethod
    def submit_preferences(
        db: Session,
        student_id: int,
        course_ids: List[int]
    ) -> List[Preference]:
        """
        Submit/update student preferences.
        course_ids should be in priority order (first = highest preference).
        """
        # Get student to verify batch
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise ValueError("Student not found")
        
        # Verify courses are in the student's batch pool
        valid_courses = PreferenceService.get_available_courses(db, student_id)
        valid_course_ids = {c.id for c in valid_courses}
        
        for course_id in course_ids:
            if course_id not in valid_course_ids:
                raise ValueError(f"Course {course_id} is not available for your batch")
        
        # Delete existing preferences
        db.query(Preference).filter(Preference.student_id == student_id).delete()
        
        # Create new preferences
        preferences = []
        for priority, course_id in enumerate(course_ids, start=1):
            pref = Preference(
                student_id=student_id,
                course_id=course_id,
                priority=priority,
                submitted_at=datetime.utcnow()
            )
            db.add(pref)
            preferences.append(pref)
        
        db.commit()
        for pref in preferences:
            db.refresh(pref)
        
        return preferences
    
    @staticmethod
    def get_student_preferences(db: Session, student_id: int) -> List[Preference]:
        """Get all preferences for a student, ordered by priority."""
        return db.query(Preference).filter(
            Preference.student_id == student_id
        ).order_by(Preference.priority).all()
    
    @staticmethod
    def get_available_courses(db: Session, student_id: int) -> List[Course]:
        """Get courses available for a student based on their batch.
        Excludes courses from the student's own department (electives only)."""
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return []

        # Get courses from the student's batch pool, excluding own department
        pool_entries = db.query(CoursePool).filter(
            CoursePool.batch_id == student.batch_id,
            CoursePool.is_active == True
        ).all()

        return [
            entry.course for entry in pool_entries
            if entry.course.is_active and entry.course.department_id != student.department_id
        ]
    
    @staticmethod
    def clear_preferences(db: Session, student_id: int) -> bool:
        """Clear all preferences for a student."""
        result = db.query(Preference).filter(
            Preference.student_id == student_id
        ).delete()
        db.commit()
        return result > 0
    
    @staticmethod
    def clear_all_preferences(db: Session, batch_id: int = None) -> int:
        """Clear all preferences, optionally for a specific batch."""
        if batch_id:
            # Get student IDs for the batch
            students = db.query(Student).filter(
                Student.batch_id == batch_id
            ).all()
            student_ids = [s.id for s in students]
            
            result = db.query(Preference).filter(
                Preference.student_id.in_(student_ids)
            ).delete(synchronize_session='fetch')
        else:
            result = db.query(Preference).delete()
        
        db.commit()
        return result
    
    @staticmethod
    def has_submitted(db: Session, student_id: int) -> bool:
        """Check if student has submitted preferences."""
        return db.query(Preference).filter(
            Preference.student_id == student_id
        ).first() is not None

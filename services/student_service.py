"""
Student Service - CRUD operations for students.
"""
from sqlalchemy.orm import Session
from models import Student, User, UserRole, ReservationCategory
from typing import List, Optional
from datetime import date
from werkzeug.security import generate_password_hash


class StudentService:
    """Service for managing students."""
    
    @staticmethod
    def create(
        db: Session,
        admission_no: str,
        exam_register_no: str,
        roll_no: str,
        name: str,
        email: str,
        password: str,
        department_id: int,
        programme_id: int,
        batch_id: int,
        admission_year: int,
        qualifying_marks: float,
        reservation_category: str = "General",
        contact_no: str = None,
        date_of_birth: date = None
    ) -> Student:
        """Create a new student with user account."""
        # Create user account
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole.STUDENT
        )
        db.add(user)
        db.flush()  # Get user ID
        
        # Map reservation category string to enum
        category_map = {
            "General": ReservationCategory.GENERAL,
            "EWS": ReservationCategory.EWS,
            "OBC": ReservationCategory.OBC,
            "SC": ReservationCategory.SC,
            "ST": ReservationCategory.ST,
        }
        
        # Create student
        student = Student(
            user_id=user.id,
            admission_no=admission_no,
            exam_register_no=exam_register_no,
            roll_no=roll_no,
            name=name,
            email=email,
            contact_no=contact_no,
            date_of_birth=date_of_birth,
            department_id=department_id,
            programme_id=programme_id,
            batch_id=batch_id,
            admission_year=admission_year,
            qualifying_marks=qualifying_marks,
            reservation_category=category_map.get(reservation_category, ReservationCategory.GENERAL)
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    
    @staticmethod
    def get_by_id(db: Session, student_id: int) -> Optional[Student]:
        """Get student by ID."""
        return db.query(Student).filter(Student.id == student_id).first()
    
    @staticmethod
    def get_by_admission_no(db: Session, admission_no: str) -> Optional[Student]:
        """Get student by admission number."""
        return db.query(Student).filter(Student.admission_no == admission_no).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Student]:
        """Get student by email."""
        return db.query(Student).filter(Student.email == email).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Student]:
        """Get all students."""
        return db.query(Student).order_by(Student.name).all()
    
    @staticmethod
    def get_by_batch(db: Session, batch_id: int) -> List[Student]:
        """Get students by batch."""
        return db.query(Student).filter(
            Student.batch_id == batch_id
        ).order_by(Student.qualifying_marks.desc()).all()
    
    @staticmethod
    def get_by_department(db: Session, department_id: int) -> List[Student]:
        """Get students by department."""
        return db.query(Student).filter(
            Student.department_id == department_id
        ).order_by(Student.name).all()
    
    @staticmethod
    def get_by_programme_and_batch(db: Session, programme_id: int, batch_id: int) -> List[Student]:
        """Get students by programme and batch, sorted by merit."""
        return db.query(Student).filter(
            Student.programme_id == programme_id,
            Student.batch_id == batch_id
        ).order_by(Student.qualifying_marks.desc()).all()
    
    @staticmethod
    def update(db: Session, student_id: int, **kwargs) -> Optional[Student]:
        """Update student fields."""
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            for key, value in kwargs.items():
                if hasattr(student, key):
                    setattr(student, key, value)
            db.commit()
            db.refresh(student)
        return student
    
    @staticmethod
    def delete(db: Session, student_id: int) -> bool:
        """Delete a student."""
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            # Also delete associated user
            if student.user:
                db.delete(student.user)
            db.delete(student)
            db.commit()
            return True
        return False

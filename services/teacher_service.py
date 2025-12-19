"""
Teacher Service - CRUD operations for teachers.
"""
from sqlalchemy.orm import Session
from models import Teacher, User, UserRole, Designation
from typing import List, Optional
from werkzeug.security import generate_password_hash


class TeacherService:
    """Service for managing teachers."""
    
    @staticmethod
    def create(
        db: Session,
        faculty_id: str,
        name: str,
        email: str,
        password: str,
        department_id: int,
        designation: str = "AP",
        contact_no: str = None
    ) -> Teacher:
        """Create a new teacher with user account."""
        # Create user account
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole.TEACHER
        )
        db.add(user)
        db.flush()  # Get user ID
        
        # Map designation string to enum
        designation_map = {
            "AP": Designation.ASSISTANT_PROFESSOR,
            "P": Designation.PROFESSOR,
        }
        
        # Create teacher
        teacher = Teacher(
            user_id=user.id,
            faculty_id=faculty_id,
            name=name,
            email=email,
            contact_no=contact_no,
            department_id=department_id,
            designation=designation_map.get(designation, Designation.ASSISTANT_PROFESSOR)
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher
    
    @staticmethod
    def get_by_id(db: Session, teacher_id: int) -> Optional[Teacher]:
        """Get teacher by ID."""
        return db.query(Teacher).filter(Teacher.id == teacher_id).first()
    
    @staticmethod
    def get_by_faculty_id(db: Session, faculty_id: str) -> Optional[Teacher]:
        """Get teacher by faculty ID."""
        return db.query(Teacher).filter(Teacher.faculty_id == faculty_id).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Teacher]:
        """Get teacher by email."""
        return db.query(Teacher).filter(Teacher.email == email).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Teacher]:
        """Get all teachers."""
        return db.query(Teacher).order_by(Teacher.name).all()
    
    @staticmethod
    def get_by_department(db: Session, department_id: int) -> List[Teacher]:
        """Get teachers by department."""
        return db.query(Teacher).filter(
            Teacher.department_id == department_id
        ).order_by(Teacher.name).all()
    
    @staticmethod
    def update(db: Session, teacher_id: int, **kwargs) -> Optional[Teacher]:
        """Update teacher fields."""
        teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
        if teacher:
            for key, value in kwargs.items():
                if hasattr(teacher, key):
                    setattr(teacher, key, value)
            db.commit()
            db.refresh(teacher)
        return teacher
    
    @staticmethod
    def delete(db: Session, teacher_id: int) -> bool:
        """Delete a teacher."""
        teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
        if teacher:
            if teacher.user:
                db.delete(teacher.user)
            db.delete(teacher)
            db.commit()
            return True
        return False

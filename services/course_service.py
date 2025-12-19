"""
Course Service - CRUD operations for courses.
"""
from sqlalchemy.orm import Session
from models import Course, SeatMatrix, CoursePool, CourseType, ReservationCategory
from typing import List, Optional


class CourseService:
    """Service for managing courses."""
    
    @staticmethod
    def create(
        db: Session,
        code: str,
        name: str,
        course_type: str,
        department_id: int,
        max_capacity: int,
        teacher_id: int = None,
        reserved_seats_percent: float = 0,
        credits: int = 3,
        description: str = None
    ) -> Course:
        """Create a new course with seat matrix."""
        # Map course type string to enum
        type_map = {
            "Minor": CourseType.MINOR,
            "MDC": CourseType.MDC,
        }
        
        # Create course
        course = Course(
            code=code.upper(),
            name=name,
            description=description,
            course_type=type_map.get(course_type, CourseType.MINOR),
            credits=credits,
            department_id=department_id,
            teacher_id=teacher_id,
            max_capacity=max_capacity,
            reserved_seats_percent=reserved_seats_percent
        )
        db.add(course)
        db.flush()  # Get course ID
        
        # Create seat matrix with default distribution
        seat_matrix = CourseService._create_seat_matrix(
            db, course.id, max_capacity, reserved_seats_percent
        )
        
        db.commit()
        db.refresh(course)
        return course
    
    @staticmethod
    def _create_seat_matrix(
        db: Session, 
        course_id: int, 
        max_capacity: int, 
        reserved_percent: float
    ) -> SeatMatrix:
        """Create seat matrix with category-wise distribution."""
        # Default reservation distribution (can be customized)
        # Total reserved = reserved_percent
        # SC: 15%, ST: 7.5%, OBC: 27%, EWS: 10% (of reserved seats)
        reserved_seats = int(max_capacity * reserved_percent / 100)
        general_seats = max_capacity - reserved_seats
        
        # Distribute reserved seats (approximate standard reservation percentages)
        if reserved_seats > 0:
            sc_seats = int(reserved_seats * 0.25)  # ~15% of total = 25% of reserved
            st_seats = int(reserved_seats * 0.125)  # ~7.5% of total
            obc_seats = int(reserved_seats * 0.45)  # ~27% of total
            ews_seats = reserved_seats - sc_seats - st_seats - obc_seats  # Rest
        else:
            sc_seats = st_seats = obc_seats = ews_seats = 0
        
        seat_matrix = SeatMatrix(
            course_id=course_id,
            general_seats=general_seats,
            ews_seats=ews_seats,
            obc_seats=obc_seats,
            sc_seats=sc_seats,
            st_seats=st_seats,
            # Initialize remaining = total
            general_remaining=general_seats,
            ews_remaining=ews_seats,
            obc_remaining=obc_seats,
            sc_remaining=sc_seats,
            st_remaining=st_seats
        )
        db.add(seat_matrix)
        return seat_matrix
    
    @staticmethod
    def get_by_id(db: Session, course_id: int) -> Optional[Course]:
        """Get course by ID."""
        return db.query(Course).filter(Course.id == course_id).first()
    
    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Course]:
        """Get course by code."""
        return db.query(Course).filter(Course.code == code.upper()).first()
    
    @staticmethod
    def get_all(db: Session, active_only: bool = True) -> List[Course]:
        """Get all courses."""
        query = db.query(Course)
        if active_only:
            query = query.filter(Course.is_active == True)
        return query.order_by(Course.code).all()
    
    @staticmethod
    def get_by_department(db: Session, department_id: int) -> List[Course]:
        """Get courses by offering department."""
        return db.query(Course).filter(
            Course.department_id == department_id,
            Course.is_active == True
        ).order_by(Course.code).all()
    
    @staticmethod
    def get_by_teacher(db: Session, teacher_id: int) -> List[Course]:
        """Get courses by teacher."""
        return db.query(Course).filter(
            Course.teacher_id == teacher_id,
            Course.is_active == True
        ).order_by(Course.code).all()
    
    @staticmethod
    def add_to_pool(db: Session, course_id: int, batch_id: int) -> CoursePool:
        """Add course to a batch's course pool."""
        # Check if already exists
        existing = db.query(CoursePool).filter(
            CoursePool.course_id == course_id,
            CoursePool.batch_id == batch_id
        ).first()
        
        if existing:
            existing.is_active = True
            db.commit()
            return existing
        
        pool_entry = CoursePool(
            course_id=course_id,
            batch_id=batch_id,
            is_active=True
        )
        db.add(pool_entry)
        db.commit()
        db.refresh(pool_entry)
        return pool_entry
    
    @staticmethod
    def get_pool_for_batch(db: Session, batch_id: int) -> List[Course]:
        """Get available courses for a batch."""
        pool_entries = db.query(CoursePool).filter(
            CoursePool.batch_id == batch_id,
            CoursePool.is_active == True
        ).all()
        return [entry.course for entry in pool_entries if entry.course.is_active]
    
    @staticmethod
    def update_seat_matrix(
        db: Session, 
        course_id: int,
        general_seats: int = None,
        ews_seats: int = None,
        obc_seats: int = None,
        sc_seats: int = None,
        st_seats: int = None
    ) -> Optional[SeatMatrix]:
        """Update seat matrix for a course."""
        seat_matrix = db.query(SeatMatrix).filter(
            SeatMatrix.course_id == course_id
        ).first()
        
        if seat_matrix:
            if general_seats is not None:
                seat_matrix.general_seats = general_seats
                seat_matrix.general_remaining = general_seats
            if ews_seats is not None:
                seat_matrix.ews_seats = ews_seats
                seat_matrix.ews_remaining = ews_seats
            if obc_seats is not None:
                seat_matrix.obc_seats = obc_seats
                seat_matrix.obc_remaining = obc_seats
            if sc_seats is not None:
                seat_matrix.sc_seats = sc_seats
                seat_matrix.sc_remaining = sc_seats
            if st_seats is not None:
                seat_matrix.st_seats = st_seats
                seat_matrix.st_remaining = st_seats
            
            db.commit()
            db.refresh(seat_matrix)
        return seat_matrix
    
    @staticmethod
    def reset_seat_matrix(db: Session, course_id: int) -> Optional[SeatMatrix]:
        """Reset remaining seats to original values."""
        seat_matrix = db.query(SeatMatrix).filter(
            SeatMatrix.course_id == course_id
        ).first()
        
        if seat_matrix:
            seat_matrix.general_remaining = seat_matrix.general_seats
            seat_matrix.ews_remaining = seat_matrix.ews_seats
            seat_matrix.obc_remaining = seat_matrix.obc_seats
            seat_matrix.sc_remaining = seat_matrix.sc_seats
            seat_matrix.st_remaining = seat_matrix.st_seats
            db.commit()
            db.refresh(seat_matrix)
        return seat_matrix
    
    @staticmethod
    def delete(db: Session, course_id: int) -> bool:
        """Soft delete a course (set inactive)."""
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            course.is_active = False
            db.commit()
            return True
        return False

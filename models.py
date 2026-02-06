"""
SQLAlchemy Models for the Choice-Based Course Selection System.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, Text, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base
import enum


# ============================================
# ENUMS
# ============================================

class UserRole(enum.Enum):
    ADMIN = "admin"
    STUDENT = "student"
    TEACHER = "teacher"
    DEPARTMENT = "department"


class ReservationCategory(enum.Enum):
    GENERAL = "General"
    EWS = "EWS"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"


class CourseType(enum.Enum):
    MINOR = "Minor"
    MDC = "MDC"


class Designation(enum.Enum):
    ASSISTANT_PROFESSOR = "AP"
    PROFESSOR = "P"


class AllocationStatus(enum.Enum):
    ALLOCATED = "Allocated"
    WAITLISTED = "Waitlisted"
    NOT_ALLOCATED = "Not Allocated"


# ============================================
# USER MODEL (Base for authentication)
# ============================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"


# ============================================
# DEPARTMENT MODEL
# ============================================

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    head_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    programmes = relationship("Programme", back_populates="department")
    teachers = relationship("Teacher", back_populates="department")
    students = relationship("Student", back_populates="department")
    courses = relationship("Course", back_populates="offering_department")

    def __repr__(self):
        return f"<Department {self.code}: {self.name}>"


# ============================================
# PROGRAMME MODEL
# ============================================

class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    duration_years = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'department_id', name='uq_programme_dept'),
    )

    # Relationships
    department = relationship("Department", back_populates="programmes")
    batches = relationship("Batch", back_populates="programme")
    students = relationship("Student", back_populates="programme")

    def __repr__(self):
        return f"<Programme {self.name}>"


# ============================================
# BATCH MODEL
# ============================================

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    current_semester = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint('programme_id', 'start_year', name='uq_batch_programme_year'),
    )

    # Relationships
    programme = relationship("Programme", back_populates="batches")
    students = relationship("Student", back_populates="batch")
    course_pools = relationship("CoursePool", back_populates="batch")

    def __repr__(self):
        return f"<Batch {self.programme.name if self.programme else 'N/A'} {self.start_year}-{self.end_year}>"


# ============================================
# STUDENT MODEL
# ============================================

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Identifiers
    admission_no = Column(String(50), unique=True, nullable=False, index=True)
    exam_register_no = Column(String(50), unique=True, nullable=False)
    roll_no = Column(String(50), nullable=False)
    
    # Personal Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    contact_no = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    
    # Academic Info
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    admission_year = Column(Integer, nullable=False)
    
    # Merit & Reservation
    qualifying_marks = Column(Float, nullable=False)  # For merit-based allocation
    reservation_category = Column(SQLEnum(ReservationCategory), default=ReservationCategory.GENERAL)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="student")
    department = relationship("Department", back_populates="students")
    programme = relationship("Programme", back_populates="students")
    batch = relationship("Batch", back_populates="students")
    preferences = relationship("Preference", back_populates="student", order_by="Preference.priority")
    allocations = relationship("Allocation", back_populates="student")
    academic_history = relationship("StudentAcademicHistory", back_populates="student", order_by="StudentAcademicHistory.semester")
    subject_marks = relationship("StudentSubjectMark", back_populates="student")
    interests = relationship("StudentInterest", back_populates="student")

    def __repr__(self):
        return f"<Student {self.admission_no}: {self.name}>"


# ============================================
# TEACHER MODEL
# ============================================

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    faculty_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    contact_no = Column(String(20), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(SQLEnum(Designation), default=Designation.ASSISTANT_PROFESSOR)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="teacher")
    department = relationship("Department", back_populates="teachers")
    courses = relationship("Course", back_populates="teacher")

    def __repr__(self):
        return f"<Teacher {self.faculty_id}: {self.name}>"


# ============================================
# COURSE MODEL
# ============================================

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    course_type = Column(SQLEnum(CourseType), nullable=False)
    credits = Column(Integer, default=3)
    
    # Offering details
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    
    # Capacity
    max_capacity = Column(Integer, nullable=False)
    reserved_seats_percent = Column(Float, default=0)  # % for reservation categories
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # AI Recommendation fields
    difficulty_level = Column(Integer, default=5)  # Scale 1-10
    tags = Column(String(500), nullable=True)  # Comma-separated tags e.g. "programming,algorithms"

    # Relationships
    offering_department = relationship("Department", back_populates="courses")
    teacher = relationship("Teacher", back_populates="courses")
    seat_matrix = relationship("SeatMatrix", back_populates="course", uselist=False)
    course_pools = relationship("CoursePool", back_populates="course")
    preferences = relationship("Preference", back_populates="course")
    allocations = relationship("Allocation", back_populates="course")

    def __repr__(self):
        return f"<Course {self.code}: {self.name}>"


# ============================================
# SEAT MATRIX MODEL (Category-wise seats)
# ============================================

class SeatMatrix(Base):
    __tablename__ = "seat_matrices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), unique=True, nullable=False)
    
    # Category-wise seat allocation
    general_seats = Column(Integer, default=0)
    ews_seats = Column(Integer, default=0)
    obc_seats = Column(Integer, default=0)
    sc_seats = Column(Integer, default=0)
    st_seats = Column(Integer, default=0)
    
    # Remaining seats (updated during allocation)
    general_remaining = Column(Integer, default=0)
    ews_remaining = Column(Integer, default=0)
    obc_remaining = Column(Integer, default=0)
    sc_remaining = Column(Integer, default=0)
    st_remaining = Column(Integer, default=0)

    # Relationships
    course = relationship("Course", back_populates="seat_matrix")

    def __repr__(self):
        return f"<SeatMatrix for Course {self.course_id}>"
    
    def get_remaining_for_category(self, category: ReservationCategory) -> int:
        """Get remaining seats for a specific category."""
        mapping = {
            ReservationCategory.GENERAL: self.general_remaining,
            ReservationCategory.EWS: self.ews_remaining,
            ReservationCategory.OBC: self.obc_remaining,
            ReservationCategory.SC: self.sc_remaining,
            ReservationCategory.ST: self.st_remaining,
        }
        return mapping.get(category, 0)
    
    def decrement_seat(self, category: ReservationCategory) -> bool:
        """Decrement seat count for a category. Returns True if successful."""
        if category == ReservationCategory.GENERAL and self.general_remaining > 0:
            self.general_remaining -= 1
            return True
        elif category == ReservationCategory.EWS and self.ews_remaining > 0:
            self.ews_remaining -= 1
            return True
        elif category == ReservationCategory.OBC and self.obc_remaining > 0:
            self.obc_remaining -= 1
            return True
        elif category == ReservationCategory.SC and self.sc_remaining > 0:
            self.sc_remaining -= 1
            return True
        elif category == ReservationCategory.ST and self.st_remaining > 0:
            self.st_remaining -= 1
            return True
        return False


# ============================================
# COURSE POOL MODEL (Courses available for choice)
# ============================================

class CoursePool(Base):
    __tablename__ = "course_pools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint('course_id', 'batch_id', name='uq_coursepool_course_batch'),
    )

    # Relationships
    course = relationship("Course", back_populates="course_pools")
    batch = relationship("Batch", back_populates="course_pools")

    def __repr__(self):
        return f"<CoursePool Course:{self.course_id} Batch:{self.batch_id}>"


# ============================================
# PREFERENCE MODEL (Student course preferences)
# ============================================

class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    priority = Column(Integer, nullable=False)  # 1 = highest preference
    submitted_at = Column(DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint('student_id', 'course_id', name='uq_preference_student_course'),
        UniqueConstraint('student_id', 'priority', name='uq_preference_student_priority'),
    )

    # Relationships
    student = relationship("Student", back_populates="preferences")
    course = relationship("Course", back_populates="preferences")

    def __repr__(self):
        return f"<Preference Student:{self.student_id} Course:{self.course_id} Priority:{self.priority}>"


# ============================================
# ALLOCATION MODEL (Final course allocations)
# ============================================

class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    status = Column(SQLEnum(AllocationStatus), default=AllocationStatus.ALLOCATED)
    preference_number = Column(Integer, nullable=True)  # Which preference was allocated
    allocation_round = Column(Integer, default=1)  # For multiple allocation rounds
    
    allocated_at = Column(DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint('student_id', 'course_id', 'allocation_round', name='uq_allocation'),
    )

    # Relationships
    student = relationship("Student", back_populates="allocations")
    course = relationship("Course", back_populates="allocations")

    def __repr__(self):
        return f"<Allocation Student:{self.student_id} Course:{self.course_id} Status:{self.status.value}>"


# ============================================
# STUDENT ACADEMIC HISTORY (for AI module)
# ============================================

class StudentAcademicHistory(Base):
    __tablename__ = "student_academic_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=True)
    sgpa = Column(Float, nullable=True)
    total_marks = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('student_id', 'semester', name='uq_student_semester'),
    )

    student = relationship("Student", back_populates="academic_history")

    def __repr__(self):
        return f"<AcademicHistory Student:{self.student_id} Sem:{self.semester} CGPA:{self.cgpa}>"


# ============================================
# STUDENT SUBJECT MARKS (for AI module)
# ============================================

class StudentSubjectMark(Base):
    __tablename__ = "student_subject_marks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_name = Column(String(255), nullable=False)
    marks_obtained = Column(Float, nullable=True)
    max_marks = Column(Float, default=100)
    grade = Column(String(5), nullable=True)
    semester = Column(Integer, nullable=True)

    student = relationship("Student", back_populates="subject_marks")

    def __repr__(self):
        return f"<SubjectMark Student:{self.student_id} {self.subject_name}: {self.marks_obtained}>"


# ============================================
# STUDENT INTERESTS (for AI module)
# ============================================

class StudentInterest(Base):
    __tablename__ = "student_interests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    interest_tag = Column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint('student_id', 'interest_tag', name='uq_student_interest'),
    )

    student = relationship("Student", back_populates="interests")

    def __repr__(self):
        return f"<StudentInterest Student:{self.student_id} Tag:{self.interest_tag}>"

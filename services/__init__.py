"""
Services package for business logic.
"""
from .department_service import DepartmentService
from .programme_service import ProgrammeService
from .batch_service import BatchService
from .student_service import StudentService
from .teacher_service import TeacherService
from .course_service import CourseService
from .preference_service import PreferenceService
from .allocation_service import AllocationService

__all__ = [
    "DepartmentService",
    "ProgrammeService", 
    "BatchService",
    "StudentService",
    "TeacherService",
    "CourseService",
    "PreferenceService",
    "AllocationService",
]

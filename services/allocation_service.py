"""
Allocation Service - Core allocation engine for course selection.
Implements merit + preference + reservation based allocation.
"""
from sqlalchemy.orm import Session
from models import (
    Student, Course, Preference, Allocation, SeatMatrix,
    AllocationStatus, ReservationCategory, CoursePool
)
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class AllocationResult:
    """Result of an allocation run."""
    total_students: int
    allocated_count: int
    waitlisted_count: int
    not_allocated_count: int
    allocations_by_course: Dict[int, int]  # course_id -> count
    allocations_by_category: Dict[str, int]  # category -> count


class AllocationService:
    """
    Service for running course allocation based on:
    1. Merit (CGPA/Marks) - Higher marks = priority
    2. Preference order - Earlier preference = priority
    3. Reservation category - Category-wise seat allocation
    """
    
    @staticmethod
    def run_allocation(
        db: Session,
        batch_id: int,
        allocation_round: int = 1
    ) -> AllocationResult:
        """
        Run the allocation algorithm for a batch.
        
        Algorithm:
        1. Fetch eligible students sorted by merit (descending)
        2. For each student:
           a. Get their preference list
           b. For each preferred course (in order):
              - Check seat availability for student's reservation category
              - If available: allocate, reduce seat count
              - Move to next student
           c. If no seats in any preferred course: mark WAITLIST
        3. Save all allocations
        """
        # Clear previous allocations for this round
        AllocationService._clear_allocations(db, batch_id, allocation_round)
        
        # Reset seat matrix for all courses in the pool
        AllocationService._reset_seat_matrices(db, batch_id)
        
        # Get eligible students sorted by merit
        students = db.query(Student).filter(
            Student.batch_id == batch_id
        ).order_by(Student.qualifying_marks.desc()).all()
        
        if not students:
            return AllocationResult(
                total_students=0,
                allocated_count=0,
                waitlisted_count=0,
                not_allocated_count=0,
                allocations_by_course={},
                allocations_by_category={}
            )
        
        # Track statistics
        allocated_count = 0
        waitlisted_count = 0
        not_allocated_count = 0
        allocations_by_course: Dict[int, int] = {}
        allocations_by_category: Dict[str, int] = {}
        
        # Process each student
        for student in students:
            result = AllocationService._allocate_student(
                db, student, allocation_round
            )
            
            if result:
                allocation, status = result
                if status == AllocationStatus.ALLOCATED:
                    allocated_count += 1
                    course_id = allocation.course_id
                    allocations_by_course[course_id] = allocations_by_course.get(course_id, 0) + 1
                    
                    category = student.reservation_category.value
                    allocations_by_category[category] = allocations_by_category.get(category, 0) + 1
                elif status == AllocationStatus.WAITLISTED:
                    waitlisted_count += 1
            else:
                not_allocated_count += 1
        
        db.commit()
        
        return AllocationResult(
            total_students=len(students),
            allocated_count=allocated_count,
            waitlisted_count=waitlisted_count,
            not_allocated_count=not_allocated_count,
            allocations_by_course=allocations_by_course,
            allocations_by_category=allocations_by_category
        )
    
    @staticmethod
    def _allocate_student(
        db: Session,
        student: Student,
        allocation_round: int
    ) -> Optional[Tuple[Allocation, AllocationStatus]]:
        """
        Try to allocate a student to one of their preferred courses.
        Returns (Allocation, Status) if processed, None if no preferences.
        """
        # Get student's preferences in order
        preferences = db.query(Preference).filter(
            Preference.student_id == student.id
        ).order_by(Preference.priority).all()
        
        if not preferences:
            # No preferences submitted
            return None
        
        # Try each preference in order
        for pref in preferences:
            course = db.query(Course).filter(
                Course.id == pref.course_id,
                Course.is_active == True
            ).first()
            
            if not course:
                continue
            
            # Check seat availability for student's category
            seat_matrix = db.query(SeatMatrix).filter(
                SeatMatrix.course_id == course.id
            ).first()
            
            if not seat_matrix:
                continue
            
            # Try to get seat for student's category
            if AllocationService._try_allocate_seat(seat_matrix, student.reservation_category):
                # Seat available! Create allocation
                allocation = Allocation(
                    student_id=student.id,
                    course_id=course.id,
                    status=AllocationStatus.ALLOCATED,
                    preference_number=pref.priority,
                    allocation_round=allocation_round,
                    allocated_at=datetime.utcnow()
                )
                db.add(allocation)
                return (allocation, AllocationStatus.ALLOCATED)
            
            # Try unreserved/general seats as fallback
            if student.reservation_category != ReservationCategory.GENERAL:
                if AllocationService._try_allocate_seat(seat_matrix, ReservationCategory.GENERAL):
                    allocation = Allocation(
                        student_id=student.id,
                        course_id=course.id,
                        status=AllocationStatus.ALLOCATED,
                        preference_number=pref.priority,
                        allocation_round=allocation_round,
                        allocated_at=datetime.utcnow()
                    )
                    db.add(allocation)
                    return (allocation, AllocationStatus.ALLOCATED)
        
        # No seat available in any preferred course - mark as waitlisted
        # Waitlist for the first preference
        first_pref = preferences[0]
        allocation = Allocation(
            student_id=student.id,
            course_id=first_pref.course_id,
            status=AllocationStatus.WAITLISTED,
            preference_number=first_pref.priority,
            allocation_round=allocation_round,
            allocated_at=datetime.utcnow()
        )
        db.add(allocation)
        return (allocation, AllocationStatus.WAITLISTED)
    
    @staticmethod
    def _try_allocate_seat(seat_matrix: SeatMatrix, category: ReservationCategory) -> bool:
        """Try to allocate a seat for the given category. Returns True if successful."""
        return seat_matrix.decrement_seat(category)
    
    @staticmethod
    def _clear_allocations(db: Session, batch_id: int, allocation_round: int):
        """Clear existing allocations for a batch and round."""
        # Get student IDs for the batch
        students = db.query(Student).filter(
            Student.batch_id == batch_id
        ).all()
        student_ids = [s.id for s in students]
        
        if student_ids:
            db.query(Allocation).filter(
                Allocation.student_id.in_(student_ids),
                Allocation.allocation_round == allocation_round
            ).delete(synchronize_session='fetch')
    
    @staticmethod
    def _reset_seat_matrices(db: Session, batch_id: int):
        """Reset seat matrices for all courses in the batch's pool."""
        # Get courses in the batch's pool
        pool_entries = db.query(CoursePool).filter(
            CoursePool.batch_id == batch_id,
            CoursePool.is_active == True
        ).all()
        
        for entry in pool_entries:
            seat_matrix = db.query(SeatMatrix).filter(
                SeatMatrix.course_id == entry.course_id
            ).first()
            
            if seat_matrix:
                seat_matrix.general_remaining = seat_matrix.general_seats
                seat_matrix.ews_remaining = seat_matrix.ews_seats
                seat_matrix.obc_remaining = seat_matrix.obc_seats
                seat_matrix.sc_remaining = seat_matrix.sc_seats
                seat_matrix.st_remaining = seat_matrix.st_seats
    
    # ============================================
    # REPORTING METHODS
    # ============================================
    
    @staticmethod
    def get_student_allocation(
        db: Session, 
        student_id: int,
        allocation_round: int = None
    ) -> Optional[Allocation]:
        """Get allocation for a specific student."""
        query = db.query(Allocation).filter(
            Allocation.student_id == student_id
        )
        if allocation_round:
            query = query.filter(Allocation.allocation_round == allocation_round)
        return query.order_by(Allocation.allocation_round.desc()).first()
    
    @staticmethod
    def get_course_allocations(
        db: Session,
        course_id: int,
        allocation_round: int = None
    ) -> List[Allocation]:
        """Get all allocations for a course."""
        query = db.query(Allocation).filter(
            Allocation.course_id == course_id,
            Allocation.status == AllocationStatus.ALLOCATED
        )
        if allocation_round:
            query = query.filter(Allocation.allocation_round == allocation_round)
        return query.all()
    
    @staticmethod
    def get_batch_allocations(
        db: Session,
        batch_id: int,
        allocation_round: int = None
    ) -> List[Allocation]:
        """Get all allocations for a batch."""
        students = db.query(Student).filter(
            Student.batch_id == batch_id
        ).all()
        student_ids = [s.id for s in students]
        
        query = db.query(Allocation).filter(
            Allocation.student_id.in_(student_ids)
        )
        if allocation_round:
            query = query.filter(Allocation.allocation_round == allocation_round)
        return query.all()
    
    @staticmethod
    def get_unallocated_students(
        db: Session,
        batch_id: int,
        allocation_round: int = None
    ) -> List[Student]:
        """Get students who were not allocated any course."""
        # Get all students in batch
        students = db.query(Student).filter(
            Student.batch_id == batch_id
        ).all()
        
        unallocated = []
        for student in students:
            allocation = db.query(Allocation).filter(
                Allocation.student_id == student.id,
                Allocation.status == AllocationStatus.ALLOCATED
            )
            if allocation_round:
                allocation = allocation.filter(
                    Allocation.allocation_round == allocation_round
                )
            if not allocation.first():
                unallocated.append(student)
        
        return unallocated
    
    @staticmethod
    def get_waitlisted_students(
        db: Session,
        course_id: int = None,
        batch_id: int = None,
        allocation_round: int = None
    ) -> List[Allocation]:
        """Get waitlisted allocations."""
        query = db.query(Allocation).filter(
            Allocation.status == AllocationStatus.WAITLISTED
        )
        
        if course_id:
            query = query.filter(Allocation.course_id == course_id)
        
        if batch_id:
            students = db.query(Student).filter(
                Student.batch_id == batch_id
            ).all()
            student_ids = [s.id for s in students]
            query = query.filter(Allocation.student_id.in_(student_ids))
        
        if allocation_round:
            query = query.filter(Allocation.allocation_round == allocation_round)
        
        return query.all()
    
    @staticmethod
    def generate_allocation_report(
        db: Session,
        batch_id: int,
        allocation_round: int = 1
    ) -> Dict:
        """Generate a comprehensive allocation report."""
        students = db.query(Student).filter(
            Student.batch_id == batch_id
        ).all()
        
        report = {
            "batch_id": batch_id,
            "allocation_round": allocation_round,
            "total_students": len(students),
            "summary": {
                "allocated": 0,
                "waitlisted": 0,
                "no_preference": 0
            },
            "by_category": {},
            "by_course": {},
            "by_preference": {1: 0, 2: 0, 3: 0, "4+": 0}
        }
        
        for student in students:
            allocation = AllocationService.get_student_allocation(
                db, student.id, allocation_round
            )
            
            category = student.reservation_category.value
            if category not in report["by_category"]:
                report["by_category"][category] = {"allocated": 0, "waitlisted": 0, "none": 0}
            
            if not allocation:
                report["summary"]["no_preference"] += 1
                report["by_category"][category]["none"] += 1
            elif allocation.status == AllocationStatus.ALLOCATED:
                report["summary"]["allocated"] += 1
                report["by_category"][category]["allocated"] += 1
                
                # Track by course
                course_id = allocation.course_id
                if course_id not in report["by_course"]:
                    course = db.query(Course).filter(Course.id == course_id).first()
                    report["by_course"][course_id] = {
                        "name": course.name if course else "Unknown",
                        "code": course.code if course else "N/A",
                        "count": 0
                    }
                report["by_course"][course_id]["count"] += 1
                
                # Track by preference number
                pref_num = allocation.preference_number
                if pref_num and pref_num <= 3:
                    report["by_preference"][pref_num] += 1
                else:
                    report["by_preference"]["4+"] += 1
            else:
                report["summary"]["waitlisted"] += 1
                report["by_category"][category]["waitlisted"] += 1
        
        return report

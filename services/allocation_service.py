"""
Allocation Service - Core allocation engine for course selection.
Implements merit + preference + reservation based allocation.
"""
from sqlalchemy.orm import Session
from models import (
    Student, Course, Preference, Allocation, SeatMatrix,
    AllocationStatus, ReservationCategory, CoursePool, Batch
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

    # ============================================
    # TRANSPARENCY METHODS
    # ============================================

    @staticmethod
    def generate_transparency_data(
        db: Session,
        batch_id: int,
        allocation_round: int = 1
    ) -> Dict:
        """
        Generate full transparency data for a batch allocation.
        Returns merit list with ranks, course cutoffs, and summary stats.
        """
        # Get all students in batch sorted by merit
        students = db.query(Student).filter(
            Student.batch_id == batch_id
        ).order_by(Student.qualifying_marks.desc()).all()

        if not students:
            return {"merit_list": [], "course_cutoffs": [], "summary": {}}

        # Build merit list with tied ranks
        merit_list = []
        current_rank = 1
        for i, student in enumerate(students):
            # Tied rank: if marks equal to previous student, share rank
            if i > 0 and student.qualifying_marks == students[i - 1].qualifying_marks:
                rank = merit_list[i - 1]["merit_rank"]
            else:
                rank = i + 1

            # Get preferences
            prefs = db.query(Preference).filter(
                Preference.student_id == student.id
            ).order_by(Preference.priority).all()

            pref_list = []
            for p in prefs:
                course = db.query(Course).filter(Course.id == p.course_id).first()
                pref_list.append({
                    "priority": p.priority,
                    "course_code": course.code if course else "N/A",
                    "course_name": course.name if course else "N/A",
                })

            # Get allocation
            allocation = db.query(Allocation).filter(
                Allocation.student_id == student.id,
                Allocation.allocation_round == allocation_round
            ).first()

            if allocation:
                alloc_course = db.query(Course).filter(Course.id == allocation.course_id).first()
                alloc_status = allocation.status.value
                alloc_course_code = alloc_course.code if alloc_course else "N/A"
                alloc_course_name = alloc_course.name if alloc_course else "N/A"
                alloc_pref_num = allocation.preference_number
            elif not prefs:
                alloc_status = "No Preference"
                alloc_course_code = "-"
                alloc_course_name = "-"
                alloc_pref_num = None
            else:
                alloc_status = "Not Allocated"
                alloc_course_code = "-"
                alloc_course_name = "-"
                alloc_pref_num = None

            merit_list.append({
                "merit_rank": rank,
                "admission_no": student.admission_no,
                "name": student.name,
                "qualifying_marks": student.qualifying_marks,
                "reservation_category": student.reservation_category.value,
                "preferences": pref_list,
                "allocation_status": alloc_status,
                "allocated_course_code": alloc_course_code,
                "allocated_course_name": alloc_course_name,
                "preference_number": alloc_pref_num,
            })

        # Build course cutoffs
        pool_entries = db.query(CoursePool).filter(
            CoursePool.batch_id == batch_id,
            CoursePool.is_active == True
        ).all()

        categories = ["General", "EWS", "OBC", "SC", "ST"]
        course_cutoffs = []

        for entry in pool_entries:
            course = db.query(Course).filter(Course.id == entry.course_id).first()
            if not course:
                continue

            seat_matrix = db.query(SeatMatrix).filter(
                SeatMatrix.course_id == course.id
            ).first()

            # Get allocated students for this course
            allocs = db.query(Allocation).filter(
                Allocation.course_id == course.id,
                Allocation.allocation_round == allocation_round,
                Allocation.status == AllocationStatus.ALLOCATED
            ).all()

            allocated_students = []
            # Group by category for cutoff calculation
            cat_marks = {c: [] for c in categories}
            pref_dist = {1: 0, 2: 0, 3: 0, "4+": 0}

            for a in allocs:
                s = db.query(Student).filter(Student.id == a.student_id).first()
                if not s:
                    continue
                # Find merit rank
                s_rank = next(
                    (m["merit_rank"] for m in merit_list if m["admission_no"] == s.admission_no),
                    None
                )
                allocated_students.append({
                    "merit_rank": s_rank,
                    "admission_no": s.admission_no,
                    "name": s.name,
                    "marks": s.qualifying_marks,
                    "category": s.reservation_category.value,
                    "pref_number": a.preference_number,
                })
                cat_marks[s.reservation_category.value].append(s.qualifying_marks)

                if a.preference_number and a.preference_number <= 3:
                    pref_dist[a.preference_number] += 1
                elif a.preference_number:
                    pref_dist["4+"] += 1

            # Calculate cutoffs per category
            cat_cutoffs = {}
            for cat in categories:
                total = getattr(seat_matrix, f"{cat.lower()}_seats", 0) if seat_matrix else 0
                filled = len(cat_marks[cat])
                if cat_marks[cat]:
                    cutoff = min(cat_marks[cat])
                else:
                    cutoff = "Open"
                cat_cutoffs[cat] = {
                    "seats_total": total,
                    "seats_filled": filled,
                    "cutoff_marks": cutoff,
                }

            total_seats = sum(c["seats_total"] for c in cat_cutoffs.values())
            filled_seats = sum(c["seats_filled"] for c in cat_cutoffs.values())

            course_cutoffs.append({
                "course_code": course.code,
                "course_name": course.name,
                "total_seats": total_seats,
                "filled_seats": filled_seats,
                "category_cutoffs": cat_cutoffs,
                "allocated_students": sorted(allocated_students, key=lambda x: x["merit_rank"] or 999),
                "preference_distribution": pref_dist,
            })

        # Summary stats
        allocated_count = sum(1 for m in merit_list if m["allocation_status"] == "Allocated")
        waitlisted_count = sum(1 for m in merit_list if m["allocation_status"] == "Waitlisted")
        no_pref_count = sum(1 for m in merit_list if m["allocation_status"] == "No Preference")
        total = len(merit_list)

        pref_nums = [m["preference_number"] for m in merit_list if m["preference_number"] is not None]
        first_pref_count = sum(1 for p in pref_nums if p == 1)
        first_pref_rate = round(first_pref_count / allocated_count * 100, 1) if allocated_count > 0 else 0
        avg_pref = round(sum(pref_nums) / len(pref_nums), 2) if pref_nums else 0

        summary = {
            "total_students": total,
            "allocated": allocated_count,
            "waitlisted": waitlisted_count,
            "no_preference": no_pref_count,
            "first_pref_rate": first_pref_rate,
            "avg_pref_fulfilled": avg_pref,
        }

        return {
            "merit_list": merit_list,
            "course_cutoffs": course_cutoffs,
            "summary": summary,
        }

    @staticmethod
    def get_student_transparency_data(
        db: Session,
        student_id: int,
        allocation_round: int = 1
    ) -> Optional[Dict]:
        """
        Get transparency data for a specific student.
        Returns merit rank, preference journey, and anonymized cutoff table.
        """
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.batch_id:
            return None

        batch_id = student.batch_id

        # Calculate merit rank
        students_in_batch = db.query(Student).filter(
            Student.batch_id == batch_id
        ).order_by(Student.qualifying_marks.desc()).all()

        total_students = len(students_in_batch)
        merit_rank = None
        for i, s in enumerate(students_in_batch):
            if i > 0 and s.qualifying_marks == students_in_batch[i - 1].qualifying_marks:
                if s.id == student_id:
                    # Find rank of previous student with same marks
                    for j in range(i - 1, -1, -1):
                        if students_in_batch[j].qualifying_marks != s.qualifying_marks or j == 0:
                            merit_rank = j + 1 if students_in_batch[j].qualifying_marks == s.qualifying_marks else j + 2
                            break
                    break
            else:
                if s.id == student_id:
                    merit_rank = i + 1
                    break

        if merit_rank is None:
            merit_rank = total_students  # fallback

        # Get student's allocation
        allocation = db.query(Allocation).filter(
            Allocation.student_id == student_id,
            Allocation.allocation_round == allocation_round
        ).first()

        # Build preference journey
        preferences = db.query(Preference).filter(
            Preference.student_id == student_id
        ).order_by(Preference.priority).all()

        categories = ["General", "EWS", "OBC", "SC", "ST"]
        student_category = student.reservation_category.value

        journey = []
        allocated_found = False
        for pref in preferences:
            course = db.query(Course).filter(Course.id == pref.course_id).first()
            if not course:
                continue

            # Get all allocated students for this course to compute cutoff
            allocs = db.query(Allocation).filter(
                Allocation.course_id == course.id,
                Allocation.allocation_round == allocation_round,
                Allocation.status == AllocationStatus.ALLOCATED
            ).all()

            # Compute cutoff for student's category
            cat_marks = []
            for a in allocs:
                alloc_student = db.query(Student).filter(Student.id == a.student_id).first()
                if alloc_student and alloc_student.reservation_category.value == student_category:
                    cat_marks.append(alloc_student.qualifying_marks)

            cutoff = min(cat_marks) if cat_marks else None

            # Check seat availability
            seat_matrix = db.query(SeatMatrix).filter(
                SeatMatrix.course_id == course.id
            ).first()

            total_cat_seats = 0
            filled_cat_seats = len(cat_marks)
            if seat_matrix:
                total_cat_seats = getattr(seat_matrix, f"{student_category.lower()}_seats", 0)

            seats_available = total_cat_seats > filled_cat_seats

            # Determine outcome
            if allocation and allocation.course_id == course.id and allocation.status == AllocationStatus.ALLOCATED:
                outcome = "ALLOCATED"
                allocated_found = True
            elif allocated_found:
                outcome = "NOT_REACHED"
            elif not seats_available and cutoff is not None and student.qualifying_marks < cutoff:
                outcome = "SEATS_FULL"
            elif total_cat_seats == 0:
                # Check general seats as fallback
                gen_marks = []
                for a in allocs:
                    alloc_student = db.query(Student).filter(Student.id == a.student_id).first()
                    if alloc_student and alloc_student.reservation_category.value == "General":
                        gen_marks.append(alloc_student.qualifying_marks)
                gen_total = seat_matrix.general_seats if seat_matrix else 0
                if gen_total <= len(gen_marks):
                    outcome = "SEATS_FULL"
                else:
                    outcome = "SEATS_FULL"
            else:
                outcome = "SEATS_FULL"

            journey.append({
                "priority": pref.priority,
                "course_code": course.code,
                "course_name": course.name,
                "cutoff_marks": cutoff if cutoff is not None else "N/A",
                "student_marks": student.qualifying_marks,
                "seats_total": total_cat_seats,
                "seats_filled": filled_cat_seats,
                "outcome": outcome,
            })

        # Build anonymized course cutoff table
        pool_entries = db.query(CoursePool).filter(
            CoursePool.batch_id == batch_id,
            CoursePool.is_active == True
        ).all()

        cutoff_table = []
        for entry in pool_entries:
            course = db.query(Course).filter(Course.id == entry.course_id).first()
            if not course:
                continue

            seat_matrix = db.query(SeatMatrix).filter(
                SeatMatrix.course_id == course.id
            ).first()

            allocs = db.query(Allocation).filter(
                Allocation.course_id == course.id,
                Allocation.allocation_round == allocation_round,
                Allocation.status == AllocationStatus.ALLOCATED
            ).all()

            cat_data = {}
            for cat in categories:
                cat_marks_list = []
                for a in allocs:
                    alloc_student = db.query(Student).filter(Student.id == a.student_id).first()
                    if alloc_student and alloc_student.reservation_category.value == cat:
                        cat_marks_list.append(alloc_student.qualifying_marks)

                total_seats = getattr(seat_matrix, f"{cat.lower()}_seats", 0) if seat_matrix else 0
                filled = len(cat_marks_list)
                cutoff_val = min(cat_marks_list) if cat_marks_list else "Open"

                cat_data[cat] = {
                    "cutoff": cutoff_val,
                    "total": total_seats,
                    "filled": filled,
                }

            total_seats = sum(cat_data[c]["total"] for c in categories)
            filled_seats = sum(cat_data[c]["filled"] for c in categories)

            cutoff_table.append({
                "course_code": course.code,
                "course_name": course.name,
                "total_seats": total_seats,
                "filled_seats": filled_seats,
                "categories": cat_data,
            })

        return {
            "student": {
                "name": student.name,
                "admission_no": student.admission_no,
                "qualifying_marks": student.qualifying_marks,
                "reservation_category": student_category,
                "merit_rank": merit_rank,
                "total_students": total_students,
            },
            "allocation": {
                "course_code": allocation.course.code if allocation and allocation.course else None,
                "course_name": allocation.course.name if allocation and allocation.course else None,
                "status": allocation.status.value if allocation else "No Allocation",
                "preference_number": allocation.preference_number if allocation else None,
            },
            "journey": journey,
            "cutoff_table": cutoff_table,
        }

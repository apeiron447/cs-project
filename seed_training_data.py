"""
Seed script to generate training data for the AI Recommendation Module.

Creates ~200 students with realistic academic profiles, 18 courses,
preferences, and allocations (~300+ samples) for ML model training.

Usage:
    rm course_selection.db
    uv run python seed_training_data.py
"""
import random
from datetime import datetime, date
from werkzeug.security import generate_password_hash

from database import init_db, db_session
from models import (
    Department, Programme, Batch, User, UserRole,
    Student, Teacher, Course, CourseType, SeatMatrix, CoursePool,
    Preference, Allocation, AllocationStatus, ReservationCategory,
    StudentAcademicHistory, StudentSubjectMark, StudentInterest,
)

random.seed(42)

# ── name pools for procedural generation ─────────────────────

FIRST_NAMES = [
    "Aarav", "Diya", "Rohan", "Priya", "Arjun", "Sneha", "Vikram", "Ananya",
    "Karthik", "Meera", "Aditya", "Kavya", "Rahul", "Ishaan", "Lakshmi",
    "Nikhil", "Riya", "Siddharth", "Tanya", "Varun", "Nandini", "Omkar",
    "Pooja", "Sameer", "Trisha", "Uma", "Anurag", "Bhavana", "Chirag", "Deepa",
    "Farhan", "Gauri", "Harsh", "Isha", "Jayesh", "Keerthi", "Luv", "Manya",
    "Naveen", "Oviya", "Pranav", "Ritika", "Shreyas", "Tanvi", "Utkarsh",
    "Vidya", "Yash", "Zara", "Abhay", "Divya", "Gaurav", "Hema", "Kabir",
    "Leela", "Manish", "Neha", "Pallavi", "Raj", "Sania", "Tushar",
]
LAST_NAMES = [
    "Sharma", "Nair", "Menon", "Iyer", "Das", "Pillai", "Raj", "Bose",
    "Reddy", "Thomas", "Kumar", "Nambiar", "Prasad", "Gupta", "Rajan",
    "Joshi", "Singh", "Pai", "Chopra", "Hegde", "Rao", "Patil", "Krishnan",
    "Verma", "Devi", "Mishra", "Mehta", "Suresh", "Khan", "Agarwal",
    "Patel", "Sinha", "Banerjee", "Chatterjee", "Mukherjee", "Sen", "Roy",
    "Ghosh", "Saxena", "Tiwari",
]

DEPT_CODES = ["CSAI", "MAT", "PHY", "ECO", "ENG", "CHE", "BIO", "PSY", "MS", "COM", "CA"]

CATEGORIES = ["General", "General", "General", "General", "OBC", "OBC", "SC", "ST", "EWS"]

INTEREST_POOLS = {
    "CSAI": ["programming", "algorithms", "data science", "machine learning", "web development",
             "databases", "cloud computing", "competitive programming", "networking", "cybersecurity"],
    "CA":   ["programming", "web development", "databases", "mobile apps", "cloud computing"],
    "MAT":  ["mathematics", "statistics", "data science", "algorithms", "linear algebra", "calculus"],
    "PHY":  ["physics", "electronics", "mathematics", "quantum", "circuits", "astrophysics"],
    "ECO":  ["economics", "statistics", "finance", "data science", "mathematics", "econometrics"],
    "ENG":  ["literature", "creative writing", "linguistics", "poetry", "drama"],
    "CHE":  ["chemistry", "biology", "research", "organic chemistry", "materials"],
    "BIO":  ["biology", "genetics", "data science", "research", "chemistry", "ecology"],
    "PSY":  ["psychology", "research", "statistics", "cognitive science", "neuroscience"],
    "MS":   ["management", "marketing", "finance", "entrepreneurship", "accounting"],
    "COM":  ["accounting", "finance", "management", "economics", "business law"],
}

SUBJECTS_FOR_DEPT = {
    "CSAI": ["Programming in C", "Discrete Math", "Data Structures", "OOP with Java",
             "Computer Networks", "Operating Systems", "Software Engineering"],
    "CA":   ["Programming Basics", "Web Tech", "DBMS Fundamentals", "System Analysis"],
    "MAT":  ["Calculus I", "Linear Algebra", "Real Analysis", "Number Theory",
             "Differential Equations", "Abstract Algebra"],
    "PHY":  ["Mechanics", "Thermodynamics", "Optics", "Electromagnetism",
             "Quantum Physics", "Modern Physics"],
    "ECO":  ["Microeconomics I", "Macroeconomics I", "Statistics I", "Indian Economy",
             "Development Economics", "International Trade"],
    "ENG":  ["Poetry", "Prose", "Grammar", "Phonetics", "Drama", "Literary Criticism"],
    "CHE":  ["Inorganic Chemistry", "Physical Chemistry", "Organic Chemistry I",
             "Analytical Chemistry", "Spectroscopy"],
    "BIO":  ["Cell Biology", "Ecology", "Biochemistry I", "Microbiology I",
             "Genetics", "Molecular Biology"],
    "PSY":  ["Intro to Psychology", "Developmental Psych", "Social Psychology",
             "Abnormal Psychology", "Research Methods"],
    "MS":   ["Business Communication", "Accounting I", "Management Principles",
             "Organizational Behavior", "Marketing Basics"],
    "COM":  ["Financial Accounting", "Business Law", "Economics for Commerce",
             "Corporate Accounting", "Cost Accounting"],
}

COURSES_DATA = [
    # (code, name, dept_code, type, capacity, difficulty, tags)
    ("CS201", "Data Structures & Algorithms",   "CSAI", "Minor", 40, 7, "programming,algorithms,data structures"),
    ("CS202", "Machine Learning Fundamentals",  "CSAI", "Minor", 35, 8, "machine learning,data science,programming,statistics"),
    ("CS203", "Web Development",                "CSAI", "MDC",   50, 4, "web development,programming,databases"),
    ("CS204", "Database Management Systems",    "CSAI", "Minor", 40, 6, "databases,programming,data management"),
    ("CS205", "Cloud Computing",                "CSAI", "Minor", 30, 7, "cloud computing,programming,networking"),
    ("MA201", "Linear Algebra",                 "MAT",  "Minor", 45, 6, "mathematics,linear algebra,algorithms"),
    ("MA202", "Probability & Statistics",        "MAT",  "MDC",   50, 5, "statistics,mathematics,data science"),
    ("PH201", "Quantum Mechanics",              "PHY",  "Minor", 30, 9, "physics,mathematics,quantum"),
    ("PH202", "Electronics & Circuits",         "PHY",  "MDC",   40, 6, "electronics,physics,circuits"),
    ("EC201", "Microeconomics",                 "ECO",  "Minor", 45, 5, "economics,finance,statistics"),
    ("EC202", "Econometrics",                   "ECO",  "Minor", 35, 7, "economics,statistics,data science,mathematics"),
    ("EN201", "Creative Writing",               "ENG",  "MDC",   40, 3, "creative writing,literature,linguistics"),
    ("EN202", "Modern Literature",              "ENG",  "Minor", 35, 4, "literature,creative writing,linguistics"),
    ("CH201", "Organic Chemistry",              "CHE",  "Minor", 35, 7, "chemistry,biology,research"),
    ("BI201", "Genetics & Genomics",            "BIO",  "Minor", 30, 8, "genetics,biology,research,data science"),
    ("PS201", "Cognitive Psychology",            "PSY",  "MDC",   40, 5, "psychology,research,statistics"),
    ("MS201", "Principles of Marketing",        "MS",   "MDC",   50, 4, "marketing,management,finance"),
    ("CO201", "Financial Accounting",           "COM",  "MDC",   45, 5, "accounting,finance,management"),
]

NUM_STUDENTS = 200  # generates ~300+ allocation records


# ── helpers ──────────────────────────────────────────────────

def make_user(email, password="pass123"):
    u = User(email=email, password_hash=generate_password_hash(password), role=UserRole.STUDENT)
    db_session.add(u)
    db_session.flush()
    return u


def generate_student_profile(i):
    """Procedurally generate a realistic student profile."""
    dept_code = random.choice(DEPT_CODES)

    # CGPA follows a roughly normal distribution centered around 7.0
    cgpa = round(max(3.5, min(9.8, random.gauss(7.0, 1.2))), 1)

    # Qualifying marks correlate with CGPA but with noise
    qualifying = round(max(35, min(99, cgpa * 10 + random.gauss(0, 5))), 1)

    category = random.choice(CATEGORIES)

    # Pick 2-5 interests from the dept pool, maybe one cross-dept
    dept_interests = INTEREST_POOLS.get(dept_code, ["general"])
    n_interests = random.randint(2, 5)
    interests = random.sample(dept_interests, min(n_interests, len(dept_interests)))
    # 30% chance to pick a cross-discipline interest
    if random.random() < 0.3:
        other_dept = random.choice([d for d in DEPT_CODES if d != dept_code])
        other_pool = INTEREST_POOLS.get(other_dept, [])
        if other_pool:
            interests.append(random.choice(other_pool))

    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"

    return {
        "name": name,
        "dept_code": dept_code,
        "cgpa": cgpa,
        "qualifying": qualifying,
        "category": category,
        "interests": list(set(interests)),  # deduplicate
    }


def seed():
    print("Initialising database...")
    init_db()

    # ── departments & programmes are auto-seeded by init_db ──

    depts = {d.code: d for d in db_session.query(Department).all()}
    progs = {}
    for d in depts.values():
        for p in d.programmes:
            progs.setdefault(d.code, []).append(p)

    # ── create batches ───────────────────────────────────────
    print("Creating batches...")
    batches = {}
    for dept_code in DEPT_CODES:
        prog_list = progs.get(dept_code, [])
        if prog_list:
            prog = prog_list[0]
            b = Batch(programme_id=prog.id, start_year=2024, end_year=2028, current_semester=3)
            db_session.add(b)
            db_session.flush()
            batches[dept_code] = b

    db_session.commit()
    print(f"  Created {len(batches)} batches")

    # ── set department passwords for login ────────────────────
    print("Setting department passwords...")
    dept_password_hash = generate_password_hash("dept123")
    for dept in depts.values():
        dept.password_hash = dept_password_hash
    db_session.commit()
    print(f"  Set password 'dept123' on {len(depts)} departments")

    # ── create teachers (one per dept for assignments) ───────
    print("Creating teachers...")
    teachers = {}
    for i, dept_code in enumerate(["CSAI", "MAT", "PHY", "ECO", "ENG", "CHE", "BIO", "PSY", "MS", "COM"]):
        dept = depts[dept_code]
        tu = User(
            email=f"teacher{i+1}@univ.edu",
            password_hash=generate_password_hash("teach123"),
            role=UserRole.STUDENT,
        )
        db_session.add(tu)
        db_session.flush()
        t = Teacher(
            user_id=tu.id,
            faculty_id=f"FAC{dept_code}{i+1:03d}",
            name=f"Prof. {dept.name.split()[-1]}",
            email=f"teacher{i+1}@univ.edu",
            department_id=dept.id,
        )
        db_session.add(t)
        db_session.flush()
        teachers[dept_code] = t

    db_session.commit()
    print(f"  Created {len(teachers)} teachers")

    # ── create courses ───────────────────────────────────────
    print("Creating courses...")
    courses = {}
    for code, name, dept_code, ctype, cap, diff, tags in COURSES_DATA:
        dept = depts[dept_code]
        teacher = teachers.get(dept_code)
        c = Course(
            code=code,
            name=name,
            course_type=CourseType.MINOR if ctype == "Minor" else CourseType.MDC,
            credits=random.choice([3, 4]),
            department_id=dept.id,
            teacher_id=teacher.id if teacher else None,
            max_capacity=cap,
            reserved_seats_percent=50,
            difficulty_level=diff,
            tags=tags,
        )
        db_session.add(c)
        db_session.flush()

        # seat matrix
        reserved = int(cap * 0.5)
        gen = cap - reserved
        sc = int(reserved * 0.25)
        st = int(reserved * 0.125)
        obc = int(reserved * 0.45)
        ews = reserved - sc - st - obc
        sm = SeatMatrix(
            course_id=c.id,
            general_seats=gen, ews_seats=ews, obc_seats=obc, sc_seats=sc, st_seats=st,
            general_remaining=gen, ews_remaining=ews, obc_remaining=obc, sc_remaining=sc, st_remaining=st,
        )
        db_session.add(sm)
        courses[code] = c

    db_session.commit()
    print(f"  Created {len(courses)} courses with seat matrices")

    # ── add all courses to all batches (course pool) ─────────
    print("Setting up course pools...")
    pool_count = 0
    for b in batches.values():
        for c in courses.values():
            cp = CoursePool(course_id=c.id, batch_id=b.id, is_active=True)
            db_session.add(cp)
            pool_count += 1
    db_session.commit()
    print(f"  Created {pool_count} course-pool entries")

    # ── generate students ────────────────────────────────────
    print(f"Creating {NUM_STUDENTS} students with academic data...")
    students = []
    used_emails = set()

    for i in range(NUM_STUDENTS):
        profile = generate_student_profile(i)
        dept_code = profile["dept_code"]
        dept = depts[dept_code]
        prog_list = progs.get(dept_code, [])
        prog = prog_list[0] if prog_list else list(progs.values())[0][0]
        batch = batches.get(dept_code, list(batches.values())[0])

        # Ensure unique email
        email = f"student{i+1}@univ.edu"
        while email in used_emails:
            email = f"student{i+1}_{random.randint(100,999)}@univ.edu"
        used_emails.add(email)

        user = make_user(email)
        s = Student(
            user_id=user.id,
            admission_no=f"ADM2024{i+1:04d}",
            exam_register_no=f"EXM2024{i+1:04d}",
            roll_no=f"{dept_code}{i+1:04d}",
            name=profile["name"],
            email=email,
            department_id=dept.id,
            programme_id=prog.id,
            batch_id=batch.id,
            admission_year=2024,
            qualifying_marks=profile["qualifying"],
            reservation_category=getattr(ReservationCategory, profile["category"].upper()),
        )
        db_session.add(s)
        db_session.flush()

        cgpa = profile["cgpa"]

        # ── academic history (3 semesters) ───────────────────
        for sem in [1, 2, 3]:
            noise = random.gauss(0, 0.3)
            sem_cgpa = round(max(2.0, min(10.0, cgpa + noise)), 2)
            sem_sgpa = round(max(2.0, min(10.0, sem_cgpa + random.gauss(0, 0.4))), 2)
            ah = StudentAcademicHistory(
                student_id=s.id,
                semester=sem,
                cgpa=sem_cgpa,
                sgpa=sem_sgpa,
                total_marks=round(sem_cgpa * 50 + random.gauss(0, 15), 1),
            )
            db_session.add(ah)

        # ── subject marks (4-7 subjects) ─────────────────────
        dept_subjects = SUBJECTS_FOR_DEPT.get(dept_code, ["General Subject I", "General Subject II"])
        n_subjects = min(random.randint(4, 7), len(dept_subjects))
        for subj in random.sample(dept_subjects, n_subjects):
            base = cgpa * 10
            marks = round(max(15, min(100, base + random.gauss(0, 8))), 1)
            grade_map = {9: "A+", 8: "A", 7: "B+", 6: "B", 5: "C", 4: "D"}
            grade = grade_map.get(int(marks // 10), "C")
            ssm = StudentSubjectMark(
                student_id=s.id,
                subject_name=subj,
                marks_obtained=marks,
                max_marks=100,
                grade=grade,
                semester=random.choice([1, 2, 3]),
            )
            db_session.add(ssm)

        # ── interests ────────────────────────────────────────
        for tag in profile["interests"]:
            si = StudentInterest(student_id=s.id, interest_tag=tag)
            db_session.add(si)

        students.append((s, profile))

        # commit in batches to avoid huge transaction
        if (i + 1) % 50 == 0:
            db_session.commit()
            print(f"    ... {i+1}/{NUM_STUDENTS} students created")

    db_session.commit()
    print(f"  Created {NUM_STUDENTS} students with academic histories, marks & interests")

    # ── create preferences & allocations ─────────────────────
    print("Generating preferences and allocations...")
    course_list = list(courses.values())
    alloc_count = 0
    pref_count = 0

    for s, profile in students:
        s_tags = set(profile["interests"])
        cgpa = profile["cgpa"]

        # only consider courses from other departments (electives)
        other_dept_courses = [c for c in course_list if c.department_id != s.department_id]

        # rank courses by affinity (tag overlap + noise)
        def affinity(c):
            c_tags = set(t.strip() for t in (c.tags or "").split(",") if t.strip())
            overlap = len(s_tags & c_tags)
            return overlap * 3 + random.random()

        ranked = sorted(other_dept_courses, key=affinity, reverse=True)
        n_prefs = random.randint(4, 7)
        chosen = ranked[:n_prefs]

        for priority, c in enumerate(chosen, 1):
            p = Preference(student_id=s.id, course_id=c.id, priority=priority)
            db_session.add(p)
            pref_count += 1

        # ── simulate allocation outcome based on CGPA ────────
        # Strong students get top choices; weaker students get lower or waitlisted
        if cgpa >= 8.5:
            alloc_pref = random.choices([1, 1, 2], weights=[5, 3, 2])[0]
        elif cgpa >= 7.0:
            alloc_pref = random.choices([1, 2, 3], weights=[3, 4, 3])[0]
        elif cgpa >= 5.5:
            alloc_pref = random.choices([2, 3, 4], weights=[3, 4, 3])[0]
        else:
            alloc_pref = random.choices([3, 4, 5], weights=[3, 3, 4])[0]

        alloc_pref = min(alloc_pref, len(chosen))
        alloc_course = chosen[alloc_pref - 1]

        # allocation status
        if cgpa < 4.5 and random.random() < 0.4:
            status = AllocationStatus.WAITLISTED
        elif cgpa < 5.0 and random.random() < 0.2:
            status = AllocationStatus.WAITLISTED
        else:
            status = AllocationStatus.ALLOCATED

        a = Allocation(
            student_id=s.id,
            course_id=alloc_course.id,
            status=status,
            preference_number=alloc_pref,
            allocation_round=1,
        )
        db_session.add(a)
        alloc_count += 1

        # ── add NOT_ALLOCATED records for last 1-2 choices (negative signal) ──
        n_rejects = random.choices([0, 1, 2], weights=[3, 5, 2])[0]
        for j in range(n_rejects):
            reject_idx = len(chosen) - 1 - j
            if reject_idx > alloc_pref - 1:  # don't reject the allocated one
                a2 = Allocation(
                    student_id=s.id,
                    course_id=chosen[reject_idx].id,
                    status=AllocationStatus.NOT_ALLOCATED,
                    preference_number=reject_idx + 1,
                    allocation_round=1,
                )
                db_session.add(a2)
                alloc_count += 1

    db_session.commit()
    print(f"  Created {pref_count} preferences and {alloc_count} allocations")

    # ── summary ──────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"  SEED COMPLETE")
    print(f"{'='*50}")
    print(f"  Students:    {NUM_STUDENTS}")
    print(f"  Courses:     {len(courses)}")
    print(f"  Batches:     {len(batches)}")
    print(f"  Preferences: {pref_count}")
    print(f"  Allocations: {alloc_count}  (training samples for ML)")
    print(f"{'='*50}")
    print()
    print("Next steps:")
    print("  1. uv sync --extra ai          # install scikit-learn etc.")
    print("  2. uv run python app.py         # start server")
    print("  3. Go to /admin/ai-status       # train the model")
    print("  4. Login as admin/adminpass")
    print("  5. Visit /student/dashboard/1   # see recommendations")


if __name__ == "__main__":
    seed()

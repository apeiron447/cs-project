from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flash messages

# Initialize database
from database import init_db, db_session, shutdown_session

# Register shutdown handler
@app.teardown_appcontext
def shutdown_db_session(exception=None):
    shutdown_session(exception)


# ============================================
# AUTHENTICATION
# ============================================

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        from werkzeug.security import check_password_hash
        from models import Student, Teacher
        
        email_or_id = request.form.get("email_or_id", "").strip()
        password = request.form.get("password", "").strip()
        
        # Check admin credentials
        if email_or_id == "admin" and password == "adminpass":
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        
        # Check student by email
        student = db_session.query(Student).filter(Student.email == email_or_id).first()
        if student and student.password_hash:
            if check_password_hash(student.password_hash, password):
                flash(f"Welcome, {student.name}!", "success")
                return redirect(url_for("student_dashboard", student_id=student.id))
        
        # Check student by admission number
        if not student:
            student = db_session.query(Student).filter(Student.admission_no == email_or_id).first()
            if student and student.password_hash:
                if check_password_hash(student.password_hash, password):
                    flash(f"Welcome, {student.name}!", "success")
                    return redirect(url_for("student_dashboard", student_id=student.id))
        
        # Check teacher by email
        teacher = db_session.query(Teacher).filter(Teacher.email == email_or_id).first()
        if teacher and teacher.password_hash:
            if check_password_hash(teacher.password_hash, password):
                flash(f"Welcome, {teacher.name}!", "success")
                return redirect(url_for("teacher_dashboard", teacher_id=teacher.id))
        
        # Check teacher by faculty ID
        if not teacher:
            teacher = db_session.query(Teacher).filter(Teacher.faculty_id == email_or_id).first()
            if teacher and teacher.password_hash:
                if check_password_hash(teacher.password_hash, password):
                    flash(f"Welcome, {teacher.name}!", "success")
                    return redirect(url_for("teacher_dashboard", teacher_id=teacher.id))
        
        flash("Invalid Email/ID or Password.", "error")

    return render_template("login.html")


@app.route("/roles")
def roles():
    return render_template("roles.html")


@app.route("/support")
def support():
    return render_template("support.html")


# ============================================
# PAGE ROUTES
# ============================================

@app.route("/department")
def department_form():
    from services import DepartmentService
    departments = DepartmentService.get_all(db_session)
    return render_template("department.html", departments=departments)


@app.route("/course")
def course_form():
    from services import TeacherService, DepartmentService
    teachers = TeacherService.get_all(db_session)
    departments = DepartmentService.get_all(db_session)
    return render_template("course.html", teachers=teachers, departments=departments)


@app.route("/student")
def student_form():
    from services import DepartmentService, ProgrammeService, BatchService
    departments = DepartmentService.get_all(db_session)
    programmes = ProgrammeService.get_all(db_session)
    batches = BatchService.get_all(db_session)
    return render_template("student.html", 
                          departments=departments,
                          programmes=programmes,
                          batches=batches)


@app.route("/teacher")
def teacher_form():
    from services import DepartmentService
    departments = DepartmentService.get_all(db_session)
    return render_template("teacher.html", departments=departments)


@app.route("/programme", methods=["GET", "POST"])
def programme_form():
    from services import DepartmentService, ProgrammeService
    
    if request.method == "POST":
        department_code = request.form.get("department")
        programme_name = request.form.get("programme_name")
        
        # Find department by code
        department = DepartmentService.get_by_code(db_session, department_code)
        if department:
            try:
                ProgrammeService.create(db_session, programme_name, department.id)
                flash(f"Programme '{programme_name}' added successfully!", "success")
            except Exception as e:
                flash(f"Error creating programme: {str(e)}", "error")
        else:
            flash("Department not found", "error")
        
        return redirect(url_for("programme_form"))
    
    departments = DepartmentService.get_all(db_session)
    return render_template("programme.html", departments=departments)


@app.route("/semester")
def semester_form():
    return render_template("semester.html")


@app.route("/add_batch")
def add_batch_form():
    from services import ProgrammeService
    programmes = ProgrammeService.get_all(db_session)
    return render_template("add_batch.html", programmes=programmes)


@app.route("/save_batch", methods=["POST"])
def save_batch():
    from services import BatchService, ProgrammeService
    
    programme_name = request.form.get("programme")
    start_year = request.form.get("start_year")
    end_year = request.form.get("end_year")
    semester = request.form.get("semester")
    
    # Find programme by name (simplified - in production, use ID)
    programmes = ProgrammeService.get_all(db_session)
    programme = next((p for p in programmes if p.name == programme_name), None)
    
    if programme:
        try:
            # Extract semester number
            sem_num = int(semester.replace("Semester ", "")) if semester else 1
            BatchService.create(
                db_session,
                programme_id=programme.id,
                start_year=int(start_year),
                end_year=int(end_year),
                current_semester=sem_num
            )
            flash("Batch Created Successfully!", "success")
        except Exception as e:
            flash(f"Error creating batch: {str(e)}", "error")
    else:
        flash("Programme not found", "error")
    
    return redirect(url_for("add_batch_form"))


# ============================================
# API ROUTES - DEPARTMENT
# ============================================

@app.route("/api/admin/create-dept", methods=["POST"])
def api_create_department():
    from services import DepartmentService
    
    code = request.form.get("dept_code", "").strip()
    name = request.form.get("dept_name", "").strip()
    head_name = request.form.get("dept_head_name", "").strip()
    
    if not code or not name:
        flash("Department code and name are required", "error")
        return redirect(url_for("department_form"))
    
    try:
        DepartmentService.create(db_session, code, name, head_name)
        flash(f"Department '{name}' created successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("department_form"))


@app.route("/api/departments", methods=["GET"])
def api_get_departments():
    from services import DepartmentService
    departments = DepartmentService.get_all(db_session)
    return jsonify([{
        "id": d.id,
        "code": d.code,
        "name": d.name,
        "head_name": d.head_name
    } for d in departments])


# ============================================
# API ROUTES - PROGRAMME
# ============================================

@app.route("/api/admin/create-programme", methods=["POST"])
def api_create_programme():
    from services import ProgrammeService
    
    data = request.get_json() if request.is_json else request.form
    name = data.get("name", "").strip()
    department_id = data.get("department_id")
    
    if not name or not department_id:
        return jsonify({"error": "Name and department_id required"}), 400
    
    try:
        programme = ProgrammeService.create(db_session, name, int(department_id))
        return jsonify({
            "id": programme.id,
            "name": programme.name,
            "department_id": programme.department_id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/programmes", methods=["GET"])
def api_get_programmes():
    from services import ProgrammeService
    programmes = ProgrammeService.get_all(db_session)
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "department_id": p.department_id,
        "department_name": p.department.name if p.department else None
    } for p in programmes])


# ============================================
# API ROUTES - BATCH
# ============================================

@app.route("/api/batches", methods=["GET"])
def api_get_batches():
    from services import BatchService
    batches = BatchService.get_all(db_session)
    return jsonify([{
        "id": b.id,
        "programme_id": b.programme_id,
        "programme_name": b.programme.name if b.programme else None,
        "start_year": b.start_year,
        "end_year": b.end_year,
        "current_semester": b.current_semester
    } for b in batches])


# ============================================
# API ROUTES - COURSE
# ============================================

@app.route("/api/admin/create-course", methods=["POST"])
def api_create_course():
    from services import CourseService, DepartmentService, TeacherService
    
    code = request.form.get("course_code", "").strip()
    name = request.form.get("course_name", "").strip()
    course_type = request.form.get("course_type", "Minor")
    offering_dept = request.form.get("offering_department", "")
    max_capacity = request.form.get("max_capacity", 0)
    teacher_id = request.form.get("assigned_teacher")
    reserved_percent = request.form.get("reserved_seats_percent", 0)
    
    if not code or not name:
        flash("Course code and name are required", "error")
        return redirect(url_for("course_form"))
    
    # Find department by name
    departments = DepartmentService.get_all(db_session)
    department = next((d for d in departments if d.name == offering_dept), None)
    
    if not department:
        flash("Invalid department", "error")
        return redirect(url_for("course_form"))
    
    try:
        CourseService.create(
            db_session,
            code=code,
            name=name,
            course_type=course_type,
            department_id=department.id,
            max_capacity=int(max_capacity),
            teacher_id=int(teacher_id) if teacher_id else None,
            reserved_seats_percent=float(reserved_percent)
        )
        flash(f"Course '{name}' created successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("course_form"))


@app.route("/api/courses", methods=["GET"])
def api_get_courses():
    from services import CourseService
    courses = CourseService.get_all(db_session)
    return jsonify([{
        "id": c.id,
        "code": c.code,
        "name": c.name,
        "type": c.course_type.value if c.course_type else None,
        "department": c.offering_department.name if c.offering_department else None,
        "teacher": c.teacher.name if c.teacher else None,
        "max_capacity": c.max_capacity
    } for c in courses])


# ============================================
# API ROUTES - STUDENT
# ============================================

@app.route("/api/register/student", methods=["POST"])
def api_register_student():
    from services import StudentService, DepartmentService, ProgrammeService, BatchService
    from datetime import datetime
    
    admission_no = request.form.get("admission_no", "").strip()
    exam_register_no = request.form.get("exam_register_no", "").strip()
    roll_no = request.form.get("roll_no", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    contact_no = request.form.get("contact_no", "").strip()
    parent_department = request.form.get("parent_department", "")
    admission_year = request.form.get("admission_year", "")
    qualifying_mark = request.form.get("qualifying_mark", 0)
    reservation_category = request.form.get("reservation_category", "General")
    dob_str = request.form.get("date_of_birth", "")
    
    if not all([admission_no, name, email, password]):
        flash("Required fields missing", "error")
        return redirect(url_for("student_form"))
    
    # Find department
    departments = DepartmentService.get_all(db_session)
    department = next((d for d in departments if d.name == parent_department), None)
    
    if not department:
        flash("Invalid department", "error")
        return redirect(url_for("student_form"))
    
    # Get first programme and batch for department (simplified)
    programmes = ProgrammeService.get_by_department(db_session, department.id)
    programme = programmes[0] if programmes else None
    
    if not programme:
        flash("No programme found for department", "error")
        return redirect(url_for("student_form"))
    
    batches = BatchService.get_by_programme(db_session, programme.id)
    batch = batches[0] if batches else None
    
    if not batch:
        # Create a default batch
        batch = BatchService.create(
            db_session,
            programme_id=programme.id,
            start_year=int(admission_year) if admission_year else datetime.now().year,
            end_year=int(admission_year) + 4 if admission_year else datetime.now().year + 4
        )
    
    try:
        # Parse date
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
        
        StudentService.create(
            db_session,
            admission_no=admission_no,
            exam_register_no=exam_register_no,
            roll_no=roll_no,
            name=name,
            email=email,
            password=password,
            department_id=department.id,
            programme_id=programme.id,
            batch_id=batch.id,
            admission_year=int(admission_year) if admission_year else datetime.now().year,
            qualifying_marks=float(qualifying_mark),
            reservation_category=reservation_category,
            contact_no=contact_no,
            date_of_birth=dob
        )
        flash(f"Student '{name}' registered successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("student_form"))


@app.route("/api/students", methods=["GET"])
def api_get_students():
    from services import StudentService
    students = StudentService.get_all(db_session)
    return jsonify([{
        "id": s.id,
        "admission_no": s.admission_no,
        "name": s.name,
        "email": s.email,
        "department": s.department.name if s.department else None,
        "programme": s.programme.name if s.programme else None,
        "batch": f"{s.batch.start_year}-{s.batch.end_year}" if s.batch else None,
        "qualifying_marks": s.qualifying_marks,
        "reservation_category": s.reservation_category.value if s.reservation_category else None
    } for s in students])


# ============================================
# API ROUTES - TEACHER
# ============================================

@app.route("/api/register/teacher", methods=["POST"])
def api_register_teacher():
    from services import TeacherService, DepartmentService
    
    faculty_id = request.form.get("faculty_id", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    contact_no = request.form.get("contact_no", "").strip()
    department_name = request.form.get("department", "")
    designation = request.form.get("designation", "AP")
    
    if not all([faculty_id, name, email, password]):
        flash("Required fields missing", "error")
        return redirect(url_for("teacher_form"))
    
    # Find department
    departments = DepartmentService.get_all(db_session)
    department = next((d for d in departments if d.name == department_name), None)
    
    if not department:
        flash("Invalid department", "error")
        return redirect(url_for("teacher_form"))
    
    try:
        TeacherService.create(
            db_session,
            faculty_id=faculty_id,
            name=name,
            email=email,
            password=password,
            department_id=department.id,
            designation=designation,
            contact_no=contact_no
        )
        flash(f"Teacher '{name}' registered successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("teacher_form"))


@app.route("/api/teachers", methods=["GET"])
def api_get_teachers():
    from services import TeacherService
    teachers = TeacherService.get_all(db_session)
    return jsonify([{
        "id": t.id,
        "faculty_id": t.faculty_id,
        "name": t.name,
        "email": t.email,
        "department": t.department.name if t.department else None,
        "designation": t.designation.value if t.designation else None
    } for t in teachers])


# ============================================
# API ROUTES - PREFERENCES
# ============================================

@app.route("/api/preferences", methods=["POST"])
def api_submit_preferences():
    from services import PreferenceService
    
    data = request.get_json()
    student_id = data.get("student_id")
    course_ids = data.get("course_ids", [])  # List of course IDs in priority order
    
    if not student_id or not course_ids:
        return jsonify({"error": "student_id and course_ids required"}), 400
    
    try:
        preferences = PreferenceService.submit_preferences(
            db_session, int(student_id), course_ids
        )
        return jsonify({
            "message": "Preferences submitted successfully",
            "count": len(preferences)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/preferences/<int:student_id>", methods=["GET"])
def api_get_preferences(student_id):
    from services import PreferenceService
    preferences = PreferenceService.get_student_preferences(db_session, student_id)
    return jsonify([{
        "priority": p.priority,
        "course_id": p.course_id,
        "course_code": p.course.code if p.course else None,
        "course_name": p.course.name if p.course else None
    } for p in preferences])


# ============================================
# API ROUTES - ALLOCATION
# ============================================

@app.route("/api/admin/run-allocation", methods=["POST"])
def api_run_allocation():
    from services import AllocationService
    
    data = request.get_json() if request.is_json else request.form
    batch_id = data.get("batch_id")
    allocation_round = data.get("allocation_round", 1)
    
    if not batch_id:
        return jsonify({"error": "batch_id required"}), 400
    
    try:
        result = AllocationService.run_allocation(
            db_session, int(batch_id), int(allocation_round)
        )
        return jsonify({
            "message": "Allocation completed",
            "total_students": result.total_students,
            "allocated": result.allocated_count,
            "waitlisted": result.waitlisted_count,
            "not_allocated": result.not_allocated_count,
            "by_course": result.allocations_by_course,
            "by_category": result.allocations_by_category
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/allocation/report/<int:batch_id>", methods=["GET"])
def api_allocation_report(batch_id):
    from services import AllocationService
    
    allocation_round = request.args.get("round", 1, type=int)
    report = AllocationService.generate_allocation_report(
        db_session, batch_id, allocation_round
    )
    return jsonify(report)


@app.route("/api/allocation/student/<int:student_id>", methods=["GET"])
def api_student_allocation(student_id):
    from services import AllocationService
    
    allocation = AllocationService.get_student_allocation(db_session, student_id)
    if allocation:
        return jsonify({
            "student_id": allocation.student_id,
            "course_id": allocation.course_id,
            "course_code": allocation.course.code if allocation.course else None,
            "course_name": allocation.course.name if allocation.course else None,
            "status": allocation.status.value,
            "preference_number": allocation.preference_number
        })
    return jsonify({"message": "No allocation found"}), 404


# ============================================
# COURSE POOL MANAGEMENT
# ============================================

@app.route("/api/admin/course-pool", methods=["POST"])
def api_add_to_course_pool():
    from services import CourseService
    
    data = request.get_json()
    course_id = data.get("course_id")
    batch_id = data.get("batch_id")
    
    if not course_id or not batch_id:
        return jsonify({"error": "course_id and batch_id required"}), 400
    
    try:
        pool_entry = CourseService.add_to_pool(
            db_session, int(course_id), int(batch_id)
        )
        return jsonify({
            "message": "Course added to pool",
            "pool_id": pool_entry.id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/course-pool/<int:batch_id>", methods=["GET"])
def api_get_course_pool(batch_id):
    from services import CourseService
    courses = CourseService.get_pool_for_batch(db_session, batch_id)
    return jsonify([{
        "id": c.id,
        "code": c.code,
        "name": c.name,
        "type": c.course_type.value if c.course_type else None,
        "max_capacity": c.max_capacity
    } for c in courses])


# ============================================
# DASHBOARD ROUTES
# ============================================

@app.route("/admin/dashboard")
def admin_dashboard():
    from services import DepartmentService, ProgrammeService, StudentService, CourseService, BatchService
    from models import Batch
    
    # Get stats
    stats = {
        "departments": len(DepartmentService.get_all(db_session)),
        "programmes": len(ProgrammeService.get_all(db_session)),
        "students": len(StudentService.get_all(db_session)),
        "courses": len(CourseService.get_all(db_session)),
    }
    
    # Get batches with eager loading
    batches = db_session.query(Batch).all()
    courses = CourseService.get_all(db_session)
    students = StudentService.get_all(db_session)
    
    return render_template("admin_dashboard.html", 
                          stats=stats, 
                          batches=batches, 
                          courses=courses,
                          students=students)


@app.route("/admin/run-allocation", methods=["POST"])
def admin_run_allocation():
    from services import AllocationService
    
    batch_id = request.form.get("batch_id")
    if not batch_id:
        flash("Batch ID required", "error")
        return redirect(url_for("admin_dashboard"))
    
    try:
        result = AllocationService.run_allocation(db_session, int(batch_id))
        flash(f"Allocation complete! {result.allocated_count} allocated, {result.waitlisted_count} waitlisted", "success")
    except Exception as e:
        flash(f"Allocation error: {str(e)}", "error")
    
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add-to-pool", methods=["POST"])
def admin_add_to_pool():
    from services import CourseService
    
    course_id = request.form.get("course_id")
    batch_id = request.form.get("batch_id")
    
    if not course_id or not batch_id:
        flash("Course and batch required", "error")
        return redirect(url_for("admin_dashboard"))
    
    try:
        CourseService.add_to_pool(db_session, int(course_id), int(batch_id))
        flash("Course added to pool successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/remove-from-pool", methods=["POST"])
def admin_remove_from_pool():
    from models import CoursePool
    
    pool_id = request.form.get("pool_id")
    if not pool_id:
        flash("Pool ID required", "error")
        return redirect(url_for("admin_dashboard"))
    
    try:
        pool_entry = db_session.query(CoursePool).filter(CoursePool.id == int(pool_id)).first()
        if pool_entry:
            pool_entry.is_active = False
            db_session.commit()
            flash("Course removed from pool", "success")
        else:
            flash("Pool entry not found", "error")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-batch", methods=["POST"])
def admin_delete_batch():
    from services import BatchService
    
    batch_id = request.form.get("batch_id")
    if not batch_id:
        flash("Batch ID required", "error")
        return redirect(url_for("admin_dashboard"))
    
    try:
        success = BatchService.delete(db_session, int(batch_id))
        if success:
            flash("Batch deleted successfully", "success")
        else:
            flash("Batch not found", "error")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/allocation-report/<int:batch_id>")
def admin_allocation_report(batch_id):
    from services import AllocationService, BatchService
    
    batch = BatchService.get_by_id(db_session, batch_id)
    if not batch:
        flash("Batch not found", "error")
        return redirect(url_for("admin_dashboard"))
    
    report = AllocationService.generate_allocation_report(db_session, batch_id)
    
    return render_template("allocation_report.html", batch=batch, report=report)


@app.route("/student/dashboard/<int:student_id>")
def student_dashboard(student_id):
    from services import StudentService, PreferenceService, CourseService, AllocationService
    
    student = StudentService.get_by_id(db_session, student_id)
    if not student:
        flash("Student not found", "error")
        return redirect(url_for("roles"))
    
    # Get preferences
    preferences = PreferenceService.get_student_preferences(db_session, student_id)
    selected_course_ids = [p.course_id for p in preferences]
    
    # Get available courses for student's batch
    available_courses = CourseService.get_pool_for_batch(db_session, student.batch_id)
    
    # Get allocation result
    allocation = AllocationService.get_student_allocation(db_session, student_id)
    
    return render_template("student_dashboard.html",
                          student=student,
                          preferences=preferences,
                          selected_course_ids=selected_course_ids,
                          available_courses=available_courses,
                          allocation=allocation)


@app.route("/student/submit-preferences", methods=["POST"])
def student_submit_preferences():
    from services import PreferenceService
    
    student_id = request.form.get("student_id")
    course_ids_str = request.form.get("course_ids", "")
    
    if not student_id:
        flash("Student ID required", "error")
        return redirect(url_for("roles"))
    
    # Parse course IDs
    course_ids = [int(x) for x in course_ids_str.split(",") if x.strip()]
    
    if not course_ids:
        flash("Please select at least one course", "error")
        return redirect(url_for("student_dashboard", student_id=student_id))
    
    try:
        PreferenceService.submit_preferences(db_session, int(student_id), course_ids)
        flash(f"Preferences saved successfully! ({len(course_ids)} courses)", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("student_dashboard", student_id=student_id))


@app.route("/teacher/dashboard/<int:teacher_id>")
def teacher_dashboard(teacher_id):
    from services import TeacherService, CourseService
    
    teacher = TeacherService.get_by_id(db_session, teacher_id)
    if not teacher:
        flash("Teacher not found", "error")
        return redirect(url_for("roles"))
    
    # Get courses taught by this teacher
    courses = CourseService.get_by_teacher(db_session, teacher_id)
    
    return render_template("teacher_dashboard.html",
                          teacher=teacher,
                          courses=courses)


# ============================================
# RUN APP
# ============================================

if __name__ == "__main__":
    # Initialize database tables
    init_db()
    app.run(debug=True, port=5001)


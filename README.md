# Choice-Based Course Selection System

A comprehensive web-based course selection platform that enables students to choose their courses based on preferences, academic merit, and reservation policies.

## 🎯 Key Features

- **Choice-Based Allocation**: Students submit preferences, allocation is based on merit + preference order + reservation category
- **Seat Matrix**: Supports category-wise quotas (GEN/OBC/SC/ST/EWS)
- **Multi-Role Access**: Admin, Student, Teacher dashboards
- **Auto-Seeding**: 20 departments + 40 programmes pre-loaded on first run

## 🚀 Quick Start

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and run
git clone https://github.com/apeiron447/cs-project.git
cd cs-project
uv sync
uv run python app.py  # Runs on http://localhost:5001
```

**First run:** Database auto-creates and seeds with departments/programmes.

## 🔑 Demo Credentials

| Role  | Email/ID | Password |
|-------|----------|----------|
| Admin | `admin` | `adminpass` |

## 📁 Project Structure

```
stu/
├── app.py                  # Flask application (38 routes)
├── database.py             # SQLAlchemy config + auto-seeding
├── models.py               # 11 ORM models
├── services/               # Business logic layer
│   ├── allocation_service.py  # Core allocation engine
│   ├── student_service.py
│   ├── course_service.py
│   └── ...
├── templates/
│   ├── admin_dashboard.html   # Run allocation, manage pools
│   ├── student_dashboard.html # Submit preferences
│   ├── teacher_dashboard.html # View allocated students
│   ├── allocation_report.html # Visual reports
│   └── ...
└── static/css/
```

## 📋 Complete Workflow

```
1. SETUP (Auto on first run)
   └── Departments & Programmes seeded

2. ADMIN SETUP
   ├── Create Batches → Add Courses to Pool
   └── Register Students & Teachers

3. STUDENT ACTIONS  
   └── Submit course preferences at /student/dashboard/{id}

4. ADMIN ALLOCATION
   └── Click "Run Allocation" in admin dashboard

5. VIEW RESULTS
   ├── Students: See allotment in dashboard
   ├── Teachers: See allocated students
   └── Admin: View allocation reports
```

## 🛠️ Dashboard URLs

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| **Admin** | `/admin/dashboard` | Run allocation, manage pools |
| **Student** | `/student/dashboard/{id}` | Submit preferences, view results |
| **Teacher** | `/teacher/dashboard/{id}` | View allocated students |
| **Report** | `/admin/allocation-report/{batch_id}` | Allocation statistics |

## ⚙️ Allocation Engine

```python
# Algorithm (in allocation_service.py):
1. Sort students by merit (marks DESC)
2. For each student, try preferences in order
3. Check seat availability by reservation category
4. Allocate or waitlist if no seats
```

**Seat Distribution** (50% reserved example):
- General: 50%, OBC: 22.5%, SC: 12.5%, ST: 6.25%, EWS: 8.75%

## 🗃️ Database Models

| Model | Description |
|-------|-------------|
| `Department` | Academic departments |
| `Programme` | Degree programmes (linked to dept) |
| `Batch` | Student batches with semester |
| `Student` | With marks + reservation category |
| `Teacher` | Faculty with designation |
| `Course` | With seat matrix + course pool |
| `Preference` | Student course preferences |
| `Allocation` | Final course allocations |

## 🔧 Development

```bash
# Add dependencies
uv add <package>

# Run with auto-reload
uv run flask run --reload --port 5001

# Reset database
rm course_selection.db && uv run python app.py
```

## 📋 Features Status

- [x] Database with SQLAlchemy (SQLite)
- [x] Auto-seeding on first run
- [x] Admin Dashboard with allocation controls
- [x] Student preference submission
- [x] Teacher dashboard
- [x] Allocation engine (merit + preference + reservation)
- [x] Visual allocation reports
- [x] AI Recommendation Module
- [ ] Export to Excel/PDF

---

## AI Recommendation Module

The system includes an AI module that predicts course suitability for students. See [docs/ai_module.md](docs/ai_module.md) for details.

- Displays "Highly Recommended", "Good Fit", or "Challenging" badges on the student dashboard
- Uses rule-based heuristics by default, with optional ML model training
- Considers CGPA, subject marks, interests, department affinity, and course difficulty
- Admin can enter academic data at `/admin/student/<id>/academic`
- Model training and status at `/admin/ai-status`

```bash
# Install AI dependencies (optional, for ML model training)
uv sync --extra ai
```

**Tech Stack:** Flask, SQLAlchemy, SQLite, Jinja2

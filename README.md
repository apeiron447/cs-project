# Choice-Based Course Selection System

A comprehensive web-based course selection platform that enables students to choose their courses based on preferences, academic merit, and reservation policies. The system features multi-role access for administrators, students, teachers, and department heads.

## 🎯 Overview

This system implements a **choice-based course allocation** mechanism where:

- Students submit course preferences in priority order
- Allocation is based on **merit (CGPA/Marks)** + **preference order** + **reservation category**
- Supports seat matrix with category-wise quotas (GEN/OBC/SC/ST)
- AI-powered course recommendations (optional module)

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Admin   │ │ Student  │ │ Teacher  │ │    Department    │ │
│  │  Portal  │ │  Portal  │ │  Portal  │ │      Portal      │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                     FLASK BACKEND                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ Authentication  │  │ Course Manager  │  │  Allocation   │ │
│  │    Service      │  │    Service      │  │    Engine     │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      DATABASE                                 │
│  Departments │ Programmes │ Batches │ Courses │ Students     │
└──────────────────────────────────────────────────────────────┘
```

## 👥 User Roles

### 1. Admin Module
- **Master Data Management**: Create/manage Departments, Programmes, Batches, Semesters
- **User Registration**: Register Teachers and Students with credentials
- **Course Management**: Create courses with seat matrices and category quotas
- **Course Pool Creation**: Define which courses are available for choice-based selection
- **Allocation Engine**: Run merit + preference + reservation based allocation
- **Reporting**: Generate allocation reports (course-wise, batch-wise)

### 2. Student Module
- **View Courses**: Browse available courses with details, syllabus, and AI recommendations
- **Submit Preferences**: Select courses in priority order before deadline
- **View Allotment**: Check allocated course or waitlist status

### 3. Department Module
- **Dashboard**: Overview of students and courses in the department
- **View Students**: Filter by Programme/Batch
- **Allocation Reports**: View and export batch-wise allocation data

### 4. Course Teacher Module
- **View Allotted Students**: See list of students assigned to their courses
- **Export Options**: Download/print student lists

## ⚙️ Allocation Engine Logic

```
1. Fetch eligible students (by Programme + Batch)
2. Sort students by merit (CGPA/Marks) in descending order
3. For each student:
   ├─ Retrieve preference list
   ├─ For each preferred course:
   │   ├─ Check seat availability by reservation category
   │   ├─ If available: Allocate → Reduce seat count → Save "Preference X"
   │   └─ Continue to next preference if no seats
   └─ If no seats in any preferred course: Mark as WAITLIST
4. Save all allocations to database
5. Generate reports: course-wise, category-wise, unallocated list
```

## 🤖 AI Recommendation Module (Optional)

- **Data Sources**: Academic history, marks, interests, past outcomes
- **Feature Engineering**: CGPA, subject marks, interest tags
- **Model**: RandomForest / XGBoost for suitability scoring
- **Labels**: 
  - 🟢 **Highly Recommended**
  - 🟡 **Good Fit**
  - 🔴 **Challenging**

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd stu
```

2. **Install uv** (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. **Create virtual environment and install dependencies**

```bash
# Initialize a new project (if pyproject.toml doesn't exist)
uv init

# Add Flask dependency
uv add flask

# Or if you have a requirements.txt
uv pip install -r requirements.txt
```

4. **Run the application**

```bash
# Using uv run (recommended)
uv run python app.py

# Or activate the virtual environment first
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
python app.py
```

5. **Access the application**

Open your browser and navigate to: `http://127.0.0.1:5000`

### Demo Credentials

| Role  | Email/ID                       | Password          |
|-------|--------------------------------|-------------------|
| Admin | `admin`                        | `adminpass`       |
| User  | `agnimithratheyyeth@gmail.com` | `agnimithra230507`|

---

## 📁 Project Structure

```
stu/
├── app.py                 # Main Flask application
├── README.md              # This file
├── static/
│   └── css/
│       ├── style.css      # Global styles
│       └── roles.css      # Role selection page styles
└── templates/
    ├── login.html         # Login page
    ├── roles.html         # Role selection page
    ├── administrator.html # Admin dashboard
    ├── Department.html    # Department management
    ├── programme.html     # Programme form
    ├── add_programme.html # Add programme page
    ├── add_batch.html     # Batch creation form
    ├── course.html        # Course management
    ├── student.html       # Student registration
    ├── teacher.html       # Teacher registration
    └── support.html       # Support/help page
```

---

## 🛠️ Development

### Quick Commands with uv

```bash
# Add a new dependency
uv add <package-name>

# Add development dependency
uv add --dev pytest

# Run with live reload (using Flask debug mode)
uv run python app.py

# Sync dependencies from pyproject.toml
uv sync

# Update all dependencies
uv lock --upgrade
```

### Environment Variables

Create a `.env` file for configuration:

```env
FLASK_SECRET_KEY=your-secret-key
FLASK_DEBUG=True
DATABASE_URL=sqlite:///courses.db
```

---

## 📋 Features Roadmap

- [x] User Authentication (Login/Logout)
- [x] Role-based Access Control
- [x] Admin: Department/Programme/Batch Management
- [x] Admin: Student & Teacher Registration
- [x] Admin: Course Creation
- [ ] Course Pool Management
- [ ] Seat Matrix Configuration
- [ ] Student Preference Submission
- [ ] Allocation Engine Implementation
- [ ] AI Recommendation Module
- [ ] Export Reports (Excel/PDF)
- [ ] Database Integration (SQLAlchemy)

---

## 📝 License

This project is for educational purposes.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

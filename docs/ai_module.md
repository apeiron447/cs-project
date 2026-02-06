# AI Recommendation Module

## Overview

The AI Recommendation Module predicts course suitability for students based on their academic profile, interests, and course characteristics. It displays recommendation labels on the student dashboard to help students make informed course selections.

## How It Works

### Recommendation Labels

Each available course on the student dashboard receives one of three labels:

| Label | Score Range | Badge Color |
|-------|-----------|-------------|
| **Highly Recommended** | 75-100 | Green |
| **Good Fit** | 50-74 | Blue |
| **Challenging** | 0-49 | Orange |

### Data Sources

The module uses the following student and course data:

**Student Features:**
- Latest CGPA (from `StudentAcademicHistory`)
- Average subject marks (from `StudentSubjectMark`)
- Qualifying marks (existing field on `Student`)
- Department and programme
- Interest tags (from `StudentInterest`)

**Course Features:**
- Offering department
- Course type (Minor/MDC)
- Credits
- Difficulty level (1-10 scale, on `Course`)
- Tags (comma-separated, on `Course`)

### Scoring Methods

#### 1. Rule-Based Heuristics (Default)

When no ML model is trained, the system uses a weighted formula:

| Component | Weight | Description |
|-----------|--------|-------------|
| Academic Performance | 40% | Based on CGPA, average marks, or qualifying marks |
| Department Affinity | 20% | Same department = 100, different = 40 |
| Interest Tag Overlap | 25% | Jaccard similarity between student interests and course tags |
| Difficulty Match | 15% | How well course difficulty matches student ability level |

#### 2. ML Model (After Training)

A `RandomForestRegressor` trained on historical allocation data. The model uses a 7-feature vector:
- CGPA, average marks, qualifying marks
- Same department flag, tag overlap ratio
- Course difficulty level, course credits

## Seed Script (Demo / Training Data)

A seed script is provided to populate the database with realistic training data so you can try the full ML pipeline without manually entering records.

```bash
rm course_selection.db
uv run python seed_training_data.py
```

This generates:

| Data | Count | Details |
|------|-------|---------|
| **Students** | 200 | Procedurally generated across 11 departments with gaussian-distributed CGPAs (mean 7.0, std 1.2) |
| **Academic History** | 600 | 3 semesters per student (CGPA, SGPA, total marks) |
| **Subject Marks** | ~1000 | 4-7 department-specific subjects per student |
| **Interest Tags** | ~700 | 2-5 per student, drawn from department interest pools with 30% cross-discipline chance |
| **Courses** | 18 | Across 10 departments with difficulty levels (3-9) and tags |
| **Preferences** | ~1080 | 4-7 per student, biased toward tag-matching courses |
| **Allocations** | ~330 | Training samples — high-CGPA students get top choices, low-CGPA get lower or waitlisted |

The allocation simulation encodes realistic patterns:
- Students with CGPA >= 8.5 usually get their 1st choice
- Students with CGPA 7.0-8.5 get 1st-3rd choice
- Students with CGPA 5.5-7.0 get 2nd-4th choice
- Students below 5.5 get lower choices or are waitlisted
- NOT_ALLOCATED records are added for bottom preferences (negative signal)

After seeding, train the model at `/admin/ai-status`. Expected R² is ~0.5 on this synthetic data. In production with real allocation history, expect higher accuracy.

### Data Size Guidelines

| Samples | R² | Quality |
|---------|-----|---------|
| < 50 | ~0.3 | Unreliable — use rule-based heuristics instead |
| 100-300 | ~0.4-0.5 | Marginal — model learns broad patterns |
| 300-500 | ~0.5-0.6 | Decent — captures tag overlap and CGPA effects |
| 500+ | 0.6+ | Good — benefits from more diverse student profiles |

The rule-based heuristic fallback works immediately with zero training data and produces reasonable recommendations.

## Data Collection

### Adding Academic Data

Admin route: `/admin/student/<id>/academic`

This page allows admins to enter:
1. **Semester records** - CGPA, SGPA, total marks per semester
2. **Subject marks** - Individual subject scores with grades
3. **Interest tags** - Student interest areas (e.g., "programming", "data science")

### Course Configuration

When creating/editing courses, set:
- **Difficulty Level** (1-10): How challenging the course is
- **Tags**: Comma-separated keywords (e.g., "programming,algorithms,data structures")

## Model Training

### Prerequisites

Install AI dependencies:
```bash
uv sync --extra ai
```

### Quick Start with Seed Data

```bash
rm course_selection.db
uv run python seed_training_data.py   # 200 students, ~330 allocations
uv run python app.py                   # start server
# Go to /admin/ai-status → click "Train AI Model"
# Visit /student/dashboard/1 to see recommendations
```

### Training Process

1. Navigate to `/admin/ai-status`
2. Ensure there are at least 5 allocation records (seed script provides ~330)
3. Click "Train AI Model"
4. The model is saved to `ai_model/model.pkl`

### Training Data

Each allocation record becomes one training sample. The target score is derived from the outcome:
- Allocated at preference 1 → target score 100
- Allocated at preference 2 → target score 85
- Allocated at preference 3 → target score 70
- Higher preferences → progressively lower scores
- Waitlisted → target score 40
- Not allocated → target score 20

### Training Metrics

After training, the system reports:
- **R² Score** - Cross-validated prediction accuracy
- **Feature Importances** - Which features matter most
- **Sample Count** - How many data points were used

## Admin Guide

### Quick Setup (from scratch)

1. Register students and add their academic data via `/admin/student/<id>/academic`
2. Create courses with tags and difficulty levels
3. Run allocations to generate training data
4. Train the model at `/admin/ai-status`
5. Students will see recommendations on their dashboard

### Quick Setup (with seed data)

1. `rm course_selection.db && uv run python seed_training_data.py`
2. `uv run python app.py`
3. Visit `/admin/ai-status` and click "Train AI Model"
4. Browse `/student/dashboard/1` through `/student/dashboard/200` to see recommendations

### Recommendations Display

Courses on the student dashboard are automatically:
- Sorted by recommendation score (highest first)
- Labeled with colored badges
- Enhanced with score tooltips on hover

## API Reference

### Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/admin/ai-status` | View model status and training data stats |
| POST | `/admin/train-ai-model` | Trigger model training |
| GET/POST | `/admin/student/<id>/academic` | View/add student academic data |

### Service Methods

```python
from services import RecommendationService

# Score a single student-course pair
result = RecommendationService.compute_suitability_score(db, student_id, course_id)
# Returns: {"score": 82.5, "label": "Highly Recommended"}

# Score multiple courses for a student
recommendations = RecommendationService.get_recommendations_for_student(db, student_id, course_ids)
# Returns: {course_id: {"score": 82.5, "label": "Highly Recommended"}, ...}
```

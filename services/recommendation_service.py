"""
AI Recommendation Service for course suitability scoring.

Computes a suitability score (0-100) for each course based on
student academic profile, interests, and course characteristics.
Uses a trained ML model if available, otherwise falls back to
rule-based heuristics.
"""
import os

from models import (
    Student, Course, StudentAcademicHistory, StudentSubjectMark,
    StudentInterest, Allocation
)


class RecommendationService:
    MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai_model", "model.pkl")

    @staticmethod
    def get_student_features(db, student_id):
        """Collect student features for scoring."""
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return None

        # Latest CGPA from academic history
        latest_history = (
            db.query(StudentAcademicHistory)
            .filter(StudentAcademicHistory.student_id == student_id)
            .order_by(StudentAcademicHistory.semester.desc())
            .first()
        )

        # Average marks from subject marks
        subject_marks = (
            db.query(StudentSubjectMark)
            .filter(StudentSubjectMark.student_id == student_id)
            .all()
        )
        avg_marks = 0.0
        if subject_marks:
            percentages = []
            for sm in subject_marks:
                if sm.max_marks and sm.max_marks > 0 and sm.marks_obtained is not None:
                    percentages.append((sm.marks_obtained / sm.max_marks) * 100)
            avg_marks = sum(percentages) / len(percentages) if percentages else 0.0

        # Interest tags
        interests = (
            db.query(StudentInterest)
            .filter(StudentInterest.student_id == student_id)
            .all()
        )
        interest_tags = [i.interest_tag.lower().strip() for i in interests]

        return {
            "student_id": student_id,
            "cgpa": latest_history.cgpa if latest_history and latest_history.cgpa else 0.0,
            "sgpa": latest_history.sgpa if latest_history and latest_history.sgpa else 0.0,
            "avg_marks": avg_marks,
            "qualifying_marks": student.qualifying_marks or 0.0,
            "department_id": student.department_id,
            "programme_id": student.programme_id,
            "interest_tags": interest_tags,
        }

    @staticmethod
    def get_course_features(db, course_id):
        """Collect course features for scoring."""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return None

        course_tags = []
        if course.tags:
            course_tags = [t.lower().strip() for t in course.tags.split(",") if t.strip()]

        return {
            "course_id": course_id,
            "department_id": course.department_id,
            "course_type": course.course_type.value if course.course_type else "Minor",
            "credits": course.credits or 3,
            "difficulty_level": course.difficulty_level or 5,
            "tags": course_tags,
        }

    @staticmethod
    def compute_suitability_score(db, student_id, course_id):
        """
        Compute suitability score (0-100) for a student-course pair.
        Uses ML model if available, otherwise rule-based heuristics.
        """
        student_features = RecommendationService.get_student_features(db, student_id)
        course_features = RecommendationService.get_course_features(db, course_id)

        if not student_features or not course_features:
            return {"score": 50, "label": "Good Fit"}

        # Try ML model first
        score = RecommendationService._try_ml_prediction(student_features, course_features)
        if score is not None:
            label = RecommendationService.get_recommendation_label(score)
            return {"score": round(score, 1), "label": label}

        # Fallback to rule-based heuristic
        score = RecommendationService._rule_based_score(student_features, course_features)
        label = RecommendationService.get_recommendation_label(score)
        return {"score": round(score, 1), "label": label}

    @staticmethod
    def _try_ml_prediction(student_features, course_features):
        """Attempt prediction using trained ML model. Returns None if unavailable."""
        try:
            if not os.path.exists(RecommendationService.MODEL_PATH):
                return None
            import joblib
            model = joblib.load(RecommendationService.MODEL_PATH)
            feature_vector = RecommendationService._build_feature_vector(
                student_features, course_features
            )
            prediction = model.predict([feature_vector])[0]
            # Model predicts score 0-100
            return max(0, min(100, float(prediction)))
        except Exception:
            return None

    @staticmethod
    def _build_feature_vector(student_features, course_features):
        """Build a numeric feature vector for ML model."""
        same_dept = 1.0 if student_features["department_id"] == course_features["department_id"] else 0.0

        # Tag overlap ratio
        s_tags = set(student_features["interest_tags"])
        c_tags = set(course_features["tags"])
        tag_overlap = len(s_tags & c_tags) / max(len(s_tags | c_tags), 1)

        return [
            student_features["cgpa"],
            student_features["avg_marks"],
            student_features["qualifying_marks"],
            same_dept,
            tag_overlap,
            course_features["difficulty_level"],
            course_features["credits"],
        ]

    @staticmethod
    def _rule_based_score(student_features, course_features):
        """
        Rule-based heuristic scoring (0-100).
        - Academic performance: 40% weight
        - Department affinity: 20% weight
        - Interest tag overlap: 25% weight
        - Difficulty match: 15% weight
        """
        # 1. Academic performance score (40%)
        cgpa = student_features["cgpa"]
        avg_marks = student_features["avg_marks"]
        qualifying = student_features["qualifying_marks"]

        if cgpa > 0:
            acad_score = (cgpa / 10.0) * 100  # CGPA out of 10
        elif avg_marks > 0:
            acad_score = avg_marks  # Already percentage
        else:
            acad_score = qualifying  # Qualifying marks as fallback

        acad_score = min(100, max(0, acad_score))

        # 2. Department affinity (20%)
        same_dept = student_features["department_id"] == course_features["department_id"]
        dept_score = 100 if same_dept else 40

        # 3. Interest tag overlap (25%)
        s_tags = set(student_features["interest_tags"])
        c_tags = set(course_features["tags"])
        if s_tags and c_tags:
            overlap = len(s_tags & c_tags)
            total = len(s_tags | c_tags)
            tag_score = (overlap / total) * 100
        elif not s_tags and not c_tags:
            tag_score = 50  # Neutral when no data
        else:
            tag_score = 30  # Low when mismatch in data availability

        # 4. Difficulty match (15%)
        difficulty = course_features["difficulty_level"]
        if cgpa > 0:
            student_level = cgpa  # 1-10 scale
        elif avg_marks > 0:
            student_level = avg_marks / 10  # Convert percentage to 1-10
        else:
            student_level = qualifying / 10

        diff_gap = abs(student_level - difficulty)
        if diff_gap <= 1:
            diff_score = 100  # Well matched
        elif diff_gap <= 2:
            diff_score = 75
        elif diff_gap <= 3:
            diff_score = 50
        else:
            diff_score = max(0, 100 - diff_gap * 15)

        # Weighted combination
        final_score = (
            acad_score * 0.40
            + dept_score * 0.20
            + tag_score * 0.25
            + diff_score * 0.15
        )

        return max(0, min(100, final_score))

    @staticmethod
    def get_recommendation_label(score):
        """Map score to recommendation label."""
        if score >= 75:
            return "Highly Recommended"
        elif score >= 50:
            return "Good Fit"
        else:
            return "Challenging"

    @staticmethod
    def get_recommendations_for_student(db, student_id, course_ids):
        """
        Batch scoring: compute recommendations for all given courses.
        Returns dict keyed by course_id with {score, label}.
        """
        recommendations = {}
        for course_id in course_ids:
            result = RecommendationService.compute_suitability_score(db, student_id, course_id)
            recommendations[course_id] = result
        return recommendations

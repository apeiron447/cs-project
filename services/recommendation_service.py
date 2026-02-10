"""
AI Recommendation Service for course suitability scoring.

Computes a suitability score (0-100) for each course based on
student academic profile, interests, and course characteristics.
Requires a trained ML model.
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
        Requires a trained ML model.
        """
        student_features = RecommendationService.get_student_features(db, student_id)
        course_features = RecommendationService.get_course_features(db, course_id)

        if not student_features or not course_features:
            return None

        score = RecommendationService._try_ml_prediction(student_features, course_features)
        if score is None:
            return None

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
        # Tag overlap ratio
        s_tags = set(student_features["interest_tags"])
        c_tags = set(course_features["tags"])
        tag_overlap = len(s_tags & c_tags) / max(len(s_tags | c_tags), 1)

        return [
            student_features["cgpa"],
            student_features["avg_marks"],
            student_features["qualifying_marks"],
            tag_overlap,
            course_features["difficulty_level"],
            course_features["credits"],
        ]

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
            if result is not None:
                recommendations[course_id] = result
        return recommendations

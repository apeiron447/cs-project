"""
AI Model Training Module.

Trains a RandomForestRegressor on historical allocation data to predict
course suitability scores. The target variable is derived from allocation
outcomes: lower preference_number = better fit = higher score.
"""
import os

from models import (
    Student, Course, Allocation, AllocationStatus,
    StudentAcademicHistory, StudentSubjectMark, StudentInterest
)
from services.recommendation_service import RecommendationService


MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai_model")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")


def prepare_training_data(db):
    """
    Collect historical allocation data and build feature matrix.

    Each row is a (student, course) pair from past allocations.
    The target score is derived from allocation outcome:
    - Allocated with preference 1 -> score 100
    - Allocated with preference 2 -> score 85
    - Allocated with preference 3 -> score 70
    - Higher preferences -> lower scores
    - Waitlisted -> score 40
    - Not Allocated -> score 20
    """
    allocations = (
        db.query(Allocation)
        .filter(Allocation.status.in_([
            AllocationStatus.ALLOCATED,
            AllocationStatus.WAITLISTED,
            AllocationStatus.NOT_ALLOCATED,
        ]))
        .all()
    )

    if not allocations:
        return None, None

    features = []
    targets = []

    for alloc in allocations:
        student_features = RecommendationService.get_student_features(db, alloc.student_id)
        course_features = RecommendationService.get_course_features(db, alloc.course_id)

        if not student_features or not course_features:
            continue

        feature_vector = RecommendationService._build_feature_vector(
            student_features, course_features
        )

        # Compute target score from allocation outcome
        if alloc.status == AllocationStatus.ALLOCATED:
            pref = alloc.preference_number or 1
            if pref == 1:
                target = 100
            elif pref == 2:
                target = 85
            elif pref == 3:
                target = 70
            else:
                target = max(40, 100 - (pref * 15))
        elif alloc.status == AllocationStatus.WAITLISTED:
            target = 40
        else:
            target = 20

        features.append(feature_vector)
        targets.append(target)

    return features, targets


def train_model(db):
    """
    Train a RandomForestRegressor on historical data.
    Returns dict with training metrics or error info.
    """
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import cross_val_score
        import numpy as np
        import joblib
    except ImportError:
        return {
            "success": False,
            "error": "AI dependencies not installed. Run: uv sync --extra ai",
        }

    features, targets = prepare_training_data(db)

    if not features or len(features) < 5:
        return {
            "success": False,
            "error": f"Not enough training data. Need at least 5 samples, got {len(features) if features else 0}.",
        }

    X = np.array(features)
    y = np.array(targets)

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
    )

    # Cross-validation score
    cv_folds = min(5, len(X))
    if cv_folds >= 2:
        scores = cross_val_score(model, X, y, cv=cv_folds, scoring="r2")
        cv_score = float(np.mean(scores))
    else:
        cv_score = None

    # Train final model on all data
    model.fit(X, y)

    # Feature importances
    feature_names = [
        "cgpa", "avg_marks", "qualifying_marks",
        "same_department", "tag_overlap",
        "difficulty_level", "credits",
    ]
    importances = dict(zip(feature_names, [round(float(v), 4) for v in model.feature_importances_]))

    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return {
        "success": True,
        "samples": len(X),
        "cv_r2_score": round(cv_score, 4) if cv_score is not None else None,
        "feature_importances": importances,
        "model_path": MODEL_PATH,
    }


def load_model():
    """Load the saved model from disk if it exists."""
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        import joblib
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def get_model_status():
    """Check whether a trained model exists and return status info."""
    model_exists = os.path.exists(MODEL_PATH)
    status = {
        "model_trained": model_exists,
        "model_path": MODEL_PATH if model_exists else None,
    }
    if model_exists:
        import datetime
        mtime = os.path.getmtime(MODEL_PATH)
        status["last_trained"] = datetime.datetime.fromtimestamp(mtime).isoformat()
        status["model_size_kb"] = round(os.path.getsize(MODEL_PATH) / 1024, 1)
    return status

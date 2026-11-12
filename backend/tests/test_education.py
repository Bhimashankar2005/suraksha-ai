import pytest
import secrets
from backend.app.core.database import SessionLocal
from backend.app.models.user import User, Role
from backend.app.models.safety_education import Course, Lesson, Quiz
from backend.app.core.security import get_password_hash
from backend.app.api.endpoints.education import (
    list_courses,
    get_course_detail,
    complete_lesson,
    submit_quiz,
    get_user_learning_progress
)
from backend.app.schemas.education import QuizSubmissionRequest

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def test_user(db):
    user_role = db.query(Role).filter(Role.name == "USER").first()
    email = f"student_{secrets.token_hex(4)}@suraksha.gov.in"
    user = User(
        email=email,
        password_hash=get_password_hash("Suraksha@StudentPass2026"),
        role_id=user_role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    # Teardown
    db.delete(user)
    db.commit()

def test_list_courses_catalog(db):
    courses = list_courses(audience=None, db=db, current_user=None)
    assert len(courses) >= 6
    slugs = [c.slug for c in courses]
    assert "upi-digital-payment-safety" in slugs
    assert "phishing-kyc-fraud-prevention" in slugs
    assert "women-cyber-safety-harassment" in slugs
    assert "senior-fraud-pension-safety" in slugs

def test_get_course_detail_and_quiz(db):
    data = get_course_detail(course_slug="upi-digital-payment-safety", db=db, current_user=None)
    assert data.slug == "upi-digital-payment-safety"
    assert len(data.lessons) >= 2
    assert data.quiz is not None
    assert len(data.quiz.questions) == 3

def test_complete_lesson_workflow(test_user, db):
    course = db.query(Course).filter(Course.slug == "upi-digital-payment-safety").first()
    first_lesson = course.lessons[0]

    data = complete_lesson(
        lesson_id=first_lesson.id,
        db=db,
        current_user=test_user
    )
    assert data["status"] == "success"
    assert data["lesson_id"] == first_lesson.id
    assert data["completed_count"] >= 1

def test_submit_quiz_passing(test_user, db):
    course = db.query(Course).filter(Course.slug == "upi-digital-payment-safety").first()
    quiz = course.quizzes[0]

    # Quiz questions for UPI:
    # Q1: correct 0
    # Q2: correct 2
    # Q3: correct 1
    payload = QuizSubmissionRequest(answers={"1": 0, "2": 2, "3": 1})

    data = submit_quiz(
        quiz_id=quiz.id,
        payload=payload,
        db=db,
        current_user=test_user
    )
    assert data.score == 100
    assert data.passed is True
    assert data.correct_count == 3
    assert data.badge_earned is not None
    assert len(data.question_results) == 3

def test_submit_quiz_failing(test_user, db):
    course = db.query(Course).filter(Course.slug == "phishing-kyc-fraud-prevention").first()
    quiz = course.quizzes[0]

    payload = QuizSubmissionRequest(answers={"1": 3, "2": 3, "3": 3})

    data = submit_quiz(
        quiz_id=quiz.id,
        payload=payload,
        db=db,
        current_user=test_user
    )
    assert data.score < 70
    assert data.passed is False

def test_user_learning_progress_aggregates(test_user, db):
    data = get_user_learning_progress(
        db=db,
        current_user=test_user
    )
    assert data.lessons_completed >= 1
    assert data.quizzes_taken >= 1
    assert data.quizzes_passed >= 1
    assert len(data.badges) >= 1

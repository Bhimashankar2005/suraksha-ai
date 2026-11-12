from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_current_user_optional, record_audit_log
from backend.app.models.user import User
from backend.app.models.safety_education import Course, Lesson, Quiz, QuizAttempt, UserProgress
from backend.app.schemas.education import (
    CourseListItem,
    CourseDetail,
    LessonItem,
    QuizDetail,
    QuizQuestionOut,
    QuizSubmissionRequest,
    QuizSubmissionResponse,
    QuizQuestionResult,
    LearningStatsResponse,
    BadgeItem
)

router = APIRouter()

COURSE_BADGE_MAP = {
    "upi-digital-payment-safety": {
        "name": "UPI_GUARDIAN",
        "title": "UPI Fraud Shield",
        "description": "Mastered UPI payment safety and PIN protection rules.",
        "icon": "shield-check"
    },
    "phishing-kyc-fraud-prevention": {
        "name": "PHISHING_DETECTIVE",
        "title": "Phishing & Fake KYC Detective",
        "description": "Excellence in recognizing lookalike domains and rogue APKs.",
        "icon": "search-check"
    },
    "women-cyber-safety-harassment": {
        "name": "CYBER_DEFENDER",
        "title": "Anti-Harassment Advocate",
        "description": "Empowered with digital evidence preservation and legal rights.",
        "icon": "heart-handshake"
    },
    "senior-fraud-pension-safety": {
        "name": "SENIOR_SAFETY_CHAMPION",
        "title": "Senior Safety Champion",
        "description": "Protecting pensions and defeating digital arrest traps.",
        "icon": "user-check"
    },
    "passwords-2fa-account-security": {
        "name": "FORTIFIED_VAULT",
        "title": "Account Fortress Master",
        "description": "Implemented strong passphrases and authenticator app 2FA.",
        "icon": "lock"
    },
    "deepfakes-synthetic-media-awareness": {
        "name": "SYNTHETIC_MEDIA_ANALYST",
        "title": "Deepfake Literacy Analyst",
        "description": "Spotting voice clones, face-swap artifacts, and media provenance.",
        "icon": "video"
    }
}

@router.get("/courses", response_model=List[CourseListItem])
def list_courses(
    audience: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns the catalog of cyber safety awareness courses with user completion status.
    """
    query = db.query(Course)
    if audience:
        query = query.filter(Course.target_audience == audience.upper())

    courses = query.order_by(Course.created_at.asc()).all()

    # Load user progress if logged in
    user_progress_map: Dict[str, UserProgress] = {}
    user_quiz_attempts: Dict[str, List[QuizAttempt]] = {}

    if current_user:
        progress_entries = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()
        for p in progress_entries:
            user_progress_map[p.course_id] = p

        attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).all()
        for a in attempts:
            if a.quiz_id not in user_quiz_attempts:
                user_quiz_attempts[a.quiz_id] = []
            user_quiz_attempts[a.quiz_id].append(a)

    result = []
    for c in courses:
        total_lessons = len(c.lessons)
        progress = user_progress_map.get(c.id)
        completed_lessons_count = len(progress.completed_lessons) if progress and progress.completed_lessons else 0
        is_completed = progress.is_completed if progress else False

        has_quiz = len(c.quizzes) > 0
        quiz_passed = False
        highest_score = None

        if has_quiz and c.quizzes:
            quiz = c.quizzes[0]
            attempts = user_quiz_attempts.get(quiz.id, [])
            if attempts:
                highest_score = max([att.score for att in attempts])
                quiz_passed = any([att.passed for att in attempts])

        result.append(CourseListItem(
            id=c.id,
            slug=c.slug,
            title=c.title,
            description=c.description,
            target_audience=c.target_audience,
            language=c.language,
            total_lessons=total_lessons,
            completed_lessons=completed_lessons_count,
            is_completed=is_completed,
            has_quiz=has_quiz,
            quiz_passed=quiz_passed,
            highest_score=highest_score
        ))

    return result

@router.get("/courses/{course_slug}", response_model=CourseDetail)
def get_course_detail(
    course_slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns full course lessons and interactive quiz for a specific topic.
    """
    course = db.query(Course).filter(Course.slug == course_slug).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cyber safety course not found."
        )

    completed_lesson_ids = set()
    is_course_completed = False
    if current_user:
        prog = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.course_id == course.id
        ).first()
        if prog:
            completed_lesson_ids = set(prog.completed_lessons or [])
            is_course_completed = prog.is_completed

    lesson_items = [
        LessonItem(
            id=l.id,
            order_index=l.order_index,
            title=l.title,
            content=l.content,
            is_completed=(l.id in completed_lesson_ids)
        )
        for l in course.lessons
    ]

    total_lessons = len(lesson_items)
    progress_percentage = round((len(completed_lesson_ids) / total_lessons * 100)) if total_lessons > 0 else 0

    quiz_detail = None
    quiz_passed = False
    if course.quizzes:
        quiz = course.quizzes[0]
        # Map questions without disclosing the correct answer
        q_outs = [
            QuizQuestionOut(
                id=q.get("id", idx + 1),
                question=q["question"],
                options=q["options"]
            )
            for idx, q in enumerate(quiz.questions_data or [])
        ]
        quiz_detail = QuizDetail(
            id=quiz.id,
            title=quiz.title,
            passing_score=quiz.passing_score,
            total_questions=len(q_outs),
            questions=q_outs
        )

        if current_user:
            attempt = db.query(QuizAttempt).filter(
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.passed == True
            ).first()
            if attempt:
                quiz_passed = True

    return CourseDetail(
        id=course.id,
        slug=course.slug,
        title=course.title,
        description=course.description,
        target_audience=course.target_audience,
        language=course.language,
        lessons=lesson_items,
        quiz=quiz_detail,
        progress_percentage=progress_percentage,
        is_completed=is_course_completed,
        quiz_passed=quiz_passed
    )

@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks a lesson as read and completed for the authenticated user.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found."
        )

    course = db.query(Course).filter(Course.id == lesson.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent course not found."
        )

    prog = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.course_id == course.id
    ).first()

    if not prog:
        prog = UserProgress(
            user_id=current_user.id,
            course_id=course.id,
            completed_lessons=[lesson.id],
            is_completed=False
        )
        db.add(prog)
    else:
        existing = list(prog.completed_lessons or [])
        if lesson.id not in existing:
            existing.append(lesson.id)
            prog.completed_lessons = existing

    # Check if all course lessons are completed
    total_course_lessons = len(course.lessons)
    if len(prog.completed_lessons) >= total_course_lessons:
        prog.is_completed = True

    db.commit()

    return {
        "status": "success",
        "lesson_id": lesson.id,
        "course_id": course.id,
        "completed_count": len(prog.completed_lessons),
        "total_lessons": total_course_lessons,
        "course_completed": prog.is_completed
    }

@router.post("/quizzes/{quiz_id}/submit", response_model=QuizSubmissionResponse)
def submit_quiz(
    quiz_id: str,
    payload: QuizSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits answers for a course quiz, calculates real-time score,
    records QuizAttempt in database, and awards badge on passing.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found."
        )

    questions = quiz.questions_data or []
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz has no questions configured."
        )

    total_questions = len(questions)
    correct_count = 0
    results: List[QuizQuestionResult] = []

    for idx, q in enumerate(questions):
        q_id = q.get("id", idx + 1)
        # user can submit with string index or question id
        user_choice = payload.answers.get(str(q_id), payload.answers.get(str(idx)))
        correct_index = q["correct_index"]
        is_correct = (user_choice == correct_index)

        if is_correct:
            correct_count += 1

        results.append(QuizQuestionResult(
            question_id=q_id,
            question=q["question"],
            user_answer_index=user_choice,
            correct_answer_index=correct_index,
            is_correct=is_correct,
            explanation=q.get("explanation", "Review the course lessons for more details.")
        ))

    score = round((correct_count / total_questions) * 100)
    passed = score >= (quiz.passing_score or 70)

    # Record Attempt
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=score,
        passed=passed
    )
    db.add(attempt)

    badge_awarded = None
    if passed and quiz.course:
        badge_meta = COURSE_BADGE_MAP.get(quiz.course.slug)
        if badge_meta:
            badge_awarded = badge_meta["title"]

    db.commit()

    record_audit_log(
        db=db,
        action="QUIZ_SUBMISSION",
        resource_type="QUIZ",
        resource_id=quiz.id,
        details={"score": score, "passed": passed, "correct_count": correct_count},
        user_id=current_user.id
    )

    return QuizSubmissionResponse(
        quiz_id=quiz.id,
        score=score,
        passed=passed,
        passing_score=quiz.passing_score or 70,
        correct_count=correct_count,
        total_questions=total_questions,
        question_results=results,
        badge_earned=badge_awarded
    )

@router.get("/my-progress", response_model=LearningStatsResponse)
def get_user_learning_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns aggregated learning stats, course progress, quiz milestones, and badges.
    """
    progress_records = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()
    courses_enrolled = len(progress_records)
    courses_completed = len([p for p in progress_records if p.is_completed])

    total_lessons_done = 0
    for p in progress_records:
        if p.completed_lessons:
            total_lessons_done += len(p.completed_lessons)

    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).all()
    quizzes_taken = len(quiz_attempts)

    # Find unique passed quizzes
    passed_quiz_ids = {att.quiz_id for att in quiz_attempts if att.passed}
    quizzes_passed = len(passed_quiz_ids)

    # Determine badges earned
    badges: List[BadgeItem] = []
    if passed_quiz_ids:
        passed_quizzes = db.query(Quiz).filter(Quiz.id.in_(passed_quiz_ids)).all()
        for q in passed_quizzes:
            if q.course and q.course.slug in COURSE_BADGE_MAP:
                b = COURSE_BADGE_MAP[q.course.slug]
                badges.append(BadgeItem(
                    name=b["name"],
                    title=b["title"],
                    description=b["description"],
                    icon=b["icon"]
                ))

    return LearningStatsResponse(
        courses_enrolled=courses_enrolled,
        courses_completed=courses_completed,
        lessons_completed=total_lessons_done,
        quizzes_taken=quizzes_taken,
        quizzes_passed=quizzes_passed,
        badges=badges
    )


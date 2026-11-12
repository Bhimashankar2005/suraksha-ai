from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class LessonItem(BaseModel):
    id: str
    order_index: int
    title: str
    content: str
    is_completed: bool = False

class QuizQuestionOut(BaseModel):
    id: int
    question: str
    options: List[str]

class QuizQuestionFull(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_index: int
    explanation: str

class QuizDetail(BaseModel):
    id: str
    title: str
    passing_score: int
    total_questions: int
    questions: List[QuizQuestionOut]

class CourseListItem(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    target_audience: str
    language: str
    total_lessons: int
    completed_lessons: int
    is_completed: bool
    has_quiz: bool
    quiz_passed: bool
    highest_score: Optional[int] = None

class CourseDetail(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    target_audience: str
    language: str
    lessons: List[LessonItem]
    quiz: Optional[QuizDetail] = None
    progress_percentage: int
    is_completed: bool
    quiz_passed: bool

class QuizSubmissionRequest(BaseModel):
    answers: Dict[str, int] = Field(..., description="Map of question index to chosen option index")

class QuizQuestionResult(BaseModel):
    question_id: int
    question: str
    user_answer_index: Optional[int] = None
    correct_answer_index: int
    is_correct: bool
    explanation: str

class QuizSubmissionResponse(BaseModel):
    quiz_id: str
    score: int
    passed: bool
    passing_score: int
    correct_count: int
    total_questions: int
    question_results: List[QuizQuestionResult]
    badge_earned: Optional[str] = None

class BadgeItem(BaseModel):
    name: str
    title: str
    description: str
    icon: str
    earned_at: Optional[str] = None

class LearningStatsResponse(BaseModel):
    courses_enrolled: int
    courses_completed: int
    lessons_completed: int
    quizzes_taken: int
    quizzes_passed: int
    badges: List[BadgeItem]


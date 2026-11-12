"use client";

import React, { useState, useEffect } from "react";
import {
  GraduationCap,
  BookOpen,
  Award,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  ShieldCheck,
  Search,
  Lock,
  ChevronRight,
  Trophy,
  Sparkles,
  Users,
  Clock,
  HeartHandshake,
  UserCheck
} from "lucide-react";
import {
  fetchCourses,
  fetchCourseDetail,
  completeCourseLesson,
  submitCourseQuiz,
  fetchLearningProgress,
  CourseListItem,
  CourseDetail,
  LearningStatsResponse,
  QuizSubmissionResponse
} from "@/lib/api";

export default function CyberAwarenessPage() {
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAudience, setSelectedAudience] = useState<string>("ALL");
  const [stats, setStats] = useState<LearningStatsResponse | null>(null);

  // Active course study modal
  const [activeCourse, setActiveCourse] = useState<CourseDetail | null>(null);
  const [activeLessonIdx, setActiveLessonIdx] = useState<number>(0);
  const [loadingCourse, setLoadingCourse] = useState(false);
  const [completingLesson, setCompletingLesson] = useState(false);

  // Quiz state
  const [quizAnswers, setQuizAnswers] = useState<Record<string, number>>({});
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizResult, setQuizResult] = useState<QuizSubmissionResponse | null>(null);

  useEffect(() => {
    loadCatalog();
    loadProgress();
  }, [selectedAudience]);

  const loadCatalog = async () => {
    try {
      setLoading(true);
      const data = await fetchCourses(selectedAudience === "ALL" ? undefined : selectedAudience);
      setCourses(data);
    } catch {
      // User might be guest
    } finally {
      setLoading(false);
    }
  };

  const loadProgress = async () => {
    try {
      const data = await fetchLearningProgress();
      setStats(data);
    } catch {
      // Guest
    }
  };

  const handleOpenCourse = async (slug: string) => {
    try {
      setLoadingCourse(true);
      setQuizResult(null);
      setQuizAnswers({});
      setActiveLessonIdx(0);
      const detail = await fetchCourseDetail(slug);
      setActiveCourse(detail);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to load course");
    } finally {
      setLoadingCourse(false);
    }
  };

  const handleCompleteCurrentLesson = async () => {
    if (!activeCourse || !activeCourse.lessons[activeLessonIdx]) return;
    const lesson = activeCourse.lessons[activeLessonIdx];

    setCompletingLesson(true);
    try {
      await completeCourseLesson(lesson.id);
      // Reload active course detail & stats
      const updated = await fetchCourseDetail(activeCourse.slug);
      setActiveCourse(updated);
      loadCatalog();
      loadProgress();
      // Move to next lesson if available
      if (activeLessonIdx + 1 < updated.lessons.length) {
        setActiveLessonIdx(activeLessonIdx + 1);
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update lesson completion");
    } finally {
      setCompletingLesson(false);
    }
  };

  const handleOptionSelect = (questionId: number, optionIdx: number) => {
    setQuizAnswers({
      ...quizAnswers,
      [String(questionId)]: optionIdx
    });
  };

  const handleSubmitQuiz = async () => {
    if (!activeCourse?.quiz) return;

    setQuizSubmitting(true);
    try {
      const res = await submitCourseQuiz(activeCourse.quiz.id, quizAnswers);
      setQuizResult(res);
      // Reload stats and course
      loadProgress();
      loadCatalog();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to submit quiz");
    } finally {
      setQuizSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Top Banner & Stats Overview */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-cyan-500 flex items-center justify-center text-slate-950 font-black shrink-0 shadow-lg shadow-amber-500/20">
              <GraduationCap className="w-6 h-6 text-slate-950" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black text-white">
                  Cyber Defense Academy &amp; Public Safety Literacy
                </h1>
                <span className="px-2.5 py-0.5 text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded-full">
                  Module 11
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
                Master digital safety through interactive bite-sized lessons, quizzes, and earned citizen defense badges.
              </p>
            </div>
          </div>
        </div>

        {/* Learning Statistics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-4 border-t border-slate-800">
          <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 block">Enrolled Courses</span>
            <span className="text-lg font-black text-white">{stats?.courses_enrolled ?? 0}</span>
          </div>
          <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 block">Courses Completed</span>
            <span className="text-lg font-black text-emerald-400">{stats?.courses_completed ?? 0}</span>
          </div>
          <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 block">Lessons Read</span>
            <span className="text-lg font-black text-cyan-400">{stats?.lessons_completed ?? 0}</span>
          </div>
          <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 block">Quizzes Passed</span>
            <span className="text-lg font-black text-amber-400">{stats?.quizzes_passed ?? 0}</span>
          </div>
          <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-center col-span-2 sm:col-span-1">
            <span className="text-[11px] text-slate-400 block">Badges Unlocked</span>
            <span className="text-lg font-black text-purple-400">{stats?.badges?.length ?? 0}</span>
          </div>
        </div>

        {/* Badges Shelf */}
        {stats && stats.badges && stats.badges.length > 0 && (
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Trophy className="w-4 h-4 text-amber-400" />
              Your Unlocked Badges:
            </div>
            <div className="flex flex-wrap gap-2.5">
              {stats.badges.map((b, i) => (
                <div
                  key={i}
                  className="px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-500/40 text-purple-200 text-xs font-bold flex items-center gap-2 shadow-sm"
                >
                  <Award className="w-4 h-4 text-purple-400" />
                  <span>{b.title}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Course Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {["ALL", "GENERAL", "SENIORS", "WOMEN", "STUDENTS"].map((aud) => (
            <button
              key={aud}
              type="button"
              onClick={() => setSelectedAudience(aud)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                selectedAudience === aud
                  ? "bg-cyan-500 text-slate-950 border-cyan-400 font-extrabold shadow-md"
                  : "bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700"
              }`}
            >
              {aud === "ALL" ? "All Courses" : aud}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-400 font-semibold">{courses.length} courses available</span>
      </div>

      {/* Course Catalog Grid */}
      {loading ? (
        <div className="text-center py-12 text-slate-500 text-xs">Loading course catalog...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {courses.map((course) => (
            <div
              key={course.id}
              className="bg-slate-900 border border-slate-800 rounded-3xl p-5 flex flex-col justify-between hover:border-slate-700 transition-all shadow-sm space-y-4 group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                    {course.target_audience}
                  </span>
                  {course.is_completed && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Completed
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="font-bold text-sm text-white group-hover:text-cyan-400 transition-colors">
                    {course.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                    {course.description}
                  </p>
                </div>
              </div>

              <div className="space-y-3 pt-3 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                    {course.completed_lessons} / {course.total_lessons} Lessons
                  </span>
                  {course.quiz_passed ? (
                    <span className="text-amber-400 font-bold flex items-center gap-1">
                      <Trophy className="w-3.5 h-3.5" />
                      Passed ({course.highest_score}%)
                    </span>
                  ) : (
                    <span className="text-slate-500">Quiz Pending</span>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => handleOpenCourse(course.slug)}
                  className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-cyan-600 hover:text-white text-slate-200 font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
                >
                  <span>{course.completed_lessons > 0 ? "Continue Course" : "Start Course"}</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Interactive Course Study Modal */}
      {activeCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-3xl w-full p-6 space-y-6 my-8 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                  {activeCourse.target_audience} Module
                </span>
                <h2 className="text-lg sm:text-xl font-black text-white mt-0.5">
                  {activeCourse.title}
                </h2>
                <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-400">
                  <span>Progress: {activeCourse.progress_percentage}%</span>
                  <span>•</span>
                  <span>{activeCourse.lessons.length} Lessons</span>
                </div>
              </div>
              <button
                onClick={() => setActiveCourse(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            {/* Lesson Selector Pills */}
            <div className="flex gap-2 overflow-x-auto pb-1">
              {activeCourse.lessons.map((lesson, idx) => (
                <button
                  key={lesson.id}
                  onClick={() => {
                    setActiveLessonIdx(idx);
                    setQuizResult(null);
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition-colors flex items-center gap-1.5 ${
                    activeLessonIdx === idx
                      ? "bg-cyan-500 text-slate-950 font-extrabold"
                      : lesson.is_completed
                      ? "bg-slate-800 text-emerald-400 border border-emerald-500/30"
                      : "bg-slate-800/80 text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  {lesson.is_completed && <CheckCircle2 className="w-3.5 h-3.5" />}
                  Lesson {idx + 1}
                </button>
              ))}

              {activeCourse.quiz && (
                <button
                  onClick={() => {
                    setActiveLessonIdx(-1); // -1 signifies Quiz view
                  }}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold shrink-0 transition-colors flex items-center gap-1.5 ${
                    activeLessonIdx === -1
                      ? "bg-amber-500 text-slate-950 font-extrabold"
                      : activeCourse.quiz_passed
                      ? "bg-slate-800 text-amber-400 border border-amber-500/40"
                      : "bg-slate-800 text-slate-300"
                  }`}
                >
                  <Trophy className="w-3.5 h-3.5" />
                  Final Quiz
                </button>
              )}
            </div>

            {/* Lesson Reader View */}
            {activeLessonIdx >= 0 && activeCourse.lessons[activeLessonIdx] && (
              <div className="space-y-4">
                <div className="p-5 bg-slate-950 rounded-2xl border border-slate-800 space-y-3">
                  <h3 className="font-black text-white text-base">
                    {activeCourse.lessons[activeLessonIdx].title}
                  </h3>
                  <div className="text-xs sm:text-sm text-slate-200 leading-relaxed space-y-2 whitespace-pre-line font-normal">
                    {activeCourse.lessons[activeLessonIdx].content}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    disabled={activeLessonIdx === 0}
                    onClick={() => setActiveLessonIdx(activeLessonIdx - 1)}
                    className="px-3.5 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold disabled:opacity-40"
                  >
                    Previous Lesson
                  </button>

                  <button
                    type="button"
                    onClick={handleCompleteCurrentLesson}
                    disabled={completingLesson}
                    className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-2 transition-colors shadow-md"
                  >
                    {activeCourse.lessons[activeLessonIdx].is_completed ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                        Completed (Next →)
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        {completingLesson ? "Saving..." : "Mark Completed & Next"}
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Quiz View */}
            {activeLessonIdx === -1 && activeCourse.quiz && (
              <div className="space-y-6">
                <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-950/40 to-slate-900 border border-amber-500/30 flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-sm text-white">{activeCourse.quiz.title}</h3>
                    <p className="text-xs text-slate-300 mt-0.5">
                      Score at least {activeCourse.quiz.passing_score}% to unlock your badge.
                    </p>
                  </div>
                  <Trophy className="w-7 h-7 text-amber-400" />
                </div>

                {/* Questions List */}
                <div className="space-y-4">
                  {activeCourse.quiz.questions.map((q, qIndex) => (
                    <div
                      key={q.id}
                      className="p-4 bg-slate-950 rounded-2xl border border-slate-800 space-y-3"
                    >
                      <div className="font-bold text-xs sm:text-sm text-white">
                        Question {qIndex + 1}: {q.question}
                      </div>

                      <div className="space-y-2">
                        {q.options.map((option, optIdx) => (
                          <label
                            key={optIdx}
                            className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer text-xs transition-colors ${
                              quizAnswers[String(q.id)] === optIdx
                                ? "bg-cyan-950/60 border-cyan-500 text-cyan-200 font-semibold"
                                : "bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
                            }`}
                          >
                            <input
                              type="radio"
                              name={`question_${q.id}`}
                              checked={quizAnswers[String(q.id)] === optIdx}
                              onChange={() => handleOptionSelect(q.id, optIdx)}
                              className="text-cyan-500 focus:ring-cyan-500 bg-slate-950"
                            />
                            <span>{option}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Quiz Result Display */}
                {quizResult && (
                  <div
                    className={`p-5 rounded-2xl border space-y-3 animate-in fade-in ${
                      quizResult.passed
                        ? "bg-emerald-950/60 border-emerald-500 text-emerald-100"
                        : "bg-red-950/60 border-red-500 text-red-100"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {quizResult.passed ? (
                          <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                        ) : (
                          <HelpCircle className="w-6 h-6 text-red-400" />
                        )}
                        <div>
                          <div className="font-black text-base">
                            {quizResult.passed ? "Congratulations! Quiz Passed" : "Quiz Not Passed"}
                          </div>
                          <div className="text-xs opacity-90">
                            Score: {quizResult.score}% ({quizResult.correct_count} of {quizResult.total_questions} correct)
                          </div>
                        </div>
                      </div>

                      {quizResult.badge_earned && (
                        <div className="px-3 py-1 rounded-xl bg-purple-500/20 text-purple-200 border border-purple-500/40 text-xs font-bold flex items-center gap-1.5">
                          <Trophy className="w-4 h-4 text-amber-400" />
                          Badge: {quizResult.badge_earned}
                        </div>
                      )}
                    </div>

                    {/* Explanations Breakdown */}
                    <div className="space-y-2 pt-2 border-t border-slate-800/80">
                      <div className="text-[11px] font-bold uppercase tracking-wider">
                        Review Explanations:
                      </div>
                      {quizResult.question_results.map((r, i) => (
                        <div
                          key={i}
                          className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1"
                        >
                          <div className="flex items-center gap-1.5 font-semibold">
                            <span className={r.is_correct ? "text-emerald-400" : "text-red-400"}>
                              {r.is_correct ? "✓ Correct" : "✕ Incorrect"}
                            </span>
                            <span className="text-slate-300">Q{i + 1}: {r.question}</span>
                          </div>
                          <p className="text-[11px] text-slate-400 pl-4">
                            {r.explanation}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleSubmitQuiz}
                  disabled={quizSubmitting || Object.keys(quizAnswers).length < activeCourse.quiz.questions.length}
                  className="w-full py-3 rounded-2xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black text-sm shadow-lg shadow-amber-500/20 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  <Trophy className="w-4 h-4" />
                  {quizSubmitting ? "Evaluating Answers..." : "Submit Quiz & Get Score"}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


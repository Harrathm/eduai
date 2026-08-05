/**
 * Course API — unified service for courses, chapters, lessons, quizzes.
 * Merges: lms.ts + courses.ts (both had duplicate fetch wrappers)
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface Course {
  id: number;
  uuid: string | null;
  title: string;
  description: string | null;
  short_description: string | null;
  cover_url: string | null;
  thumbnail_url: string | null;
  category: string | null;
  level: string | null;
  language: string | null;
  status: string;
  price_tokens: number;
  price_dt: number;
  is_free: boolean;
  is_published: boolean;
  published_at: string | null;
  teacher_id: number;
  teacher_name: string;
  author_name: string;
  max_students: number | null;
  students_enrolled: number;
  total_chapters: number;
  total_modules: number;
  total_lessons: number;
  total_duration_minutes: number;
  created_at: string | null;
  updated_at: string | null;
  prerequisites: string | null;
  learning_objectives: string | null;
  visibility: string | null;
  enrollment_type: string | null;
  tags: string[] | null;
  slug: string;
  niveau_scolaire?: string;
  matiere?: string;
}

export interface Chapter {
  id: number;
  title: string;
  description: string | null;
  order: number;
  order_index: number;
  lessons: Lesson[];
}

export interface Lesson {
  id: number;
  chapter_id: number;
  title: string;
  description: string | null;
  lesson_type: string;
  content_text: string | null;
  content_html: string | null;
  video_url: string | null;
  video_duration_seconds: number | null;
  video_thumbnail_url: string | null;
  pdf_url: string | null;
  document_url: string | null;
  document_type: string | null;
  image_urls: string[];
  link_url: string | null;
  link_title: string | null;
  order: number;
  duration_minutes: number;
  is_free: boolean;
  is_preview: boolean;
  has_quiz: boolean;
}

export interface SyllabusChapter {
  id: number;
  title: string;
  order_index: number;
  lessons: SyllabusLesson[];
}

export interface SyllabusLesson {
  id: number;
  title: string;
  lesson_type: string;
  duration_minutes: number;
  is_free: boolean;
  status: string;
  has_quiz: boolean;
}

export interface LessonContent extends Lesson {
  quiz?: {
    id: number;
    title: string;
    description?: string;
    time_limit_seconds?: number;
    passing_score_percent: number;
  };
  notes?: Note[];
  bookmarks?: Bookmark[];
}

export interface Note {
  id: number;
  content: string;
  position: number | null;
  created_at: string;
}

export interface Bookmark {
  id: number;
  position_seconds: number;
  note: string | null;
  created_at: string;
}

export interface CourseAnalytics {
  course_id: number;
  course_title: string;
  total_modules: number;
  total_lessons: number;
  total_enrolled: number;
  completion_rate: number;
  total_revenue: number;
}

export interface Quiz {
  id: number;
  title: string;
  description?: string;
  lesson_id?: number;
  time_limit_seconds?: number;
  passing_score_percent: number;
  max_attempts?: number;
}

// ─── Admin Course API ───────────────────────────────────────────────────────

export const courseAdmin = {
  list: (params?: {
    status_filter?: string;
    search?: string;
    category?: string;
    level?: string;
    skip?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.status_filter) sp.set("status_filter", params.status_filter);
    if (params?.search) sp.set("search", params.search);
    if (params?.category) sp.set("category", params.category);
    if (params?.level) sp.set("level", params.level);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<{ total: number; items: Course[] }>(`/api/admin/courses${qs ? `?${qs}` : ""}`);
  },

  get: (id: number) => api.get<Course>(`/api/admin/courses/${id}`),

  create: (data: Partial<Course>) =>
    api.post<Course>("/api/admin/courses", data),

  update: (id: number, data: Partial<Course>) =>
    api.patch<Course>(`/api/admin/courses/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/api/admin/courses/${id}`),

  publish: (id: number, priceTokens = 0, priceDt = 0) =>
    api.post<Course>(
      `/api/admin/courses/${id}/publish?price_tokens=${priceTokens}&price_dt=${priceDt}`
    ),

  unpublish: (id: number) =>
    api.post<Course>(`/api/admin/courses/${id}/unpublish`),

  duplicate: (id: number) =>
    api.post<Course>(`/api/admin/courses/${id}/duplicate`),

  reorder: (id: number, order: number[]) =>
    api.post<void>(`/api/admin/courses/${id}/reorder`, { order }),

  analytics: (id: number) =>
    api.get<CourseAnalytics>(`/api/admin/courses/${id}/analytics`),

  archive: (id: number) =>
    api.post<Course>(`/api/admin/courses/${id}/archive`),

  submitForReview: (id: number) =>
    api.post<{ id: number; pedagogical_status: string }>(
      `/api/admin/courses/${id}/submit-for-review`
    ),

  preview: (id: number) =>
    api.get<any>(`/api/admin/courses/${id}/preview`),
};

// ─── Admin Chapter API ──────────────────────────────────────────────────────

export const chapterAdmin = {
  list: (courseId: number) =>
    api.get<Chapter[]>(`/api/admin/courses/${courseId}/chapters`),

  get: (courseId: number, chapterId: number) =>
    api.get<Chapter>(`/api/admin/courses/${courseId}/chapters/${chapterId}`),

  create: (courseId: number, data: Partial<Chapter>) =>
    api.post<Chapter>(`/api/admin/courses/${courseId}/chapters`, data),

  update: (courseId: number, chapterId: number, data: Partial<Chapter>) =>
    api.patch<Chapter>(`/api/admin/courses/${courseId}/chapters/${chapterId}`, data),

  delete: (courseId: number, chapterId: number) =>
    api.delete<void>(`/api/admin/courses/${courseId}/chapters/${chapterId}`),
};

// ─── Admin Lesson API ───────────────────────────────────────────────────────

export const lessonAdmin = {
  list: (moduleId: number) =>
    api.get<Lesson[]>(`/api/admin/lessons?module_id=${moduleId}`),

  get: (id: number) =>
    api.get<Lesson>(`/api/admin/lessons/${id}`),

  create: (moduleId: number, data: Partial<Lesson>) =>
    api.post<Lesson>(`/api/admin/lessons?module_id=${moduleId}`, data),

  update: (id: number, data: Partial<Lesson>) =>
    api.patch<Lesson>(`/api/admin/lessons/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/api/admin/lessons/${id}`),

  reorder: (order: number[]) =>
    api.post<void>("/api/admin/lessons/reorder", { order }),
};

// ─── Admin Quiz API ─────────────────────────────────────────────────────────

export const quizAdmin = {
  getByLesson: (lessonId: number) =>
    api.get<Quiz>(`/api/admin/quizzes/lesson/${lessonId}`),

  get: (id: number) =>
    api.get<Quiz>(`/api/admin/quizzes/${id}`),

  create: (data: Partial<Quiz>) =>
    api.post<Quiz>("/api/admin/quizzes", data),

  update: (id: number, data: Partial<Quiz>) =>
    api.patch<Quiz>(`/api/admin/quizzes/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/api/admin/quizzes/${id}`),

  addQuestion: (quizId: number, data: any) =>
    api.post(`/api/admin/quizzes/${quizId}/questions`, data),

  updateQuestion: (quizId: number, questionId: number, data: any) =>
    api.patch(`/api/admin/quizzes/${quizId}/questions/${questionId}`, data),

  deleteQuestion: (quizId: number, questionId: number) =>
    api.delete(`/api/admin/quizzes/${quizId}/questions/${questionId}`),

  addOption: (quizId: number, questionId: number, data: any) =>
    api.post(`/api/admin/quizzes/${quizId}/questions/${questionId}/options`, data),

  deleteOption: (quizId: number, questionId: number, optionId: number) =>
    api.delete(`/api/admin/quizzes/${quizId}/questions/${questionId}/options/${optionId}`),
};

// ─── Academy Catalog (student view) ─────────────────────────────────────────

export const courseAcademy = {
  list: () => api.get<Course[]>("/api/academy/courses"),
};

// ─── Learner Course API ─────────────────────────────────────────────────────

export const courseLearner = {
  catalog: (params?: {
    search?: string;
    category?: string;
    level?: string;
    language?: string;
    skip?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.search) sp.set("search", params.search);
    if (params?.category) sp.set("category", params.category);
    if (params?.level) sp.set("level", params.level);
    if (params?.language) sp.set("language", params.language);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<Course[]>(`/api/learner/courses${qs ? `?${qs}` : ""}`);
  },

  get: (id: number) => api.get<Course>(`/api/learner/courses/${id}`),

  syllabus: (id: number) =>
    api.get<SyllabusChapter[]>(`/api/learner/courses/${id}/syllabus`),

  enroll: (courseId: number) =>
    api.post<void>(`/api/learner/courses/${courseId}/enroll`),

  myCourses: () => api.get<Course[]>("/api/learner/my-courses"),

  certificate: (courseId: number) =>
    api.get<any>(`/api/learner/courses/${courseId}/certificate`),

  preview: (courseId: number) =>
    api.get<any>(`/api/learner/courses/${courseId}/preview`),

  purchase: (courseId: number) =>
    api.post<any>(`/api/courses/${courseId}/purchase`),

  refundRequest: (courseId: number, reason: string) =>
    api.post<any>(`/api/courses/${courseId}/refund-request?reason=${encodeURIComponent(reason)}`),
};

// ─── Learner Lesson API ─────────────────────────────────────────────────────

export const lessonLearner = {
  get: (id: number) => api.get<LessonContent>(`/api/learner/lessons/${id}`),

  progress: (lessonId: number, data: {
    video_position_seconds?: number;
    video_completed?: boolean;
    content_completed?: boolean;
    quiz_completed?: boolean;
    quiz_passed?: boolean;
    quiz_score?: number;
  }) => api.post<void>(`/api/learner/lessons/${lessonId}/progress`, data),

  notes: {
    list: (lessonId: number) =>
      api.get<Note[]>(`/api/learner/lessons/${lessonId}/notes`),
    create: (lessonId: number, content: string, position?: number) =>
      api.post<Note>(`/api/learner/lessons/${lessonId}/notes`, { content, position }),
  },

  bookmarks: {
    list: (lessonId: number) =>
      api.get<Bookmark[]>(`/api/learner/lessons/${lessonId}/bookmarks`),
    create: (lessonId: number, positionSeconds: number, note?: string) =>
      api.post<Bookmark>(`/api/learner/lessons/${lessonId}/bookmarks`, {
        position_seconds: positionSeconds,
        note,
      }),
  },
};

// ─── Learner Quiz API ───────────────────────────────────────────────────────

export const quizLearner = {
  start: (quizId: number) =>
    api.post<any>(`/api/learner/quizzes/${quizId}/start`),

  get: (quizId: number) =>
    api.get<any>(`/api/learner/quizzes/${quizId}`),

  submit: (attemptId: number, answers: { question_id: number; selected_option_ids: number[] }[]) =>
    api.post<any>(`/api/learner/quiz-attempts/${attemptId}/submit`, { answers }),

  certificates: () => api.get<any[]>("/api/learner/certificates"),

  certificate: (id: number) => api.get<any>(`/api/learner/certificates/${id}`),
};

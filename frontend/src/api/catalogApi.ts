/**
 * Catalog API — public catalog, enrollment, player.
 * Migrated from catalog.ts — now uses centralized apiClient.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface CatalogCourse {
  id: number;
  title: string;
  slug: string;
  description?: string;
  cover_url?: string;
  category?: string;
  category_cible?: string;
  tag_pack_requis?: string;
  niveau_scolaire?: string;
  level: string;
  language: string;
  is_locked?: boolean;
  is_free: boolean;
  price_tokens: number;
  price_dt: number;
  total_modules: number;
  total_lessons: number;
  total_duration_minutes: number;
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

export interface LessonContent {
  id: number;
  title: string;
  description?: string;
  lesson_type: string;
  content_html?: string;
  content_text?: string;
  video_url?: string;
  video_duration_seconds?: number;
  video_thumbnail_url?: string;
  document_url?: string;
  document_type?: string;
  image_urls?: string;
  link_url?: string;
  link_title?: string;
  duration_minutes: number;
  quiz?: {
    id: number;
    title: string;
    description?: string;
    time_limit_seconds?: number;
    passing_score_percent: number;
  };
}

// ─── Catalog ────────────────────────────────────────────────────────────────

export const catalogApi = {
  list: (params?: {
    search?: string;
    category?: string;
    category_cible?: string;
    level?: string;
    language?: string;
    niveau_scolaire?: string;
    skip?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.search) sp.set("search", params.search);
    if (params?.category) sp.set("category", params.category);
    if (params?.category_cible) sp.set("category_cible", params.category_cible);
    if (params?.level) sp.set("level", params.level);
    if (params?.language) sp.set("language", params.language);
    if (params?.niveau_scolaire) sp.set("niveau_scolaire", params.niveau_scolaire);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<CatalogCourse[]>(`/catalog/courses${qs ? `?${qs}` : ""}`);
  },

  get: (slug: string) => api.get<CatalogCourse>(`/catalog/courses/${slug}`),

  categories: () => api.get<string[]>("/catalog/categories"),
};

// ─── Enrollment ─────────────────────────────────────────────────────────────

export const enrollmentApi = {
  enroll: (courseId: number) =>
    api.post<void>(`/api/learner/courses/${courseId}/enroll`),

  myCourses: () => api.get<any[]>("/api/learner/my-courses"),
};

// ─── Player ─────────────────────────────────────────────────────────────────

export const playerApi = {
  syllabus: (courseId: number) =>
    api.get<SyllabusChapter[]>(`/api/learner/courses/${courseId}/syllabus`),

  lesson: (lessonId: number) =>
    api.get<LessonContent>(`/api/learner/lessons/${lessonId}`),

  progress: (lessonId: number, data: {
    video_position_seconds?: number;
    video_completed?: boolean;
    content_completed?: boolean;
    quiz_completed?: boolean;
    quiz_passed?: boolean;
    quiz_score?: number;
  }) =>
    api.post<void>(`/api/learner/lessons/${lessonId}/progress`, data),

  notes: {
    list: (lessonId: number) =>
      api.get<any[]>(`/api/learner/lessons/${lessonId}/notes`),
    create: (lessonId: number, content: string, position?: number) =>
      api.post(`/api/learner/lessons/${lessonId}/notes`, { content, position }),
  },

  bookmarks: {
    list: (lessonId: number) =>
      api.get<any[]>(`/api/learner/lessons/${lessonId}/bookmarks`),
    create: (lessonId: number, positionSeconds: number, note?: string) =>
      api.post(`/api/learner/lessons/${lessonId}/bookmarks`, {
        position_seconds: positionSeconds,
        note,
      }),
  },

  quiz: {
    start: (quizId: number) =>
      api.post<any>(`/api/learner/quizzes/${quizId}/start`),
    get: (quizId: number) =>
      api.get<any>(`/api/learner/quizzes/${quizId}`),
    submit: (attemptId: number, answers: { question_id: number; selected_option_ids: number[] }[]) =>
      api.post<any>(`/api/learner/quiz-attempts/${attemptId}/submit`, { answers }),
  },

  certificate: (courseId: number) =>
    api.get<any>(`/api/learner/courses/${courseId}/certificate`),
};

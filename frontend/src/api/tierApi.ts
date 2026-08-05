/**
 * Tier API — dashboard, daily objective, recommended path, placement tests.
 * Migrated from tier.ts — now uses centralized apiClient.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface DashboardData {
  tier: string;
  user_id: number;
  total_enrolled_courses: number;
  overall_progress_pct: number;
  lessons_completed: number;
  total_lessons: number;
  courses: DashboardCourse[];
  daily_objective: DailyObjective;
  features: TierFeatures;
  encouragement?: string;
  matiere_stats?: Record<string, MatiereStat>;
  suggested_school_courses?: { id: number; title: string; niveau_scolaire: string }[];
}

export interface DashboardCourse {
  id: number;
  title: string;
  niveau_scolaire: string;
  progress_pct: number;
  lessons_completed: number;
  total_lessons: number;
  matiere?: string;
}

export interface DailyObjective {
  tier: string;
  type: string;
  message: string;
  estimated_minutes: number;
  lesson_id?: number;
  lesson_title?: string;
  course_title?: string;
  module_title?: string;
}

export interface TierFeatures {
  ai_access: string;
  placement_test: boolean;
  recommendations: string;
  analytics: boolean;
  school_content?: boolean;
}

export interface MatiereStat {
  total: number;
  completed: number;
  progress_pct: number;
}

export interface RecommendedPath {
  tier: string;
  description: string;
  courses: { id: number; title: string; progress_pct: number; priority: string }[];
  next_step: string;
  weakest_subject?: string;
}

export interface PlacementTest {
  id: number;
  matiere: string;
  niveau: string;
  title: string;
  num_questions: number;
}

// ─── Endpoints ──────────────────────────────────────────────────────────────

export const tierApi = {
  dashboard: () => api.get<DashboardData>("/api/learner/dashboard"),

  dailyObjective: () => api.get<DailyObjective>("/api/learner/daily-objective"),

  recommendedPath: () => api.get<RecommendedPath>("/api/learner/recommended-path"),

  placementTests: (params?: { matiere?: string; niveau?: string }) => {
    const sp = new URLSearchParams();
    if (params?.matiere) sp.set("matiere", params.matiere);
    if (params?.niveau) sp.set("niveau", params.niveau);
    const qs = sp.toString();
    return api.get<PlacementTest[]>(`/api/placement/tests${qs ? `?${qs}` : ""}`);
  },

  submitPlacementTest: (testId: number, answers: { question_index: number; selected: string }[]) =>
    api.post(`/api/placement/tests/${testId}/submit`, { answers }),
};

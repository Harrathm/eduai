const API_URL = "";

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem("token");
  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

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

export const tierAPI = {
  dashboard: () => fetchAPI("/api/learner/dashboard"),
  dailyObjective: () => fetchAPI("/api/learner/daily-objective"),
  recommendedPath: () => fetchAPI("/api/learner/recommended-path"),
  placementTests: (params?: { matiere?: string; niveau?: string }) => {
    const sp = new URLSearchParams();
    if (params?.matiere) sp.set("matiere", params.matiere);
    if (params?.niveau) sp.set("niveau", params.niveau);
    return fetchAPI(`/api/placement/tests${sp.toString() ? `?${sp}` : ""}`);
  },
  submitPlacementTest: (testId: number, answers: { question_index: number; selected: string }[]) =>
    fetchAPI(`/api/placement/tests/${testId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),
};

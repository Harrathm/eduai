// Learner API - Catalog and Player

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

// ===== CATALOG =====

export interface CatalogCourse {
  id: number;
  title: string;
  slug: string;
  description?: string;
  cover_url?: string;
  category?: string;
  level: string;
  language: string;
  is_free: boolean;
  price_tokens: number;
  price_dt: number;
  total_modules: number;
  total_lessons: number;
  total_duration_minutes: number;
}

export const catalogAPI = {
  list: (params?: {
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
    return fetchAPI(`/catalog/courses${sp.toString() ? `?${sp}` : ""}`);
  },

  get: (slug: string) => fetchAPI(`/catalog/courses/${slug}`),
  categories: () => fetchAPI("/catalog/categories"),
};

// ===== ENROLLMENT =====

export const enrollmentAPI = {
  enroll: (courseId: number) => 
    fetchAPI(`/api/learner/courses/${courseId}/enroll`, { method: "POST" }),
  
  myCourses: () => fetchAPI("/api/learner/my-courses"),
};

// ===== PLAYER =====

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

export const playerAPI = {
  syllabus: (courseId: number) => fetchAPI(`/api/learner/courses/${courseId}/syllabus`),
  
  lesson: (lessonId: number) => fetchAPI(`/api/learner/lessons/${lessonId}`),
  
  progress: (lessonId: number, data: {
    video_position_seconds?: number;
    video_completed?: boolean;
    content_completed?: boolean;
    quiz_completed?: boolean;
    quiz_passed?: boolean;
    quiz_score?: number;
  }) => 
    fetchAPI(`/api/learner/lessons/${lessonId}/progress`, { 
      method: "POST", 
      body: JSON.stringify(data) 
    }),
  
  // Notes
  notes: {
    list: (lessonId: number) => fetchAPI(`/api/learner/lessons/${lessonId}/notes`),
    create: (lessonId: number, content: string, position?: number) => 
      fetchAPI(`/api/learner/lessons/${lessonId}/notes`, { 
        method: "POST", 
        body: JSON.stringify({ content, position }) 
      }),
  },
  
  // Bookmarks
  bookmarks: {
    list: (lessonId: number) => fetchAPI(`/api/learner/lessons/${lessonId}/bookmarks`),
    create: (lessonId: number, positionSeconds: number, note?: string) => 
      fetchAPI(`/api/learner/lessons/${lessonId}/bookmarks`, { 
        method: "POST", 
        body: JSON.stringify({ position_seconds: positionSeconds, note }) 
      }),
  },
  
  // Quiz
  quiz: {
    start: (quizId: number) => fetchAPI(`/api/learner/quizzes/${quizId}/start`, { method: "POST" }),
    get: (quizId: number) => fetchAPI(`/api/learner/quizzes/${quizId}`),
    submit: (attemptId: number, answers: { question_id: number; selected_option_ids: number[] }[]) => 
      fetchAPI(`/api/learner/quiz-attempts/${attemptId}/submit`, { 
        method: "POST", 
        body: JSON.stringify({ answers }) 
      }),
  },
  
  // Certificate
  certificate: (courseId: number) => fetchAPI(`/api/learner/courses/${courseId}/certificate`),
};
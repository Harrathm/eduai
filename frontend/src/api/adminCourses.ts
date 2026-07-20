// Admin Courses API - using existing endpoints

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

export interface Course {
  id: number;
  title: string;
  description?: string;
  cover_url?: string;
  category?: string;
  level: string;
  status: string;
  price_tokens: number;
  price_dt: number;
  total_chapters: number;
  total_lessons: number;
}

export interface Chapter {
  id: number;
  title: string;
  description?: string;
  order: number;
  lessons: Lesson[];
}

export interface Lesson {
  id: number;
  title: string;
  description?: string;
  lesson_type: string;
  order: number;
  duration_minutes: number;
  is_free: boolean;
  is_preview: boolean;
}

export const adminCoursesAPI = {
  list: () => fetchAPI("/api/admin/courses"),
  
  get: (id: number) => fetchAPI(`/api/admin/courses/${id}`),
  
  create: (data: Partial<Course>) => 
    fetchAPI("/api/admin/courses", { method: "POST", body: JSON.stringify(data) }),
  
  update: (id: number, data: Partial<Course>) => 
    fetchAPI(`/api/admin/courses/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  
  delete: (id: number) => 
    fetchAPI(`/api/admin/courses/${id}`, { method: "DELETE" }),
  
  publish: (id: number) => 
    fetchAPI(`/api/admin/courses/${id}/publish`, { method: "POST" }),
  
  unpublish: (id: number) => 
    fetchAPI(`/api/admin/courses/${id}/unpublish`, { method: "POST" }),
};

export const adminChaptersAPI = {
  create: (courseId: number, data: Partial<Chapter>) => 
    fetchAPI(`/api/admin/courses/${courseId}/chapters`, { method: "POST", body: JSON.stringify(data) }),
  
  update: (id: number, data: Partial<Chapter>) => 
    fetchAPI(`/api/admin/chapters/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  
  delete: (id: number) => 
    fetchAPI(`/api/admin/chapters/${id}`, { method: "DELETE" }),
};

export const adminLessonsAPI = {
  create: (chapterId: number, data: Partial<Lesson>) => 
    fetchAPI(`/api/admin/lessons?module_id=${chapterId}`, { method: "POST", body: JSON.stringify(data) }),
  
  get: (id: number) => fetchAPI(`/api/admin/lessons/${id}`),
  
  update: (id: number, data: Partial<Lesson>) => 
    fetchAPI(`/api/admin/lessons/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  
  delete: (id: number) => 
    fetchAPI(`/api/admin/lessons/${id}`, { method: "DELETE" }),
};
import { tokenStorage } from "../utils/tokenStorage";

const API_URL = import.meta.env.VITE_API_URL || "";

function getToken() {
  return tokenStorage.getToken();
}

async function request(endpoint: string, options: RequestInit = {}) {
  const token = getToken();
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
    throw new Error(err.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

export const coursesAdmin = {
  list: (status?: string) =>
    request(`/api/admin/courses${status ? `?status_filter=${status}` : ""}`),

  get: (id: number) =>
    request(`/api/admin/courses/${id}`),

  create: (data: any) =>
    request("/api/admin/courses", { method: "POST", body: JSON.stringify(data) }),

  update: (id: number, data: any) =>
    request(`/api/admin/courses/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  delete: (id: number) =>
    request(`/api/admin/courses/${id}`, { method: "DELETE" }),

  publish: (id: number, price_tokens = 0, price_dt = 0) =>
    request(`/api/admin/courses/${id}/publish?price_tokens=${price_tokens}&price_dt=${price_dt}`, { method: "POST" }),

  unpublish: (id: number) =>
    request(`/api/admin/courses/${id}/unpublish`, { method: "POST" }),

  duplicate: (id: number) =>
    request(`/api/admin/courses/${id}/duplicate`, { method: "POST" }),
};

export const chaptersAdmin = {
  list: (courseId: number) =>
    request(`/api/admin/courses/${courseId}/chapters`),

  create: (courseId: number, data: any) =>
    request(`/api/admin/courses/${courseId}/chapters`, { method: "POST", body: JSON.stringify(data) }),

  update: (id: number, data: any) =>
    request(`/api/admin/chapters/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  delete: (id: number) =>
    request(`/api/admin/chapters/${id}`, { method: "DELETE" }),
};

export const lessonsAdmin = {
  list: (moduleId: number) =>
    request(`/api/admin/lessons?module_id=${moduleId}`),

  create: (moduleId: number, data: any) =>
    request(`/api/admin/lessons?module_id=${moduleId}`, { method: "POST", body: JSON.stringify(data) }),

  update: (id: number, data: any) =>
    request(`/api/admin/lessons/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  delete: (id: number) =>
    request(`/api/admin/lessons/${id}`, { method: "DELETE" }),
};

export const learnerEndpoints = {
  previewCourse: (courseId: number) =>
    request(`/api/learner/courses/${courseId}/preview`),
};

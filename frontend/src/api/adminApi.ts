/**
 * Admin API — analytics, settings, logs, broadcast, transactions.
 * Extracted from features/admin/api/index.ts — admin-specific endpoints only.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface AdminDashboardStats {
  total_users: number;
  total_students: number;
  total_teachers: number;
  total_courses: number;
  pending_courses: number;
  published_courses: number;
  total_revenue: number;
  total_dt_revenue: number;
  total_tokens_sold: number;
  total_transactions: number;
  pending_teacher_registrations: number;
  active_subscriptions: number;
  pending_registrations: number;
}

export interface AuditLog {
  id: number;
  user_id: number;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: number | null;
  details: Record<string, any>;
  ip_address: string;
  created_at: string;
}

export interface PlatformSetting {
  key: string;
  value: string;
  description: string | null;
}

export interface Transaction {
  id: number;
  user_id: number;
  user_email: string;
  type: string;
  amount_dt: number;
  amount_tokens: number;
  description: string | null;
  created_at: string;
}

export interface EnrollmentTrend {
  date: string;
  registrations: number;
}

export interface ApiCostTrend {
  date: string;
  tokens_consumed: number;
  estimated_cost_dt: number;
}

// ─── Dashboard ──────────────────────────────────────────────────────────────

export const adminDashboard = {
  stats: () => api.get<AdminDashboardStats>("/api/admin/dashboard/stats"),
};

// ─── Analytics ──────────────────────────────────────────────────────────────

export const adminAnalytics = {
  overview: () => api.get<any>("/api/admin/analytics/overview"),
  users: () => api.get<any>("/api/admin/analytics/users"),
  courses: () => api.get<any>("/api/admin/analytics/courses"),
  revenue: (period: string = "30d") =>
    api.get<any>(`/api/admin/analytics/revenue?period=${period}`),
  enrollments: (period: string = "30d") =>
    api.get<{ period: string; data: EnrollmentTrend[] }>(
      `/api/admin/analytics/enrollments?period=${period}`
    ),
  apiCosts: (period: string = "30d") =>
    api.get<{ period: string; data: ApiCostTrend[] }>(
      `/api/admin/analytics/api-costs?period=${period}`
    ),
};

// ─── Settings ───────────────────────────────────────────────────────────────

export interface TokenLimits {
  student_free: { monthly: number; daily: number; per_request: number };
  student_premium: { monthly: number; daily: number; per_request: number };
  teacher: { monthly: number; daily: number; per_request: number };
  admin: { monthly: number; daily: number; per_request: number };
  super_admin: { monthly: number; daily: number; per_request: number };
}

export interface ErrorLogResponse {
  total_lines: number;
  lines: string[];
  file: string;
  truncated: boolean;
  error?: string;
}

export const adminSettings = {
  list: () => api.get<PlatformSetting[]>("/api/admin/settings"),

  update: (key: string, value: string) =>
    api.patch<PlatformSetting>("/api/admin/settings", { key, value }),

  apply: (settings: { key: string; value: string; description?: string }[]) =>
    api.post<{ ok: boolean; applied: number; settings: any[] }>("/api/admin/settings/apply", settings),

  getTokenLimits: () =>
    api.get<{ limits: TokenLimits }>("/api/admin/settings/token-limits"),

  updateTokenLimits: (limits: TokenLimits) =>
    api.put<{ ok: boolean; limits: TokenLimits }>("/api/admin/settings/token-limits", limits),

  refreshCache: () =>
    api.post<{ ok: boolean; message: string }>("/api/admin/settings/refresh-cache"),

  testProvider: (provider: string, key?: string, model?: string) =>
    api.post<any>("/api/admin/settings/test-provider", { provider_id: provider, key, model }),
};

// ─── Audit Logs ─────────────────────────────────────────────────────────────

export const adminLogs = {
  list: (params?: { skip?: number; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<AuditLog[]>(`/api/admin/audit-logs${qs ? `?${qs}` : ""}`);
  },

  errors: (params?: { lines?: number; search?: string; level?: string }) => {
    const sp = new URLSearchParams();
    if (params?.lines) sp.set("lines", String(params.lines));
    if (params?.search) sp.set("search", params.search);
    if (params?.level) sp.set("level", params.level);
    const qs = sp.toString();
    return api.get<ErrorLogResponse>(`/api/admin/logs/errors${qs ? `?${qs}` : ""}`);
  },
};

// ─── Broadcast ──────────────────────────────────────────────────────────────

export const adminBroadcast = {
  send: (data: { subject: string; body: string; recipients?: string }) =>
    api.post<any>("/api/admin/broadcast", data),
};

// ─── Transactions ───────────────────────────────────────────────────────────

export const adminTransactions = {
  list: (params?: { skip?: number; limit?: number; type?: string }) => {
    const sp = new URLSearchParams();
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    if (params?.type) sp.set("type", params.type);
    const qs = sp.toString();
    return api.get<Transaction[]>(`/api/admin/transactions${qs ? `?${qs}` : ""}`);
  },
};

// ─── Token Packages ────────────────────────────────────────────────────────

export const adminTokenPackages = {
  list: () => api.get<any[]>("/api/admin/token-packages"),

  create: (data: any) => api.post<any>("/api/admin/token-packages", data),

  update: (id: number, data: any) =>
    api.patch<any>(`/api/admin/token-packages/${id}`, data),

  delete: (id: number) => api.delete<void>(`/api/admin/token-packages/${id}`),
};

// ─── UGC Course Moderation ─────────────────────────────────────────────────

export const adminCourseModeration = {
  list: (status?: string) => {
    const qs = status && status !== "all" ? `?status=${status}` : "";
    return api.get<any[]>(`/api/admin/courses${qs}`);
  },
  setStatus: (courseId: number, status: string) =>
    api.put<any>(`/api/admin/courses/${courseId}/status`, { status }),
  delete: (courseId: number) =>
    api.delete<void>(`/api/admin/courses/${courseId}`),
};

// ─── Teacher Registrations ─────────────────────────────────────────────────

export const adminTeacherRegistrations = {
  list: () => api.get<any[]>("/api/admin/teacher-registrations"),
  approve: (id: number) =>
    api.post<any>(`/api/admin/teacher-registrations/${id}/review?status=approved`),
  reject: (id: number, reason?: string) =>
    api.post<any>(`/api/admin/teacher-registrations/${id}/review?status=rejected&rejection_reason=${encodeURIComponent(reason || "Rejected by admin")}`),
};

// ─── Users All (Financial Hub) ─────────────────────────────────────────────

export const adminUsersAll = {
  list: () => api.get<any[]>("/api/admin/users-all"),
  update: (userId: number, data: { token_balance?: number; dt_balance?: number }) =>
    api.put<any>(`/api/admin/users/${userId}`, data),
};

// ─── School Dashboard ──────────────────────────────────────────────────────

export const adminSchoolDashboard = {
  get: () => api.get<any>("/api/admin/dashboard"),
};

// ─── Pedagogical Admin ─────────────────────────────────────────────────────

export const pedagogicalAdmin = {
  listPending: () => api.get<any[]>("/api/pedagogical/courses/pending"),
  review: (courseId: number, action: "approved_for_b2b" | "needs_revision") =>
    api.put<any>(`/api/pedagogical/courses/${courseId}/review`, { action }),
};

// ─── Pedagogical Lead ──────────────────────────────────────────────────────

export const pedagogicalLead = {
  listPendingCourses: () => api.get<any[]>("/api/pedagogical-lead/courses/pending"),
  getPerformance: () => api.get<any>("/api/pedagogical-lead/performance"),
  reviewLocal: (courseId: number, action: "approve_local" | "reject") =>
    api.put<any>(`/api/pedagogical-lead/courses/${courseId}/review-local`, { action }),
  escalate: (courseId: number) =>
    api.post<any>(`/api/pedagogical-lead/escalate/${courseId}`),
};

// ─── AI Factory (admin) ─────────────────────────────────────────────────────

export const adminAIFactory = {
  generatePlan: (data: any) => api.post<any>("/api/admin/ai-factory/generate-plan", data),
  generateContent: (data: any) => api.post<any>("/api/admin/ai-factory/generate-content", data),
  generateQuiz: (data: any) => api.post<any>("/api/admin/ai-factory/generate-quiz", data),
};

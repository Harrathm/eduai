/**
 * User API — CRUD users (admin), roles, balance, teacher registrations.
 * Extracted from features/admin/api/index.ts (776 lines) — user-specific endpoints only.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  school_id: number | null;
  school_name: string | null;
  is_active: boolean;
  is_approved: boolean | null;
  subscription_plan: string;
  balance_dt: number;
  balance_tokens: number;
  created_at: string;
}

export interface UserListResponse {
  total: number;
  items: User[];
}

// ─── Endpoints ──────────────────────────────────────────────────────────────

export const userApi = {
  list: (params?: {
    role?: string;
    school_id?: number;
    search?: string;
    skip?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.role) sp.set("role", params.role);
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.search) sp.set("search", params.search);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<UserListResponse>(`/api/admin/users${qs ? `?${qs}` : ""}`);
  },

  listAll: (params?: { role?: string; school_id?: number; search?: string }) => {
    const sp = new URLSearchParams();
    if (params?.role) sp.set("role", params.role);
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.search) sp.set("search", params.search);
    const qs = sp.toString();
    return api.get<User[]>(`/api/admin/users/all${qs ? `?${qs}` : ""}`);
  },

  get: (id: number) => api.get<User>(`/api/admin/users/${id}`),

  create: (data: Partial<User> & { password?: string }) =>
    api.post<User>("/api/admin/users", data),

  delete: (id: number) => api.delete<void>(`/api/admin/users/${id}`),

  toggleActive: (id: number) =>
    api.post<User>(`/api/admin/users/${id}/toggle-active`),

  updateBalance: (id: number, data: { amount_dt?: number; amount_tokens?: number; reason: string }) =>
    api.post<User>(`/api/admin/users/${id}/balance`, data),

  changeRole: (id: number, role: string) =>
    api.post<User>(`/api/admin/users/${id}/role`, { role }),

  approve: (id: number) =>
    api.post<User>(`/api/admin/users/${id}/approve`),

  resetPassword: (id: number) =>
    api.post<{ temporary_password: string }>(`/api/admin/users/${id}/reset-password`),

  update: (id: number, data: Partial<User>) =>
    api.patch<User>(`/api/admin/users/${id}`, data),

  // Wallet operations
  addWallet: (id: number, data: { amount_dt: number; amount_tokens: number; reason: string }) =>
    api.post<any>(`/api/admin/users/${id}/wallet/add`, data),

  deductWallet: (id: number, data: { amount_dt: number; amount_tokens: number; reason: string }) =>
    api.post<any>(`/api/admin/users/${id}/wallet/deduct`, data),

  listWallets: (params?: { school_id?: number; role?: string; skip?: number; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.role) sp.set("role", params.role);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<any[]>(`/api/admin/wallets${qs ? `?${qs}` : ""}`);
  },
};

// ─── Teacher Registration API ───────────────────────────────────────────────

export const teacherRegistrationApi = {
  list: (params?: { status?: string; skip?: number; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.status) sp.set("status", params.status);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<any[]>(`/api/admin/teacher-registrations${qs ? `?${qs}` : ""}`);
  },

  approve: (id: number) =>
    api.post<any>(`/api/admin/teacher-registrations/${id}/approve`),

  reject: (id: number, reason?: string) =>
    api.post<any>(`/api/admin/teacher-registrations/${id}/reject`, { reason }),
};

// ─── Backward compat aliases ───────────────────────────────────────────────

export const adminUsers = userApi;

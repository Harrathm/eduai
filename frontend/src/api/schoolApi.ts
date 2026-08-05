/**
 * School API — CRUD schools (admin), invite codes.
 * Extracted from features/admin/api/index.ts.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface School {
  id: number;
  name: string;
  code: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  invite_code: string;
  is_active: boolean;
  created_at: string;
}

// ─── Endpoints ──────────────────────────────────────────────────────────────

export const schoolApi = {
  list: () => api.get<School[]>("/api/admin/schools"),

  get: (id: number) => api.get<School>(`/api/admin/schools/${id}`),

  create: (data: Partial<School>) =>
    api.post<School>("/api/admin/schools", data),

  update: (id: number, data: Partial<School>) =>
    api.patch<School>(`/api/admin/schools/${id}`, data),

  delete: (id: number) => api.delete<void>(`/api/admin/schools/${id}`),

  regenerateInviteCode: (id: number) =>
    api.post<{ invite_code: string }>(`/api/admin/schools/${id}/regenerate-invite-code`),
};

/**
 * Live Sessions API — teacher CRUD, learner listing, join.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export type LiveSessionStatus = "upcoming" | "live" | "ended" | "cancelled";

export interface LiveSession {
  id: number;
  teacher_id: number;
  class_id: number;
  school_id: number;
  title: string;
  description: string | null;
  scheduled_at: string;
  duration_minutes: number;
  status: LiveSessionStatus;
  meeting_url: string | null;
  created_at: string;
  updated_at: string;
  class_name?: string;
}

export interface LiveSessionCreate {
  class_id: number;
  title: string;
  description?: string;
  scheduled_at: string;
  duration_minutes: number;
}

export interface JoinResponse {
  meeting_url: string;
  room_name: string | null;
}

// ─── Teacher API ───────────────────────────────────────────────────────────

export const teacherLiveSessionsApi = {
  list: (status?: string) =>
    api.get<LiveSession[]>("/api/teacher/live-sessions", { params: status ? { status } : {} }),

  create: (data: LiveSessionCreate) =>
    api.post<LiveSession>("/api/teacher/live-sessions", data),

  listByClass: (classId: number) =>
    api.get<LiveSession[]>(`/api/teacher/classes/${classId}/live-sessions`),

  get: (id: number) =>
    api.get<LiveSession>(`/api/teacher/live-sessions/${id}`),

  update: (id: number, data: Partial<LiveSessionCreate>) =>
    api.put<LiveSession>(`/api/teacher/live-sessions/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/api/teacher/live-sessions/${id}`),
};

// ─── Learner API ───────────────────────────────────────────────────────────

export const learnerLiveSessionsApi = {
  list: () =>
    api.get<LiveSession[]>("/api/learner/live-sessions"),

  get: (id: number) =>
    api.get<LiveSession>(`/api/learner/live-sessions/${id}`),
};

// ─── Join ──────────────────────────────────────────────────────────────────

export const liveSessionApi = {
  join: (sessionId: number) =>
    api.post<JoinResponse>(`/api/live-sessions/${sessionId}/join`),

  teacher: teacherLiveSessionsApi,
  learner: learnerLiveSessionsApi,
};

export default liveSessionApi;

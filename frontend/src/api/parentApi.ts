/**
 * Parent API - famille, enfants, wallet, messagerie.
 * Reconstructed to match all methods called by parent pages.
 */

import { api } from "./client";

// --- Types ----------------------------------------------------------------

export interface CompteFamille {
  id: number;
  parent_id: number;
  max_enfants: number;
  rang_famille: number;
}

export interface EnfantFamille {
  eleve_id: number;
  full_name: string;
  email: string;
  rang: number;
  remise_pct: number;
}

export interface DashboardEnfant {
  eleve_id: number;
  full_name: string;
  niveau_scolaire: string;
  dt_balance: number;
  packs_actifs_count: number;
}

export interface ParentDashboardData {
  enfants: DashboardEnfant[];
  total_dt_depense: number;
}

export interface PackActif {
  pack_id: number;
  valid_from: string | null;
  valid_until: string | null;
  amount_paid: number;
  currency: string;
}

export interface SuiviData {
  eleve_id: number;
  full_name: string;
  niveau_scolaire: string | null;
  dt_balance: number;
  packs_actifs: PackActif[];
}

export interface ScoreEntry {
  chapitre_id: number;
  score: number;
  date: string;
}

export interface BadgeEntry {
  badge_id: number;
  nom: string;
  description: string;
  icon_url: string | null;
  couleur: string;
  date_obtention: string;
}

export interface StreakEntry {
  date: string;
  streak_login: boolean;
  streak_quiz: boolean;
  streak_objectif: boolean;
  points_jour: number;
}

export interface ObjectifEntry {
  id: number;
  matiere: string | null;
  horizon: string;
  metric_type: string;
  target_value: number;
  status: string;
  progress_pct: number;
}

export interface ProgressionData {
  eleve_id: number;
  full_name: string;
  niveau_scolaire: string | null;
  scores: ScoreEntry[];
  badges: BadgeEntry[];
  streaks: StreakEntry[];
  objectifs: ObjectifEntry[];
}

export interface ParentMessage {
  id: number;
  sender_id: number;
  sender_name: string;
  subject: string;
  body: string;
  created_at: string;
  is_read: boolean;
}

export interface SendMessagePayload {
  recipient_type: "teacher" | "admin";
  subject: string;
  body: string;
  // M9 FIX — destinataire explicite optionnel (sinon broadcast aux
  // enseignants/admins de l'école).
  recipient_id?: number;
}

export interface SendMessageResult {
  id: number | null;
  sent: number;
  message: string;
}

// --- Famille --------------------------------------------------------------

export const parentFamille = {
  getCompte: () => api.get<CompteFamille>("/api/famille/compte"),
  getEnfants: () => api.get<{ items?: EnfantFamille[]; enfants?: EnfantFamille[] }>("/api/famille/enfants"),
};

// --- Enfants --------------------------------------------------------------

export const parentEnfants = {
  list: () => api.get<{ enfants: DashboardEnfant[] }>("/api/parents/me/enfants"),

  lie: (emailEleve: string, invitationCode: string) =>
    api.post<any>("/api/parents/me/enfants/lier", { email_eleve: emailEleve, invitation_code: invitationCode }),

  delier: (eleveId: number) =>
    api.delete<void>(`/api/parents/me/enfants/${eleveId}/delier`),

  suivi: (eleveId: number) =>
    api.get<SuiviData>(`/api/parents/me/enfants/${eleveId}/suivi`),

  progression: (eleveId: number) =>
    api.get<ProgressionData>(`/api/parents/me/enfants/${eleveId}/progression`),
};

// --- Dashboard ------------------------------------------------------------

export const parentDashboard = {
  get: () => api.get<ParentDashboardData>("/api/parents/me/dashboard"),
};

// --- Wallet Recharge ------------------------------------------------------

export const parentWallet = {
  creditWallet: (eleveId: number, amountTnd: number) =>
    api.post<any>(`/api/konnect/parents/me/enfants/${eleveId}/credit-wallet`, { amount_tnd: amountTnd }),
};

// --- Messagerie -----------------------------------------------------------

export const parentMessages = {
  list: (params?: { skip?: number; limit?: number; unread_only?: boolean }) => {
    const qs = new URLSearchParams();
    if (params?.skip) qs.set("skip", String(params.skip));
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.unread_only) qs.set("unread_only", "true");
    const query = qs.toString();
    return api.get<{ total: number; messages: ParentMessage[] }>(
      `/api/parents/me/messages${query ? `?${query}` : ""}`
    );
  },

  send: (payload: SendMessagePayload) =>
    api.post<SendMessageResult>("/api/parents/me/messages", payload),

  markRead: (messageId: number) =>
    api.put<{ ok: boolean }>(`/api/parents/me/messages/${messageId}/read`),
};

// --- Unified parentAPI object (used by pages) -----------------------------

export const parentAPI = {
  getDashboard: () => parentDashboard.get(),
  lierEleve: (email: string, invitationCode: string) => parentEnfants.lie(email, invitationCode),
  delierEleve: (id: number) => parentEnfants.delier(id),
  getSuivi: (id: number) => parentEnfants.suivi(id),
  getProgression: (id: number) => parentEnfants.progression(id),
  rechargeWallet: (id: number, amount: number) => parentWallet.creditWallet(id, amount),
  getMessages: () => parentMessages.list(),
  sendMessage: (payload: SendMessagePayload) => parentMessages.send(payload),
  markMessageRead: (id: number) => parentMessages.markRead(id),
};

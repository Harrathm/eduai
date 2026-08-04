import { tokenStorage } from "../../../utils/tokenStorage";

const API_BASE = "/api";

async function fetchJSON(url: string, options?: RequestInit) {
  const token = tokenStorage.getToken();
  const headers: Record<string, string> = { ...((options?.headers as Record<string, string>) || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!headers["Content-Type"] && options?.method !== "GET") {
    headers["Content-Type"] = "application/json";
  }
  const resp = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || "Erreur API");
  }
  return resp.json();
}

export interface Enfant {
  eleve_id: number;
  full_name: string;
  email: string;
  niveau_scolaire: string | null;
  school_id: number | null;
  date_liaison: string;
  dt_balance: number;
  packs_actifs_count: number;
}

export interface DashboardData {
  enfants: Enfant[];
  total_dt_depense: number;
}

export interface SuiviData {
  eleve_id: number;
  full_name: string;
  niveau_scolaire: string | null;
  dt_balance: number;
  packs_actifs: { pack_id: number; valid_from: string; valid_until: string; amount_paid: number; currency: string }[];
}

export interface ProgressionData {
  eleve_id: number;
  full_name: string;
  niveau_scolaire: string | null;
  scores: { chapitre_id: number; score: number; date: string }[];
  badges: { badge_id: number; nom: string; description: string; icon_url: string | null; couleur: string; date_obtention: string }[];
  streaks: { date: string; streak_login: boolean; streak_quiz: boolean; streak_objectif: boolean; points_jour: number }[];
  objectifs: { id: number; matiere: string | null; horizon: string; metric_type: string; target_value: number; status: string; progress_pct: number }[];
}

export interface Message {
  id: number;
  sender_id: number;
  sender_name: string;
  subject: string;
  body: string;
  created_at: string;
  is_read: boolean;
}

export const parentAPI = {
  getDashboard: () => fetchJSON("/parents/me/dashboard") as Promise<DashboardData>,
  getEnfants: () => fetchJSON("/parents/me/enfants") as Promise<{ enfants: Enfant[] }>,
  getSuivi: (eleveId: number) => fetchJSON(`/parents/me/enfants/${eleveId}/suivi`) as Promise<SuiviData>,
  getProgression: (eleveId: number) => fetchJSON(`/parents/me/enfants/${eleveId}/progression`) as Promise<ProgressionData>,
  lierEleve: (email: string) => fetchJSON("/parents/me/enfants/lier", { method: "POST", body: JSON.stringify({ email_eleve: email }) }),
  delierEleve: (eleveId: number) => fetchJSON(`/parents/me/enfants/${eleveId}/delier`, { method: "DELETE" }),

  // Messaging
  getMessages: (unreadOnly = false) =>
    fetchJSON(`/parents/me/messages${unreadOnly ? "?unread_only=true" : ""}`) as Promise<{ total: number; messages: Message[] }>,
  sendMessage: (data: { recipient_type: string; subject: string; body: string }) =>
    fetchJSON("/parents/me/messages", { method: "POST", body: JSON.stringify(data) }),
  markMessageRead: (messageId: number) =>
    fetchJSON(`/parents/me/messages/${messageId}/read`, { method: "PUT" }),

  // Wallet recharge via Konnect
  rechargeWallet: (eleveId: number, amountTnd: number) =>
    fetchJSON(`/konnect/parents/me/enfants/${eleveId}/credit-wallet`, {
      method: "POST",
      body: JSON.stringify({ amount_tnd: amountTnd }),
    }) as Promise<{ pay_url: string; payment_id: string }>,
};

/**
 * Parent API — famille, enfants, wallet.
 * Migrated from inline fetch calls in parent pages.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

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

export interface SuiviEnfant {
  eleve_id: number;
  dt_balance: number;
  packs_actifs_count: number;
}

// ─── Famille ───────────────────────────────────────────────────────────────

export const parentFamille = {
  getCompte: () => api.get<CompteFamille>("/api/famille/compte"),
  getEnfants: () => api.get<{ items?: EnfantFamille[]; enfants?: EnfantFamille[] }>("/api/famille/enfants"),
};

// ─── Enfants ───────────────────────────────────────────────────────────────

export const parentEnfants = {
  list: () => api.get<{ enfants: DashboardEnfant[] }>("/api/parents/me/enfants"),

  lie: (emailEleve: string) =>
    api.post<any>("/api/parents/me/enfants/lier", { email_eleve: emailEleve }),

  delier: (eleveId: number) =>
    api.delete<void>(`/api/parents/me/enfants/${eleveId}/delier`),

  suivi: (eleveId: number) =>
    api.get<SuiviEnfant>(`/api/parents/me/enfants/${eleveId}/suivi`),
};

// ─── Wallet Recharge ───────────────────────────────────────────────────────

export const parentWallet = {
  creditWallet: (eleveId: number, amountTnd: number) =>
    api.post<any>(`/api/konnect/parents/me/enfants/${eleveId}/credit-wallet`, { amount_tnd: amountTnd }),
};

// ─── Backward compat alias ─────────────────────────────────────────────────

export const parentAPI = { famille: parentFamille, enfants: parentEnfants };

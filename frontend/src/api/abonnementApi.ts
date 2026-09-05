/**
 * Abonnement API — packs, abonnements, tier changes.
 * Extracted from inline fetch calls in StudentDashboard, TeacherAbonnementsPage, etc.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface Abonnement {
  id: number;
  pack_id: number;
  pack_name: string;
  user_id: number;
  school_id: number;
  start_date: string;
  end_date: string;
  status: string;
  tier: string;
  price_paid: number;
  matieres_config?: { matieres?: number[] } | null;
}

export interface PackDefinition {
  id: number;
  name: string;
  tier: string;
  description: string | null;
  price: number;
  duration_months: number;
  features: string[];
  is_active: boolean;
}

// ─── Endpoints ──────────────────────────────────────────────────────────────

export interface MatiereOption {
  id: number;
  name: string;
  category: "langue" | "specialite";
  niveau_scolaire: string;
}

export const abonnementApi = {
  mesAbonnements: () => api.get<Abonnement[]>("/api/abonnements/mes-abonnements"),

  listPacks: () => api.get<PackDefinition[]>("/api/abonnements/packs"),

  // Écart#1 FIX — un parent doit fournir eleve_id (bénéficiaire enfant),
  // sinon le backend répond 400 (routers/abonnements.py:200-205).
  purchasePack: (packId: number, options?: { matieres?: number[]; eleveId?: number }) =>
    api.post<any>(`/api/abonnements/packs/${packId}/purchase`, {
      matieres: options?.matieres,
      ...(options?.eleveId != null ? { eleve_id: options.eleveId } : {}),
    }),

  listMyAbonnements: () => api.get<Abonnement[]>("/api/abonnements/mes-abonnements"),

  getAvailableMatieres: (niveauScolaire: string) =>
    api.get<MatiereOption[]>(`/api/pathway/matieres?niveau_scolaire=${encodeURIComponent(niveauScolaire)}`),

  reconfigureMatieres: (abonnementId: number, matieres: number[]) =>
    api.post<any>(`/api/abonnements/${abonnementId}/reconfigure`, { matieres }),
};

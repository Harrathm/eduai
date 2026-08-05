/**
 * Pathway API — parcours, matières, spécialités, éléments (Module A).
 * Merged from features/pathway/api/index.ts + features/teacher/api/moduleApi.ts.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface Parcours {
  id: number;
  title: string;
  description: string | null;
  niveau_scolaire: string;
  status: string;
  school_id: number | null;
  created_at: string;
}

export interface Chapitre {
  id: number;
  parcours_id: number;
  title: string;
  order_index: number;
}

export interface Lecon {
  id: number;
  chapitre_id: number;
  title: string;
  order_index: number;
}

export interface Paragraphe {
  id: number;
  lecon_id: number;
  content: string;
  order_index: number;
}

export interface ElementPedagogique {
  id: number;
  type: string;
  title: string;
  content: string | null;
  status: string;
  workflow_status: string | null;
  school_id: number | null;
  created_by: number;
  created_at: string;
}

// ─── Parcours CRUD ──────────────────────────────────────────────────────────

export const pathwayParcours = {
  list: () => api.get<Parcours[]>("/api/pathway/parcours"),
  get: (id: number) => api.get<Parcours>(`/api/pathway/parcours/${id}`),
  create: (data: Partial<Parcours>) => api.post<Parcours>("/api/pathway/parcours", data),
  update: (id: number, data: Partial<Parcours>) =>
    api.patch<Parcours>(`/api/pathway/parcours/${id}`, data),
  delete: (id: number) => api.delete<void>(`/api/pathway/parcours/${id}`),
};

// ─── Chapitres ──────────────────────────────────────────────────────────────

export const pathwayChapitres = {
  list: (parcoursId: number) =>
    api.get<Chapitre[]>(`/api/pathway/parcours/${parcoursId}/chapitres`),
  create: (parcoursId: number, data: Partial<Chapitre>) =>
    api.post<Chapitre>(`/api/pathway/parcours/${parcoursId}/chapitres`, data),
  update: (id: number, data: Partial<Chapitre>) =>
    api.patch<Chapitre>(`/api/pathway/chapitres/${id}`, data),
  delete: (id: number) => api.delete<void>(`/api/pathway/chapitres/${id}`),
};

// ─── Lecons ─────────────────────────────────────────────────────────────────

export const pathwayLecons = {
  list: (chapitreId: number) =>
    api.get<Lecon[]>(`/api/pathway/chapitres/${chapitreId}/lecons`),
  create: (chapitreId: number, data: Partial<Lecon>) =>
    api.post<Lecon>(`/api/pathway/chapitres/${chapitreId}/lecons`, data),
  update: (id: number, data: Partial<Lecon>) =>
    api.patch<Lecon>(`/api/pathway/lecons/${id}`, data),
  delete: (id: number) => api.delete<void>(`/api/pathway/lecons/${id}`),
};

// ─── Paragraphes ────────────────────────────────────────────────────────────

export const pathwayParagraphes = {
  list: (leconId: number) =>
    api.get<Paragraphe[]>(`/api/pathway/lecons/${leconId}/paragraphes`),
  create: (leconId: number, data: Partial<Paragraphe>) =>
    api.post<Paragraphe>(`/api/pathway/lecons/${leconId}/paragraphes`, data),
  update: (id: number, data: Partial<Paragraphe>) =>
    api.patch<Paragraphe>(`/api/pathway/paragraphes/${id}`, data),
  delete: (id: number) => api.delete<void>(`/api/pathway/paragraphes/${id}`),
};

// ─── Matières (with thresholds) ────────────────────────────────────────────

export const pathwayMatieres = {
  list: (niveauEtudeId?: number) => {
    const sp = new URLSearchParams();
    if (niveauEtudeId) sp.set("niveau_etude_id", String(niveauEtudeId));
    const qs = sp.toString();
    return api.get<any[]>(`/api/pathway/matieres${qs ? `?${qs}` : ""}`);
  },
  update: (id: number, data: {
    remediation_threshold?: number;
    standard_threshold?: number;
    avance_threshold?: number;
  }) => api.put<any>(`/api/pathway/matieres/${id}`, data),
};

// ─── Spécialités Pédagogiques ─────────────────────────────────────────────

export const pathwaySpecialites = {
  list: () => api.get<any[]>("/api/pathway/specialites-pedagogiques"),
  create: (data: { nom: string; cycle_scolaire: string; matiere_ids: number[] }) =>
    api.post<any>("/api/pathway/specialites-pedagogiques", data),
};

// ─── Responsables Pédagogiques ────────────────────────────────────────────

export const pathwayResponsables = {
  assign: (data: { specialite_id: number; user_id: number; niveaux_etude_ids: number[] }) =>
    api.post<any>("/api/pathway/responsables-pedagogiques", data),
  listContenus: (userId: number) =>
    api.get<any[]>(`/api/pathway/responsables-pedagogiques/${userId}/contenus`),
};

// ─── Contenus Validation ──────────────────────────────────────────────────

export const pathwayContenus = {
  valider: (contenuId: number) =>
    api.post<any>(`/api/pathway/contenus-notion/${contenuId}/valider`),
  rejeter: (contenuId: number, commentaire: string) =>
    api.post<any>(`/api/pathway/contenus-notion/${contenuId}/rejeter`, { commentaire }),
};

// ─── Elements ───────────────────────────────────────────────────────────────

export const pathwayElements = {
  list: (params?: { type?: string; status?: string; skip?: number; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.type) sp.set("type", params.type);
    if (params?.status) sp.set("status", params.status);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<ElementPedagogique[]>(`/api/pathway/elements${qs ? `?${qs}` : ""}`);
  },
  get: (id: number) => api.get<ElementPedagogique>(`/api/pathway/elements/${id}`),
  create: (data: Partial<ElementPedagogique>) =>
    api.post<ElementPedagogique>("/api/pathway/elements", data),
  update: (id: number, data: Partial<ElementPedagogique>) =>
    api.patch<ElementPedagogique>(`/api/pathway/elements/${id}`, data),
  submit: (id: number) =>
    api.post<ElementPedagogique>(`/api/pathway/elements/${id}/submit`),
  getWorkflow: (id: number) =>
    api.get<any[]>(`/api/pathway/elements/${id}/workflow`),
};

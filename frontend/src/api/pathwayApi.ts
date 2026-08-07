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

// ─── Additional Types (from old features/pathway/api) ──────────────────────

export interface PathwayCatalogItem {
  id: number;
  nom: string;
  cycle_scolaire: string;
  matieres: { id: number; nom: string }[];
}

export interface MonParcoursNiveau {
  niveau_etude_id: number;
  nom: string;
  matieres: {
    id: number;
    nom: string;
    chapters: {
      id: number;
      nom: string;
      progress_pct: number;
    }[];
  }[];
}

export interface NiveauEffectif {
  niveau: string;
  effectif: number;
}

export interface NiveauEtude {
  id: number;
  nom: string;
  cycle_scolaire: string;
  ordre: number;
}

export interface Matiere {
  id: number;
  nom: string;
  niveau_etude_id: number;
  remediation_threshold: number;
  standard_threshold: number;
  avance_threshold: number;
}

export interface ChapterPathway {
  id: number;
  nom: string;
  matiere_id: number;
  ordre: number;
}

export interface Notion {
  id: number;
  nom: string;
  chapter_id: number;
  ordre: number;
}

export interface ContenuNotion {
  id: number;
  notion_id: number;
  type: string;
  content: string;
  statut: string;
}

export interface StatutPublication {
  notion_id: number;
  statut: string;
  published_at: string | null;
}

export interface NotificationReorientation {
  id: number;
  student_id: number;
  student_name: string;
  current_niveau: string;
  target_niveau: string;
  reason: string;
  status: string;
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

// ─── Catalog & Enrollment (student-facing) ─────────────────────────────────

export const pathwayCatalog = {
  get: () => api.get<PathwayCatalogItem[]>("/api/pathway/catalog"),
  enroll: (niveauId: number) =>
    api.post<any>(`/api/pathway/catalog/${niveauId}/enroll`),
};

export const pathwayMonParcours = {
  get: () => api.get<MonParcoursNiveau[]>("/api/pathway/mon-parcours"),
};

// ─── Niveaux d'étude CRUD ──────────────────────────────────────────────────

export const pathwayNiveauxEtude = {
  list: () => api.get<NiveauEtude[]>("/api/pathway/niveaux-etude"),
  create: (data: Partial<NiveauEtude>) =>
    api.post<NiveauEtude>("/api/pathway/niveaux-etude", data),
  update: (id: number, data: Partial<NiveauEtude>) =>
    api.patch<NiveauEtude>(`/api/pathway/niveaux-etude/${id}`, data),
  delete: (id: number) =>
    api.delete<void>(`/api/pathway/niveaux-etude/${id}`),
};

// ─── Matières CRUD ─────────────────────────────────────────────────────────

export const pathwayMatieresCrud = {
  list: (niveauEtudeId?: number) => {
    const sp = new URLSearchParams();
    if (niveauEtudeId) sp.set("niveau_etude_id", String(niveauEtudeId));
    const qs = sp.toString();
    return api.get<Matiere[]>(`/api/pathway/matieres${qs ? `?${qs}` : ""}`);
  },
  create: (data: Partial<Matiere>) =>
    api.post<Matiere>("/api/pathway/matieres", data),
  update: (id: number, data: Partial<Matiere>) =>
    api.patch<Matiere>(`/api/pathway/matieres/${id}`, data),
  delete: (id: number) =>
    api.delete<void>(`/api/pathway/matieres/${id}`),
};

// ─── Chapters CRUD (pathway) ───────────────────────────────────────────────

export const pathwayChaptersCrud = {
  list: (matiereId: number) =>
    api.get<ChapterPathway[]>(`/api/pathway/matieres/${matiereId}/chapters`),
  create: (matiereId: number, data: Partial<ChapterPathway>) =>
    api.post<ChapterPathway>(`/api/pathway/matieres/${matiereId}/chapters`, data),
  update: (id: number, data: Partial<ChapterPathway>) =>
    api.patch<ChapterPathway>(`/api/pathway/chapters/${id}`, data),
  delete: (id: number) =>
    api.delete<void>(`/api/pathway/chapters/${id}`),
};

// ─── Notions CRUD ──────────────────────────────────────────────────────────

export const pathwayNotions = {
  list: (chapterId: number) =>
    api.get<Notion[]>(`/api/pathway/chapters/${chapterId}/notions`),
  create: (chapterId: number, data: Partial<Notion>) =>
    api.post<Notion>(`/api/pathway/chapters/${chapterId}/notions`, data),
  update: (id: number, data: Partial<Notion>) =>
    api.patch<Notion>(`/api/pathway/notions/${id}`, data),
  delete: (id: number) =>
    api.delete<void>(`/api/pathway/notions/${id}`),
};

// ─── Contenus (content by notion) ──────────────────────────────────────────

export const pathwayContenusByNotion = {
  list: (notionId: number) =>
    api.get<ContenuNotion[]>(`/api/pathway/notions/${notionId}/contenus`),
};

// ─── Statut Publication ────────────────────────────────────────────────────

export const pathwayStatutPublication = {
  get: (notionId: number) =>
    api.get<StatutPublication>(`/api/pathway/notions/${notionId}/statut`),
};

// ─── Niveau Effectif (student profile) ─────────────────────────────────────

export const pathwayNiveauEffectif = {
  get: () => api.get<NiveauEffectif[]>("/api/pathway/niveau-effectif"),
};

// ─── Reorientation ─────────────────────────────────────────────────────────

export const pathwayReorientation = {
  listNotifications: () =>
    api.get<NotificationReorientation[]>("/api/pathway/reorientation/notifications"),
  valider: (notificationId: number) =>
    api.post<any>(`/api/pathway/reorientation/${notificationId}/valider`),
};

// ─── Legacy flat exports (backward compat for old import patterns) ─────────

export const getPathwayCatalog = pathwayCatalog.get;
export const enrollPathway = pathwayCatalog.enroll;
export const getMonParcours = pathwayMonParcours.get;
export const getMatieres = pathwayMatieresCrud.list;
export const createMatiere = pathwayMatieresCrud.create;
export const updateMatiere = pathwayMatieresCrud.update;
export const deleteMatiere = pathwayMatieresCrud.delete;
export const getChapters = pathwayChaptersCrud.list;
export const createChapter = pathwayChaptersCrud.create;
export const updateChapter = pathwayChaptersCrud.update;
export const deleteChapter = pathwayChaptersCrud.delete;
export const getNotions = pathwayNotions.list;
export const createNotion = pathwayNotions.create;
export const updateNotion = pathwayNotions.update;
export const deleteNotion = pathwayNotions.delete;
export const getContenus = pathwayContenusByNotion.list;
export const getStatutPublication = pathwayStatutPublication.get;
export const getNiveauEffectif = pathwayNiveauEffectif.get;
export const getNiveauxEtude = pathwayNiveauxEtude.list;
export const createNiveauEtude = pathwayNiveauxEtude.create;
export const updateNiveauEtude = pathwayNiveauxEtude.update;
export const deleteNiveauEtude = pathwayNiveauxEtude.delete;
export const getNotificationsReorientation = pathwayReorientation.listNotifications;
export const validerReorientation = pathwayReorientation.valider;

// ─── Legacy moduleApi flat exports (backward compat) ───────────────────────

export const searchElements = pathwayElements.list;
export const listCompetences = async () => api.get<any[]>("/api/pathway/competences");
export const listElements = pathwayElements.list;
export const createElement = pathwayElements.create;
export const updateElement = pathwayElements.update;
export const submitElement = pathwayElements.submit;
export const getWorkflow = pathwayElements.getWorkflow;
export const createElementTexte = (data: any) => api.post<any>("/api/pathway/elements/texte", data);
export const createElementVideo = (data: any) => api.post<any>("/api/pathway/elements/video", data);
export const listParcours = pathwayParcours.list;
export const createParcours = pathwayParcours.create;
export const updateParcours = pathwayParcours.update;
export const listChapitres = pathwayChapitres.list;
export const createChapitre = pathwayChapitres.create;
export const updateChapitre = pathwayChapitres.update;
export const listLecons = pathwayLecons.list;
export const createLecon = pathwayLecons.create;
export const updateLecon = pathwayLecons.update;
export const listParagraphes = pathwayParagraphes.list;
export const createParagraphe = pathwayParagraphes.create;
export const updateParagraphe = pathwayParagraphes.update;

// ─── Additional types for moduleApi compat ─────────────────────────────────

export type Competence = { id: number; name: string; description: string | null };
export type WorkflowEntry = { id: number; status: string; user_id: number; timestamp: string };

// ─── Matières by niveau (for course creation ABAC) ────────────────────────

export const pathwayApi = {
  getMatieresByNiveau: (niveauScolaire: string) =>
    api.get<any[]>(`/api/pathway/matieres-by-niveau?niveau_scolaire=${encodeURIComponent(niveauScolaire)}`),
};

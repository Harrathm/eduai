const API = "";

async function api<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = JSON.parse(localStorage.getItem("auth-storage") || "{}")?.state?.token;
  const r = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...opts.headers,
    },
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail || "Erreur API");
  }
  return r.json();
}

export interface Parcours {
  id: number;
  titre: string;
  description?: string;
  matiere: string;
  niveau_scolaire: string;
  difficulte: string;
  objectifs?: any;
  est_publique: boolean;
  est_actif: boolean;
  auteur_id?: number;
  created_at?: string;
}

export interface Chapitre {
  id: number;
  parcours_id: number;
  titre: string;
  ordre?: number;
  created_at?: string;
}

export interface Lecon {
  id: number;
  chapitre_id: number;
  titre: string;
  ordre?: number;
  created_at?: string;
}

export interface Paragraphe {
  id: number;
  lecon_id: number;
  titre: string;
  contenu: string;
  ordre?: number;
  created_at?: string;
}

export interface ElementPedagogique {
  id: number;
  type: string;
  titre: string;
  description?: string;
  lecon_id?: number;
  paragraphe_id?: number;
  auteur_id?: number;
  statut: string;
  difficulte: string;
  est_global: boolean;
  est_libre: boolean;
  created_at?: string;
}

export interface WorkflowEntry {
  id: number;
  element_id: number;
  from_statut: string;
  to_statut: string;
  commentaire?: string;
  effectue_par_id: number;
  created_at: string;
}

export interface Competence {
  id: number;
  nom: string;
  description?: string;
  matiere?: string;
  niveau_scolaire?: string;
}

export interface PackDefinition {
  id: number;
  nom: string;
  description?: string;
  tier: string;
  prix: number;
  niveau_scolaire: string;
  nb_cours: number;
  duree_jours: number;
  est_actif: boolean;
}

export interface Abonnement {
  id: number;
  eleve_id: number;
  pack_id: number;
  statut: string;
  date_debut: string;
  date_fin?: string;
  created_at?: string;
}

// --- Parcours ---
export const listParcours = () => api<{ total: number; items: Parcours[] }>("/api/parcours");
export const createParcours = (data: Partial<Parcours>) => api<Parcours>("/api/parcours", { method: "POST", body: JSON.stringify(data) });
export const getParcours = (id: number) => api<Parcours>(`/api/parcours/${id}`);
export const updateParcours = (id: number, data: Partial<Parcours>) => api<Parcours>(`/api/parcours/${id}`, { method: "PUT", body: JSON.stringify(data) });

// --- Chapitres ---
export const listChapitres = (parcoursId: number) => api<{ total: number; items: Chapitre[] }>(`/api/parcours/${parcoursId}/chapitres`);
export const createChapitre = (parcoursId: number, data: Partial<Chapitre>) => api<Chapitre>(`/api/parcours/${parcoursId}/chapitres`, { method: "POST", body: JSON.stringify(data) });
export const updateChapitre = (id: number, data: Partial<Chapitre>) => api<Chapitre>(`/api/chapitres/${id}`, { method: "PUT", body: JSON.stringify(data) });

// --- Lecons ---
export const listLecons = (chapitreId: number) => api<{ total: number; items: Lecon[] }>(`/api/chapitres/${chapitreId}/lecons`);
export const createLecon = (chapitreId: number, data: Partial<Lecon>) => api<Lecon>(`/api/chapitres/${chapitreId}/lecons`, { method: "POST", body: JSON.stringify(data) });
export const updateLecon = (id: number, data: Partial<Lecon>) => api<Lecon>(`/api/lecons/${id}`, { method: "PUT", body: JSON.stringify(data) });

// --- Paragraphes ---
export const listParagraphes = (leconId: number) => api<{ total: number; items: Paragraphe[] }>(`/api/lecons/${leconId}/paragraphes`);
export const createParagraphe = (leconId: number, data: Partial<Paragraphe>) => api<Paragraphe>(`/api/lecons/${leconId}/paragraphes`, { method: "POST", body: JSON.stringify(data) });
export const updateParagraphe = (id: number, data: Partial<Paragraphe>) => api<Paragraphe>(`/api/paragraphes/${id}`, { method: "PUT", body: JSON.stringify(data) });

// --- Elements ---
export const listElements = (params?: Record<string, string>) => {
  const q = params ? "?" + new URLSearchParams(params).toString() : "";
  return api<{ total: number; items: ElementPedagogique[] }>(`/api/elements${q}`);
};
export const createElement = (data: Partial<ElementPedagogique>) => api<ElementPedagogique>("/api/elements", { method: "POST", body: JSON.stringify(data) });
export const getElement = (id: number) => api<ElementPedagogique>(`/api/elements/${id}`);
export const updateElement = (id: number, data: Partial<ElementPedagogique>) => api<ElementPedagogique>(`/api/elements/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const submitElement = (id: number) => api(`/api/elements/${id}/submit`, { method: "POST" });
export const getWorkflow = (id: number) => api<WorkflowEntry[]>(`/api/elements/${id}/workflow`);
export const createElementTexte = (id: number, data: { contenu_html: string }) => api(`/api/elements/${id}/texte`, { method: "POST", body: JSON.stringify(data) });
export const createElementVideo = (id: number, data: { url: string; duree_secondes?: number }) => api(`/api/elements/${id}/video`, { method: "POST", body: JSON.stringify(data) });

// --- Bibliotheque ---
export const searchElements = (q: string) => api<{ total: number; items: ElementPedagogique[] }>(`/api/bibliotheque/search?q=${encodeURIComponent(q)}`);
export const listCompetences = () => api<{ total: number; items: Competence[] }>("/api/bibliotheque/competences");

// --- Packs ---
export const listPacks = () => api<{ total: number; items: PackDefinition[] }>("/api/abonnements/packs");
export const getPack = (id: number) => api<PackDefinition>(`/api/abonnements/packs/${id}`);

// --- Abonnements ---
export const listMyAbonnements = () => api<{ total: number; items: Abonnement[] }>("/api/abonnements/mes-abonnements");

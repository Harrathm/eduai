const API_URL = "";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = typeof err.detail === "object" ? JSON.stringify(err.detail) : (err.detail || `HTTP ${res.status}`);
    throw new Error(detail);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

// ─── Types ──────────────────────────────────────────────────────────────────

export interface NiveauEtude {
  id: number;
  nom: string;
  ordre: number;
}

export interface Matiere {
  id: number;
  niveau_etude_id: number;
  nom: string;
}

export interface ChapterPathway {
  id: number;
  matiere_id: number;
  nom: string;
  ordre: number;
}

export interface Notion {
  id: number;
  chapitre_id: number;
  nom: string;
  ordre: number;
}

export interface ContenuNotion {
  id: number;
  notion_id: number;
  niveau_assimilation: string;
  type_ressource: string;
  contenu: string;
  enseignant_id: number | null;
  statut_pedagogique: string;
}

export interface ProfilAssimilation {
  id: number;
  eleve_id: number;
  chapitre_id: number;
  niveau_assimilation_courant: string;
  source_changement: string;
  score_declencheur: number | null;
  date: string;
  statut_validation: string;
}

export interface NotificationReorientation {
  id: number;
  profil_assimilation_id: number;
  enseignant_id: number;
  date_notification: string;
  date_limite_action: string;
  action_prise: string;
}

export interface StatutPublication {
  statut: "publiable" | "brouillon";
  niveaux_manquants: string[];
}

export interface NiveauEffectif {
  eleve_id: number;
  chapitre_id: number;
  niveau_effectif: string;
  source: string;
}

export interface AccesEffectif {
  eleve_id: number;
  matiere_id: number;
  chapitre_id: number;
  acces: boolean;
  niveau_effectif: string | null;
}

export interface HistoriqueScore {
  id: number;
  eleve_id: number;
  chapitre_id: number;
  quiz_id: number | null;
  score: number;
  date: string;
}

// ─── API Functions ──────────────────────────────────────────────────────────

// Arborescence CRUD
export const getNiveauxEtude = () => request<NiveauEtude[]>("/api/pathway/niveaux-etude");
export const createNiveauEtude = (data: { nom: string; ordre: number }) =>
  request<NiveauEtude>("/api/pathway/niveaux-etude", { method: "POST", body: JSON.stringify(data) });
export const updateNiveauEtude = (id: number, data: { nom: string; ordre: number }) =>
  request<NiveauEtude>(`/api/pathway/niveaux-etude/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteNiveauEtude = (id: number) =>
  request<{ message: string }>(`/api/pathway/niveaux-etude/${id}`, { method: "DELETE" });

export const getMatieres = (niveauEtudeId?: number) => {
  const params = niveauEtudeId ? `?niveau_etude_id=${niveauEtudeId}` : "";
  return request<Matiere[]>(`/api/pathway/matieres${params}`);
};
export const createMatiere = (data: { niveau_etude_id: number; nom: string }) =>
  request<Matiere>("/api/pathway/matieres", { method: "POST", body: JSON.stringify(data) });
export const updateMatiere = (id: number, data: { niveau_etude_id: number; nom: string }) =>
  request<Matiere>(`/api/pathway/matieres/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteMatiere = (id: number) =>
  request<{ message: string }>(`/api/pathway/matieres/${id}`, { method: "DELETE" });

export const getChapters = (matiereId?: number) => {
  const params = matiereId ? `?matiere_id=${matiereId}` : "";
  return request<ChapterPathway[]>(`/api/pathway/chapter-pathways${params}`);
};
export const createChapter = (data: { matiere_id: number; nom: string; ordre: number }) =>
  request<ChapterPathway>("/api/pathway/chapter-pathways", { method: "POST", body: JSON.stringify(data) });
export const updateChapter = (id: number, data: { matiere_id: number; nom: string; ordre: number }) =>
  request<ChapterPathway>(`/api/pathway/chapter-pathways/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteChapter = (id: number) =>
  request<{ message: string }>(`/api/pathway/chapter-pathways/${id}`, { method: "DELETE" });

export const getNotions = (chapitreId?: number) => {
  const params = chapitreId ? `?chapitre_id=${chapitreId}` : "";
  return request<Notion[]>(`/api/pathway/notions-list${params}`);
};
export const createNotion = (data: { chapitre_id: number; nom: string; ordre: number }) =>
  request<Notion>("/api/pathway/notions-list", { method: "POST", body: JSON.stringify(data) });
export const updateNotion = (id: number, data: { chapitre_id: number; nom: string; ordre: number }) =>
  request<Notion>(`/api/pathway/notions-list/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteNotion = (id: number) =>
  request<{ message: string }>(`/api/pathway/notions-list/${id}`, { method: "DELETE" });

export const getContenus = (notionId?: number) => {
  const params = notionId ? `?notion_id=${notionId}` : "";
  return request<ContenuNotion[]>(`/api/pathway/contenus${params}`);
};
export const createContenu = (data: {
  notion_id: number; niveau_assimilation: string; type_ressource: string;
  contenu: string; enseignant_id?: number; statut_pedagogique?: string;
}) => request<ContenuNotion>("/api/pathway/contenus", { method: "POST", body: JSON.stringify(data) });
export const updateContenu = (id: number, data: {
  notion_id: number; niveau_assimilation: string; type_ressource: string;
  contenu: string; enseignant_id?: number; statut_pedagogique?: string;
}) => request<ContenuNotion>(`/api/pathway/contenus/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteContenu = (id: number) =>
  request<{ message: string }>(`/api/pathway/contenus/${id}`, { method: "DELETE" });

// Pathway logic
export const getNiveauEffectif = (eleveId: number, chapitreId: number) =>
  request<NiveauEffectif>(`/api/pathway/eleves/${eleveId}/profil-assimilation?chapitre_id=${chapitreId}`);
export const getAccesEffectif = (eleveId: number, matiereId: number, chapitreId: number) =>
  request<AccesEffectif>(`/api/pathway/eleves/${eleveId}/acces-effectif?matiere_id=${matiereId}&chapitre_id=${chapitreId}`);
export const getStatutPublication = (notionId: number) =>
  request<StatutPublication>(`/api/pathway/notions/${notionId}/statut-publication`);
export const getContenuAServir = (notionId: number, eleveId: number) =>
  request<any>(`/api/pathway/notions/${notionId}/contenu?eleve_id=${eleveId}`);

// Notifications
export const getNotificationsReorientation = (enseignantId: number) =>
  request<NotificationReorientation[]>(`/api/pathway/enseignants/${enseignantId}/notifications-reorientation`);
export const validerReorientation = (profilId: number, action: "confirme" | "annule") =>
  request<ProfilAssimilation>(`/api/pathway/profils-assimilation/${profilId}/validation`, {
    method: "POST", body: JSON.stringify({ action }),
  });

// Scores
export const recordScore = (data: { eleve_id: number; chapitre_id: number; quiz_id?: number; score: number }) =>
  request<HistoriqueScore>("/api/pathway/scores", { method: "POST", body: JSON.stringify(data) });

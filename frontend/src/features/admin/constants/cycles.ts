export const CYCLE_NIVEAUX: Record<string, string[]> = {
  primaire: [
    "1ère Année Base", "2ème Année Base", "3ème Année Base",
    "4ème Année Base", "5ème Année Base", "6ème Année Base",
  ],
  preparatoire: [
    "7ème Année Base", "8ème Année Base", "9ème Année Base",
  ],
  secondaire: [
    "1ère Année Secondaire",
    "2ème Lettres", "2ème Sciences", "2ème Technologie", "2ème Économie et Services",
    "3ème Lettres", "3ème Mathématiques", "3ème Sciences Expérimentales",
    "3ème Économie et Gestion", "3ème Sciences de l'Informatique", "3ème Sciences Techniques",
    "Bac Lettres", "Bac Mathématiques", "Bac Sciences Expérimentales",
    "Bac Économie et Gestion", "Bac Sciences de l'Informatique", "Bac Sciences Techniques",
  ],
};

export const CYCLE_LABELS: Record<string, string> = {
  primaire: "Primaire",
  preparatoire: "Préparatoire",
  secondaire: "Secondaire",
};

/** Flat list of all official niveau values, grouped by cycle. */
export const ALL_NIVEAUX: { group: string; items: string[] }[] = Object.entries(CYCLE_NIVEAUX).map(
  ([key, items]) => ({ group: CYCLE_LABELS[key] || key, items })
);

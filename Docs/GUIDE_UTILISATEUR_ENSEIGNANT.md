# Guide Utilisateur EDUAI Learning - Enseignant (Teacher)

> **Version** : 1.0 — Aout 2026
> **Branche** : phase1-critical
> **Derniere mise a jour** : 06/08/2026

---

## Table des matieres

1. [Introduction au Role](#1-introduction-au-rle)
2. [Tableau de Bord Enseignant](#2-tableau-de-bord-enseignant)
3. [Etats du Compte (A / B / C)](#3-etats-du-compte-a--b--c)
4. [Gestion des Classes](#4-gestion-des-classes)
5. [Creation de Contenu](#5-creation-de-contenu)
6. [Studio IA](#6-studio-ia)
7. [Bibliotheque Globale & Parcours](#7-bibliothque-globale--parcours)
8. [Gestion des Evaluations (LMS)](#8-gestion-des-valuations-lms)
9. [Finance & Revenus](#9-finance--revenus)
10. [Souscriptions & Packs](#10-souscriptions--packs)

---

## 1. Introduction au Role

### Qui est l'Enseignant ?

L'Enseignant (`teacher`) est un role qui couvre la creation de contenu, la gestion de classes, l'evaluation des eleves et l'utilisation des outils IA. Ce role possede 3 sous-etats qui determinent le niveau d'acces.

### Les 3 sous-etats du compte

Le systeme distingue 3 etats bases sur les proprietes `is_approved` et `subscription_plan` de votre compte :

| Etat | Label | Condition | Niveau d'acces |
|------|-------|-----------|---------------|
| **A** | Valide (vert) | `is_approved != false` ET `subscription_plan != "trial"` | Acces complet — toutes les fonctionnalites |
| **B** | En attente (ambre) | `is_approved === false` | Read-only — pas de creation ni modification de contenu |
| **C** | Essai (rouge) | `subscription_plan === "trial"` | Read-only + restreint — pas de creation de contenu, souscription requise |

> **Pour les admin/lead**, le state est toujours A (non-teacher).

### Le role dans la navigation

Lorsque vous etes connecte en tant qu'enseignant, vous voyez dans la barre laterale :

- **Mes Classes** — Gestion de vos classes
- **Mes Cours** — Cours que vous avez crees
- **AI Studio** — Creation de contenu par IA (state A uniquement)
- **Revenus** — Suivi de vos revenus (partenaires uniquement)
- **Wallet** — Solde de credits IA
- **Parcours** — Parcours pedagogiques (state A uniquement)
- **Elements** — Elements pedagogiques (state A uniquement)
- **Bibliotheque** — Contenus de la bibliotheque globale

---

## 2. Tableau de Bord Enseignant

### Que contient le tableau de bord ?

**Chemin :** `Dashboard` (apres connexion)

Le tableau de bord affiche en parallel 3 appels API :

1. **Nombre de cours** — via `GET /api/courses/my-courses`
2. **Nombre de classes** — via `GET /api/teacher/classes`
3. **Credits IA** — via `GET /api/wallet/balance`

**Widgets affiches :**

| Widget | Description |
|--------|-------------|
| **Mes Cours** | Nombre total de cours que vous avez crees |
| **Mes Classes** | Nombre de classes actives |
| **Etudiants** | Nombre total d'eleves dans toutes vos classes |
| **Credits IA** | Solde disponible pour les fonctionnalites IA |
| **Badge d'etat** | Valide / En attente / Essai |
| **Actions rapides** | Liens vers : Mes Classes, AI Studio, Revenus, Wallet |
| **Classes recentes** | 3 premieres classes avec nombre d'eleves et cours associes |

---

## 3. Etats du Compte (A / B / C)

### State A — Valide

**Condition :** `is_approved != false` ET `subscription_plan != "trial"`

**Acces :** Toutes les fonctionnalites sont disponibles :
- Creation et modification de contenu
- Gestion de classes
- AI Studio
- Parcours et elements
- Validation de contenu
- Reorientations

### State B — En attente

**Condition :** `is_approved === false`

**Acces :** Read-only — vous pouvez consulter mais pas modifier.

**Banniere affichee :**
> "Vous ne pouvez pas creer ou modifier de contenu en attendant la validation pedagogique."

**Pages restreintes (TeacherWriteGuard) :**
- AI Studio
- Reorientations
- Validation Contenu
- Parcours
- Elements

**Comment sortir de l'etat B ?**
1. Votre inscription est envoyee a un Pedagogical Lead
2. Le Pedagogical Lead approuve votre compte (`is_approved = true`)
3. Vous passez en etat A

### State C — Essai

**Condition :** `subscription_plan === "trial"`

**Acces :** Read-only + restreint.

**Banniere affichee :**
> "Votre compte est en periode d'essai. Souscrivez a un pack pour acceder a toutes les fonctionnalites."

**Lien propose :** `/dashboard/teacher/abonnements` (catalogue de packs)

**Comment sortir de l'etat C ?**
1. Souscrivez a un pack d'abonnement
2. Votre `subscription_plan` passe a `"independent_paid"` ou `"school_allocated"`
3. Vous passez en etat A

### Verification backend

Le backend verifie l'abonnement avec `require_active_subscription` (fichier `deps.py:252-267`). Cette dependance bloque uniquement les **actions de creation** pour les enseignants independants avec abonnement expire. Les actions de lecture restent toujours accessibles.

---

## 4. Gestion des Classes

### Creer une classe

**Chemin :** `Mes Classes` > `Creer une classe`

**Pour creer une classe :**
1. Cliquez sur **"Creer une classe"**
2. Entrez le nom de la classe (ex: "3eme Sciences 2026-2027")
3. Selectionnez la matiere
4. Selectionnez le niveau scolaire
5. Creez

**Endpoint :** `POST /api/teacher/classes`

### Ajouter des eleves a une classe

**Pour ajouter un eleve :**
1. Selectionnez une classe
2. Cliquez sur **"Ajouter un eleve"**
3. Recherchez par nom ou email
4. Selectionnez l'eleve
5. L'eleve est ajoute a la classe

**Endpoint de recherche :** `GET /api/teacher/students/search?q={nom}`

**Endpoint d'ajout :** `POST /api/teacher/classes/{id}/students`

### Retirer un eleve

1. Selectionnez une classe
2. Selectionnez l'eleve a retirer
3. Cliquez sur **"Retirer"**
4. L'eleve est retire de la classe

**Endpoint :** `DELETE /api/teacher/classes/{id}/students/{sid}`

### Associer des cours a une classe

**Pour associer un cours :**
1. Selectionnez une classe
2. Cliquez sur **"Ajouter un cours"**
3. Selectionnez un de vos cours
4. Le cours est associe a la classe
5. Les eleves de la classe y auront acces

**Endpoint :** `POST /api/teacher/classes/{id}/courses`

### Supprimer une classe

1. Selectionnez la classe
2. Cliquez sur **"Supprimer"**
3. Confirmez

**Endpoint :** `DELETE /api/teacher/classes/{id}`

---

## 5. Creation de Contenu

### Cours (Academy)

**Pour creer un cours :**
1. Allez dans `Mes Cours`
2. Cliquez sur **"Creer un cours"**
3. Entrez le titre et la description
4. Selectionnez la matiere et le niveau
5. Definissez le statut de visibilite (`private`, `school`, `public`)
6. Definissez le statut pedagogique (`draft`, `pending_review`)
7. Enregistrez

**Endpoint :** `POST /api/academy/courses` ou `POST /api/courses`

**Cours "Mes Cours" :** `GET /api/academy/my-courses`

### Modules

**Pour creer un module :**
1. Selectionnez un cours
2. Cliquez sur **"Ajouter un module"**
3. Entrez le titre du module
4. Creez

**Endpoint :** `POST /api/academy/modules` ou `POST /api/courses/{id}/modules`

### Lecons

**Pour creer une lecon :**
1. Selectionnez un module
2. Cliquez sur **"Ajouter une lecon"**
3. Entrez le titre de la lecon
4. Ajoutez le contenu (texte, video, exercices)
5. Enregistrez

**Endpoint :** `POST /api/academy/lessons` ou `POST /api/courses/modules/{id}/lessons`

### Quizzes

**Pour creer un quiz :**
1. Selectionnez une lecon
2. Cliquez sur **"Creer un quiz"**
3. Ajoutez des questions
4. Definissez les reponses correctes
5. Enregistrez

**Endpoint :** `POST /api/academy/quizzes`

### Parcours (nouveau systeme)

Le systeme de Parcours est le nouveau format de contenu, base sur la structure officielle tunisienne.

**Pour creer un parcours :**
1. Allez dans `Parcours`
2. Cliquez sur **"Creer un parcours"**
3. Selectionnez la matiere
4. Selectionnez le niveau scolaire
5. Ajoutez des chapitres
6. Pour chaque chapitre, ajoutez des notions
7. Pour chaque notion, ajoutez des contenus (video, fiche, quiz, etc.)

**Endpoints :**
- `POST /api/parcours/` — creer un parcours
- `POST /api/parcours/{id}/chapitres` — ajouter un chapitre
- `POST /api/parcours/chapitres/{id}/notions` — ajouter une notion
- `POST /api/parcours/notions/{id}/contenus` — ajouter un contenu

### Elements Pedagogiques

Les elements pedagogiques sont des unites de contenu reutilisables.

**Pour creer un element :**
1. Allez dans `Elements`
2. Cliquez sur **"Creer un element"**
3. Selectionnez le type (`texte`, `video`, `image`, `quiz`, `pdf`)
4. Entrez le titre et le contenu
5. Definissez la difficulte (`basique`, `moyen`, `difficile`)
6. Enregistrez

**Workflow de validation :**
```
brouillon → en_review → publie → brouillon (retour en edition)
                   ↘ rejete → en_review (resoumission)
```

**Pour soumettre pour validation :** `POST /api/elements/{id}/submit`

---

## 6. Studio IA

### Acces

**Chemin :** `AI Studio`

**Condition :** State A uniquement (etait B ou C bloque l'acces)

> **Note :** Les enseignants beneficient d'une exemption speciale : ils peuvent utiliser la generation IA sans restriction de tier (ligne `ai.py:603`).

### Fonctionnalites

| Action | Description | Endpoint |
|--------|-------------|----------|
| **Generer un cours** | Generation complete d'un cours a partir d'un sujet | `POST /api/ai/generate` |
| **Ingestion PDF** | Integrer un document PDF dans le RAG | `POST /api/ai/ingest/pdf` |
| **Ingestion texte** | Integrer du texte dans le RAG | `POST /api/ai/ingest/text` |
| **Ingestion lecon** | Integrer le contenu d'une lecon dans le RAG | `POST /api/ai/ingest/lesson/{id}` |
| **Generer un quiz** | Creer des questions de quiz | `POST /api/ai/quiz` |
| **Generer des exercices** | Creer des exercices | `POST /api/ai/exercises` |

### Tuteur IA (tous les utilisateurs)

| Action | Description | Endpoint |
|--------|-------------|----------|
| **Poser une question** | Reponse streaming via SSE | `POST /api/ai/ask` |
| **Expliquer un concept** | Explication detaillee | `POST /api/ai/explain` |
| **Corriger un devoir** | Correction automatique | `POST /api/ai/correct` |

### Historique IA

| Action | Description | Endpoint |
|--------|-------------|----------|
| **Voir l'historique** | Historique de vos conversations IA | `GET /api/ai/history` |
| **Voir l'utilisation** | Credits IA utilises | `GET /api/ai/usage` |
| **Voir les stats** | Statistiques d'utilisation | `GET /api/ai/stats` |

### Exporter des messages IA

Vous pouvez exporter une reponse IA en PDF ou DOCX :
- `POST /api/conversations/export/message/pdf`
- `POST /api/conversations/export/message/docx`

---

## 7. Bibliotheque Globale & Parcours

### Rechercher dans la bibliotheque

**Endpoint :** `GET /api/bibliotheque/search`

Parametres :
- `q` : Texte de recherche (titre)
- `type` : Filtre par type (`texte`, `video`, `image`, `quiz`, `pdf`)
- `matiere` : Filtre par matiere
- `niveau_scolaire` : Filtre par niveau
- `difficulte` : Filtre par difficulte

Seuls les elements avec `statut="publie"` sont retournes.

### Consulter les competences

**Endpoint :** `GET /api/bibliotheque/competences`

Parametres :
- `matiere` : Filtre par matiere
- `niveau_scolaire` : Filtre par niveau

### Catalogue de parcours

**Chemin :** `Parcours Catalog`

Vous pouvez explorer les parcours officiels tunisiens crees par la plateforme.

---

## 8. Gestion des Evaluations (LMS)

### Creer un devoir (Assignment)

**Endpoint :** `POST /api/lms/assignments`

**Pour creer un devoir :**
1. Selectionnez une classe
2. Entrez le titre et la description
3. Definissez la date limite
4. Definissez le type (`homework`, `quiz`, `exam`)
5. Enregistrez

### Noter les soumissions

**Endpoint :** `PUT /api/lms/submissions/{id}/grade`

**Pour noter une soumission :**
1. Allez dans `Soumissions`
2. Selectionnez une soumission en attente
3. Entrez la note (0-20)
4. Ajoutez un commentaire
5. Enregistrez

### Voir toutes les soumissions

**Endpoint :** `GET /api/lms/submissions`

En tant qu'enseignant, vous voyez **toutes les soumissions** de votre ecole (pas uniquement les vôtres).

### Suivre la progression

**Endpoint :** `GET /api/lms/progress`

---

## 9. Finance & Revenus

### Portefeuille (Wallet)

| Action | Endpoint | Description |
|--------|----------|-------------|
| Voir le solde | `GET /api/wallet/balance` | Credits IA disponibles |
| Historique | `GET /api/wallet/history` | Transactions recentes |
| Acheter des credits | `POST /api/wallet/purchase` | Recharger le portefeuille |

### Revenus (Partenaires uniquement)

**Condition :** `user.is_partner == true`

| Action | Endpoint | Description |
|--------|----------|-------------|
| Rapport de revenus | `GET /api/teacher/revenue-report` | Revenus totaux, taux de commission, nombre de vues |
| Historique des revenus | `GET /api/teacher/revenue-history` | Detaille par cours et par mois |

**Taux de commission :** 5% du montant par vue premium d'eleve par lecon par mois.

### Ventes de cours

**Endpoint :** `GET /api/courses/my-sales`

---

## 10. Souscriptions & Packs

### Consulter les packs disponibles

**Endpoint :** `GET /api/abonnements/packs`

### Consulter mes abonnements

**Endpoint :** `GET /api/abonnements/mes-abonnements`

### Souscrire a un pack

**Endpoint :** `POST /api/abonnements`

### Changer de tier

**Endpoint :** `POST /api/abonnements/change-tier`

### Annuler un abonnement

**Endpoint :** `DELETE /api/abonnements/{id}/cancel`

**Delai de grace :** 7 jours avant la fin effective.

---

## Recapitulatif des permissions

### Ce que vous POUVEZ faire (Teacher)

| Action | Condition |
|--------|-----------|
| Creer des cours, modules, lecons | State A |
| Creer des quizzes | State A |
| Gestion de classes (creer, ajouter/retirer eleves) | Toujours |
| Associer des cours a des classes | Toujours |
| Noter les soumissions | Toujours |
| Utiliser le Studio IA | State A |
| Ingerer des documents dans le RAG | State A |
| Generer du contenu par IA | State A |
| Rechercher dans la bibliotheque | Toujours |
| Consulter les parcours | Toujours |
| Consulter le portefeuille | Toujours |
| Acheter des credits | Toujours |
| Voir les revenus (partenaires) | is_partner = true |
| Soumettre des elements pour validation | State A |
| Valider le contenu des autres (Pedagogical Lead) | Si pedagogical_lead |
| Exporter des messages IA (PDF/DOCX) | Toujours |

### Ce que vous NE POUVEZ PAS faire

| Action | Qui peut le faire |
|--------|-------------------|
| Approuver pour le B2B | Admin Pedagogique |
| Valider localement les cours | Leader Pedagogique |
| Gestion des finances plateforme | Super-Admin |
| Parametres plateforme | Super-Admin |
| Importer des eleves par CSV | Admin Ecole |
| Acheter des packs ecole | Admin Ecole |
| Reassigner les enseignants | Leader Pedagogique |

---

## Partie Enseignant : COMPLETE

Le document couvre :
- Les 3 sous-etats du compte (A/B/C) avec conditions et consequences
- Tableau de bord et widgets
- Gestion des classes (creation, eleves, cours associes)
- Creation de contenu (cours, modules, lecons, quizzes, parcours, elements)
- Studio IA (generation, ingestion, historique, export)
- Bibliotheque globale et parcours
- Gestion des evaluations LMS
- Finance, revenus et souscriptions

**Pret pour le role suivant : Eleve (Student)**

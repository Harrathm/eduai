# Guide Utilisateur EDUAI Learning - Leader Pedagogique (Pedagogical Lead)

> **Version** : 1.0 — Aout 2026
> **Branche** : phase1-critical
> **Derniere mise a jour** : 06/08/2026

---

## Table des matieres

1. [Introduction au Role](#1-introduction-au-rle)
2. [Validation Locale des Cours](#2-validation-locale-des-cours)
3. [Reassignation des Enseignants](#3-reassignation-des-enseignants)
4. [Suivi de la Performance & Progression](#4-suivi-de-la-performance--progression)
5. [Gestion des Objectifs Trimestriels](#5-gestion-des-objectifs-trimestriels)
6. [Validation des Elements Pedagogiques](#6-validation-des-elements-pdagogiques)
7. [Administration de l'Ecole (scope)](#7-administration-de-lcole-scope)

---

## 1. Introduction au Role

### Qui est le Leader Pedagogique ?

Le Leader Pedagogique (`pedagogical_lead`) est un role **scope a une ecole**. Sa mission est d'assurer la **qualite pedagogique locale** — c'est-dire valider les contenus d'enseignants de son ecole et suivre la progression des eleves.

Ce role est defini dans le code backend comme `pedagogical_lead` et est autorise par la dependance `require_pedagogical_lead` (fichier `deps.py:128`).

### Perimetre d'action vs Super-Admin vs Admin Pedagogique

| Capacite | Super-Admin | Admin Pedagogique | **Leader Pedagogique** |
|----------|-------------|-------------------|----------------------|
| Validation B2B des cours | Oui | Oui (exclusif) | **Non** |
| **Validation LOCALE des cours** | Oui | Oui | **Oui (exclusif)** |
| **Reassignation enseignants** | Oui | Non | **Oui** |
| **Suivi progression eleves** | Oui | Non | **Oui** |
| **Objectifs trimestriels classe** | Oui | Non | **Oui** |
| Gestion de l'arborescence | Oui | Oui | Oui (scope ecole) |
| Gestion des ecoles | Oui | Non | Non |
| Mode maintenance | Oui | Non | Non |
| Finances | Oui | Non | Non |

**Principe fondamental :** Le Leader Pedagogique **approuve localement** (pour une seule ecole), tandis que l'Admin Pedagogique **approuve pour le B2B** (toutes les ecoles).

### Le Context Switcher

Si votre compte possede plusieurs roles (ex: `["admin_school", "pedagogical_lead"]`), un **dropdown de contexte** apparait dans la barre laterale. Selectionnez le role **"Leader Pedagogique"** pour activer les permissions pedagogiques de votre ecole.

**Important :** Le role `pedagogical_lead` est **scope a votre ecole** — vous ne voyez que les donnees de votre propre ecole.

### Droits d'administration

Le Leader Pedagogique a **egalement** les droits `require_admin` et `require_school_admin` sur les pages suivantes :

- `Admin Panel` > `Users` — Gestion des utilisateurs
- `Admin Panel` > `Courses` — Gestion des cours
- `Admin Panel` > `Teachers` — Validation des enseignants
- `Admin Panel` > `Pedagogie` — **Exclusif au Leader Pedagogique**
- `Admin Panel` > `Wallets` — Consultation des portefeuilles
- `Admin Panel` > `Audit Logs` — Journaux d'audit

**Pages masquees pour le Leader Pedagogique :**
- `Admin Panel` > `Finance` — Masque dans la sidebar
- `Admin Panel` > `Settings` — Masque dans la sidebar

---

## 2. Validation Locale des Cours

### La page Pedagogie

**Chemin :** `Admin Panel` > `Pedagogie`

> **Note :** C'est la seule page reservee exclusivement au role `pedagogical_lead`. Elle n'est visible que par ce role dans la barre laterale.

**Comment acceder :**
1. Connectez-vous avec un compte `pedagogical_lead`
2. Cliquez sur **"Pedagogie"** dans la barre laterale
3. La page affiche :
   - **KPIs de performance** : Enseignants, Cours actifs, Taux d'achèvement
   - **Filtres de statut** : Tous / En attente / Approuves / Rejetes
   - **Liste des cours** avec actions

### Filtres de statut

| Filtre | Description |
|--------|-------------|
| `Tous` | Affiche tous les cours de l'ecole |
| `En attente` | Cours avec statut `pending_review` (en attente de validation) |
| `Approuves` | Cours avec statut `approved_local` |
| `Rejetes` | Cours avec statut `rejected` ou `revision_requested` |

### Validation d'un cours

**Pour valider un cours :**
1. Selectionnez un cours avec le statut `pending_review`
2. Cliquez sur le bouton vert **"Approuver"**
3. Un appel `PUT /api/pedagogical-lead/courses/{course_id}/review-local` est effectue avec `action: "approve_local"`
4. Le cours passe en statut `approved_local`
5. Le cours devient accessible aux eleves de **votre ecole uniquement**
6. Un toast de confirmation vert s'affiche : *"Cours approuve pour l'ecole"*

**Pour demander une revision :**
1. Selectionnez un cours avec le statut `pending_review`
2. Cliquez sur le bouton orange **"Rejeter"**
3. Un appel `PUT /api/pedagogical-lead/courses/{course_id}/review-local` est effectue avec `action: "reject"`
4. Le cours passe en statut `revision_requested`
5. L'enseignant sera notifie et pourra corriger son cours

**Pour escalader a la plateforme :**
1. Selectionnez un cours avec le statut `pending_review`
2. Cliquez sur le bouton violet **"Escalader"**
3. Un appel `POST /api/pedagogical-lead/escalate/{course_id}` est effectue
4. Le cours passe en statut `pending_review` avec une notification a l'Admin Pedagogique
5. L'Admin Pedagogique pourra alors l'approuver pour le B2B (toutes les ecoles)

### Cycle de vie d'un cours

```
draft → pending_review → approved_local → approved_for_b2b → published
                     ↘ needs_revision → pending_review (resoumission)
                     ↘ archived
```

**Transition interdite :** Le Leader Pedagogique **ne peut PAS** mettre un cours en statut `approved_for_b2b`. Seul l'Admin Pedagogique le peut.

---

## 3. Reassignation des Enseignants

### Le contexte

Lorsqu'un enseignant est indisponible (maladie, depart temporaire...), le Leader Pedagogique peut **reassigner temporairement** sa classe a un autre enseignant.

**Endpoint :** `POST /api/pedagogical-lead/classes/{class_id}/reassign-teacher`

**Pour reassigner un enseignant :**
1. Selectionnez la classe a reassigner
2. Entrez l'ID de l'enseignant remplacement (`replacement_teacher_id`)
3. Definissez la date de fin (`end_date`)
4. Definissez la raison (`reason` : maladie, formation, autre)
5. Envoyez la demande

**Effets :**
- Un enregistrement `Assignment` est cree avec `is_temporary = true`
- L'enseignant remplacement prend le controle de la classe
- A la date de fin, l'enseignant original est restaure automatiquement

### Gestion des remplacements

**Pour valider un remplacement :**
1. Selectionnez l'assignation en attente
2. Cliquez sur **"Valider"**
3. L'assignation passe en statut `approved`

**Reporter un remplacement :**
1. Selectionnez l'assignation active
2. Entrez une nouvelle date de fin
3. Definissez la raison du report
4. L'assignation est mise a jour

**Endpoint :** `PUT /api/pedagogical-lead/assignments/{assignment_id}/postpone`

---

## 4. Suivi de la Performance & Progression

### Progression par classe et matiere

**Endpoint :** `GET /api/pedagogical-lead/progress-report`

Parametres :
- `classroom_id` : ID de la classe (optionnel)
- `matiere_id` : ID de la matiere (optionnel)

Retourne :
- Taux de progression des eleves par classe
- Taux de completion par matiere
- Alertes pour les eleves en retard

### Performance agregee

**Endpoint :** `GET /api/pedagogical-lead/performance`

Parametres :
- `classroom_id` : ID de la classe (optionnel)
- `period` : `month`, `trimester`, `year` (optionnel)

Retourne :
- Moyenne generale par classe
- Taux de reussite par matiere
- Taux d'engagement des eleves
- Top 5 des eleves les plus actifs

### Analyse des questions IA

**Endpoint :** `GET /api/pedagogical-lead/ai-questions-analysis`

Parametres :
- `limit` : Nombre de questions (defaut: 10)

Retourne :
- Les questions les plus posees par les eleves a l'IA
- Frequence de chaque question
- Categorie de chaque question

**Utilite :** Identifier les points faibles communs dans la classe pour adapter l'enseignement.

---

## 5. Gestion des Objectifs Trimestriels

### Definir des objectifs pour une classe

**Endpoint :** `POST /api/pedagogical-lead/goals/quarterly`

**Pour definir un objectif trimestriel :**
1. Selectionnez une classe
2. Selectionnez une matiere
3. Entrez le nom de l'objectif (ex: "Maitriser les fractions")
4. Definissez le type : `annual` ou `quarterly`
5. Si `quarterly`, selectionnez le trimestre : `T1`, `T2`, ou `T3`
6. Definissez les cibles (score minimum, taux de completion)
7. Envoyez

**Effets :**
- L'objectif est cree pour **tous les eleves de la classe**
- Chaque eleve verra l'objectif dans son tableau de bord
- Le suivi est automatique (pas besoin de mettre a jour manuellement)

### Vue d'ensemble des objectifs trimestriels

**Endpoint :** `GET /api/pedagogical-lead/goals/quarterly-overview`

Parametres :
- `classroom_id` : ID de la classe (optionnel)
- `trimester` : `T1`, `T2`, `T3` (optionnel)

Retourne :
- Nombre d'objectifs par classe
- Taux d'atteinte global
- Detail par eleve

### Objectifs individuels

En plus des objectifs de classe, le Leader Pedagogique peut aussi creer des **objectifs individuels** pour des eleves specifiques.

**Endpoint :** `POST /api/goals`

**Pour definir un objectif individuel :**
1. Selectionnez un eleve
2. Selectionnez une matiere
3. Entrez le nom de l'objectif
4. Definissez le type : `annual`, `monthly`, ou `custom`
5. Definissez les cibles

---

## 6. Validation des Elements Pedagogiques

### Elements en attente de validation

Les enseignants de votre ecole soumettent des elements pedagogiques (lecons, quizzes, videos...) pour validation. Vous etes le premier niveau de validation avant la promotion a la bibliotheque globale.

### Valider un element

**Endpoint :** `POST /api/elements/{element_id}/validate`

**Pour valider un element :**
1. Selectionnez un element en statut `en_review`
2. Verifiez le contenu
3. Cliquez sur **"Valider"**
4. L'element passe en statut `publie`
5. Si `est_global = false`, l'element reste dans le repertoire de l'ecole

### Rejeter un element

**Endpoint :** `POST /api/elements/{element_id}/reject`

**Pour rejeter un element :**
1. Selectionnez un element en statut `en_review`
2. Ajoutez un commentaire de rejet
3. Cliquez sur **"Rejeter"**
4. L'element passe en statut `rejete`
5. L'enseignant sera notifie

### Promouvoir vers la bibliotheque globale

**Endpoint :** `POST /api/elements/{element_id}/promote-global`

**Pour promouvoir un element :**
1. Selectionnez un element publie (`statut = "publie"`)
2. Cliquez sur **"Promouvoir global"**
3. L'element devient visible par **toutes les ecoles**
4. Un snapshot `ContentPromotion` est cree pour tracer l'historique

---

## 7. Administration de l'Ecole (scope)

### Gestion des utilisateurs

Le Leader Pedagogique a acces aux fonctionnalites d'administration de l'ecole (scope ecole) via les droits `require_admin` et `require_school_admin`.

**Actions disponibles :**
- Consulter la liste des utilisateurs
- Creer des comptes eleves et enseignants
- Modifier les informations utilisateur
- Reinitialiser les mots de passe
- Gestion des classes et inscriptions

### Gestion des cours

Le Leader Pedagogique peut aussi gerer les cours de son ecole.

**Actions disponibles :**
- Consulter la liste des cours
- Creer des cours (a l'echelle de l'ecole)
- Modifier les metadonnees des cours
- Supprimer des cours

### Validation des enseignants

Le Leader Pedagogique peut valider les inscriptions des enseignants.

**Actions disponibles :**
- Consulter les inscriptions en attente
- Approuver ou rejeter une inscription
- Voir le detail d'un enseignant

### Portefeuilles

Le Leader Pedagogique peut **consulter** les portefeuilles des utilisateurs de son ecole.

**Endpoint :** `GET /api/admin/wallets` (scope ecole)

### Journaux d'audit

Le Leader Pedagogique peut consulter l'historique des actions dans son ecole.

**Endpoint :** `GET /api/admin/audit-logs` (scope ecole)

---

## Recapitulatif des permissions

### Ce que vous POUVEZ faire (Pedagogical Lead)

| Action | Endpoint | Scope |
|--------|----------|-------|
| Approuver un cours localement | `PUT /api/pedagogical-lead/courses/{id}/review-local` | Votre ecole |
| Rejeter un cours | `PUT /api/pedagogical-lead/courses/{id}/review-local` | Votre ecole |
| Escalader un cours a la plateforme | `POST /api/pedagogical-lead/escalate/{id}` | Votre ecole |
| Reassigner un enseignant | `POST /api/pedagogical-lead/classes/{id}/reassign-teacher` | Votre ecole |
| Reporter un remplacement | `PUT /api/pedagogical-lead/assignments/{id}/postpone` | Votre ecole |
| Voir la progression par classe | `GET /api/pedagogical-lead/progress-report` | Votre ecole |
| Voir la performance | `GET /api/pedagogical-lead/performance` | Votre ecole |
| Analyser les questions IA | `GET /api/pedagogical-lead/ai-questions-analysis` | Votre ecole |
| Definir des objectifs trimestriels | `POST /api/pedagogical-lead/goals/quarterly` | Votre ecole |
| Voir les objectifs trimestriels | `GET /api/pedagogical-lead/goals/quarterly-overview` | Votre ecole |
| Valider des elements pedagogiques | `POST /api/elements/{id}/validate` | Votre ecole |
| Rejeter des elements pedagogiques | `POST /api/elements/{id}/reject` | Votre ecole |
| Promouvoir vers la bibliotheque globale | `POST /api/elements/{id}/promote-global` | Global |
| Creer des competences | `POST /api/bibliotheque/competences` | Global |
| Consulter les utilisateurs | `GET /api/admin/users` | Votre ecole |
| Gerer les classes | `GET/POST /api/admin/classes` | Votre ecole |
| Consulter les analytics | `GET /api/admin/analytics/*` | Votre ecole |

### Ce que vous NE POUVEZ PAS faire

| Action | Qui peut le faire |
|--------|-------------------|
| Approuver pour le B2B (toutes les ecoles) | Admin Pedagogique uniquement |
| Gestion des finances | Super-Admin uniquement |
| Parametres plateforme | Super-Admin uniquement |
| Mode maintenance | Super-Admin uniquement |
| Acheter des packs ecole | Admin Ecole uniquement |
| Importer des eleves par CSV | Admin Ecole uniquement |
| Ajuster les soldes des utilisateurs | Super-Admin uniquement |
| Approuver des ecoles | Super-Admin uniquement |
| Statistiques globales | Super-Admin uniquement |

---

## Partie Leader Pedagogique : COMPLETE

Le document couvre :
- Introduction au role avec distinction Super-Admin vs Admin Pedagogique vs Leader Pedagogique
- Validation locale des cours (workflow complet)
- Reassignation des enseignants
- Suivi de la progression et performance
- Gestion des objectifs trimestriels (classe et individuels)
- Validation des elements pedagogiques
- Administration de l'ecole (scope)
- Tableau recapitulatif des permissions

**Pret pour le role suivant : Enseignant (Teacher)**

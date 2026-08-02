# 📖 Guide d'Utilisation Complet — EDUAI Learning

## Table des Matières
1. [Architecture Globale](#1-architecture-globale)
2. [Rôles et Permissions](#2-rôles-et-permissions)
3. [Guide Super-Admin](#3-super-admin)
4. [Guide Admin Pédagogique](#4-admin-pédagogique)
5. [Guide Admin École](#5-admin-école)
6. [Guide Responsable Pédagogique (Pedagogical Lead)](#6-responsable-pédagogique)
7. [Guide Enseignant](#7-enseignant)
8. [Guide Élève](#8-élève)
9. [Guide Parent](#9-parent)
10. [Fonctionnalités Transversales](#10-fonctionnalités-transversales)
11. [Système de Données](#11-système-de-données)

---

## 1. Architecture Globale

### Stack technique
| Couche | Technologie |
|--------|------------|
| Backend | Python 3.14, FastAPI, SQLAlchemy 2.0 (async), pg8000 |
| Frontend | React 19, TypeScript, Vite, TanStack Query, TailwindCSS |
| Base | PostgreSQL |
| Cache | Redis (rate-limiting) |
| Stockage | S3/MinIO (fichiers media) |
| IA | Groq (Llama 3.3), OpenAI, 9 providers supportés |
| Paiements | Stripe (subscriptions) + portefeuille interne DT |
| Scheduler | APScheduler (goals, expirations) |

### Multi-tenancy
- Chaque école est un **tenant** isolé
- Filtre automatique `school_id` au niveau base de données (event listener SQLAlchemy)
- Les rôles globaux (`super_admin`, `pedagogical_admin`) contournent le filtre

### Authentification
- JWT token (header `Authorization: Bearer <token>`)
- Inscription via `/auth/register` (mot de passe: 8+ caractères, lettre + chiffre)
- Login via `/auth/login` → retourne `access_token` + `user`
- Rédirection automatique par rôle après connexion

---

## 2. Rôles et Permissions

| Rôle | Portée | Description |
|------|--------|-------------|
| `super_admin` | **Globale** (toutes écoles) | Administrateur plateforme. Accès total. |
| `pedagogical_admin` | **Globale** (toutes écoles) | Admin pédagogique. Révision cours, rapports, escalades. |
| `admin_school` | **École** (school_id) | Administrateur d'école. Gestion complète de son école. |
| `pedagogical_lead` | **École** (school_id) | Responsable pédagogique local. Validation cours, objectifs, réorientations. |
| `teacher` | **École** (school_id) | Enseignant. Création cours, classes, suivi élèves. |
| `student` | **École** (school_id) | Élève. Apprentissage, quizzes, IA tuteur, gamification. |
| `parent` | **École** (school_id) | Parent. Consultation seule du suivi de ses enfants. |

### Matrice de permissions

| Fonctionnalité | super_admin | pedagogical_admin | admin_school | pedagogical_lead | teacher | student | parent |
|----------------|:-----------:|:------------------:|:------------:|:----------------:|:-------:|:-------:|:------:|
| Gérer les écoles | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Gérer tous les users | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Gérer users de son école | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Config plateforme | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Audit logs | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Packages de tokens | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Codes d'invitation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Révision cours (toutes écoles) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Rapports pédagogiques (global) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| AI Factory | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Validation contenu | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Réorientations | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Objectifs pédagogiques | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Créer/modifier cours | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Créer classes | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Devoirs / notes | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Gérer finances école | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Wallet (solde) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| IA Tuteur | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Acheter packs | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Suivi élèves | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Gamification | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Voir ses enfants | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 3. Super-Admin

**URL:** `http://localhost:5173/dashboard/admin`
**Layout:** Admin sidebar latérale avec 18 sections

### 3.1 Tableau de bord (`/dashboard/admin`)

**Page:** `AdminDashboardPage.tsx`
**Endpoint:** `GET /api/admin/dashboard`

Fonctionnalités :
- **KPIs en haut** : Chiffre d'affaires total (DT), MRR (Revenu Mensuel Récurrent), ARR (Annuel), Nombre total d'utilisateurs, Tokens vendus, Total cours
- **Graphiques** : Tendances d'inscription, Coûts API IA
- **Distribution** : Répartition élèves/enseignants, Répartition par forfait
- **Stats rapides** : Cours en attente, Cours publiés, Transactions, Inscriptions enseignants en attente
- **Top écoles** par revenu
- **Sélecteur de période** : 7j / 30j / 90j / 12 mois

### 3.2 Gestion des Utilisateurs (`/dashboard/admin/users`)

**Page:** `AdminUsersPage.tsx`
**Endpoints:**
- `GET /api/admin/users` — Liste paginée avec filtres
- `GET /api/admin/users/{id}` — Détail utilisateur
- `PUT /api/admin/users/{id}` — Modifier
- `DELETE /api/admin/users/{id}` — Supprimer (super_admin uniquement)

Fonctionnalités :
- **Table paginée** avec recherche par nom/email
- **Filtres** : Rôle (tous/student/teacher/admin_school/pedagogical_admin/pedagogical_lead/super_admin), Statut (actif/inactif)
- **Actions** : Créer utilisateur, Modifier, Ajouter/Déduire tokens ou DT, Changer rôle, Activer/Désactiver, Supprimer
- **KPIs** : Total utilisateurs, Actifs, Tokens en circulation, DT en circulation
- **Export CSV** de la liste

### 3.3 Gestion des Écoles (`/dashboard/admin/schools`)

**Page:** `AdminSchoolsPage.tsx`
**Endpoints:**
- `GET /api/admin/schools` — Liste paginée
- `GET /api/admin/schools/{id}` — Détail école
- `POST /api/admin/schools` — Créer
- `PUT /api/admin/schools/{id}` — Modifier
- `DELETE /api/admin/schools/{id}` — Supprimer

Fonctionnalités :
- **Table paginée** avec recherche
- **Filtres** : Tier (FREE/TEACHER_PRO/SCHOOL/INSTITUTION), Statut
- **CRUD** : Créer, Modifier (nom, domaine, forfait, max_users, actif), Supprimer
- **KPIs** : Total écoles, Actives, Free tier, Institution

### 3.4 Distribution de Cours (`/dashboard/admin/course-distribution`)

**Page:** `SchoolCourseDistribution.tsx`

- Gère l'accès aux cours par école
- Affiche par école : cours accordés, utilisateurs inscrits, compteurs élèves/enseignants
- Actions : Accorder/Révoquer l'accès à un cours pour une école

### 3.5 Catalogue Enseignants (`/dashboard/admin/teacher-catalog`)

**Page:** `SuperAdminCourseFactory.tsx`

- Vue d'ensemble de toutes les classes d'enseignants
- Détails extensibles par classe (cours, inscriptions)
- Recherche

### 3.6 Gestion des Cours (`/dashboard/admin/courses`)

**Page:** `AdminCoursesPage.tsx` + `CourseEditorPage.tsx`
**Endpoints:**
- `GET /admin-courses` — Liste
- `POST /admin-courses` — Créer
- `PUT /admin-courses/{id}` — Modifier
- `DELETE /admin-courses/{id}` — Supprimer
- `PUT /admin-courses/{id}/status` — Changer statut
- `POST /admin-courses/bulk-publish` — Publication massive

Fonctionnalités :
- **Filtres** : Statut (draft/published/archived), Catégorie, Niveau (beginner/intermediate/advanced), Statut pédagogique (draft/pending_review/rejected/approved_for_platform/approved_for_b2b/revision_requested)
- **Actions** : Publier/Dépublier, Dupliquer, Archiver, Soumettre pour révision, Modifier (éditeur complet), Prévisualiser, Supprimer
- **Éditeur de cours** (`CourseEditorPage`) : Gestion chapters/leçons avec drag-and-drop, Types de leçons (texte/vidéo/PDF/image/lien/quiz), Paramètres (titre, description, catégorie, niveau, visibilité, prix tokens/DT)

### 3.7 Révision Pédagogique (`/dashboard/admin/pedagogical-review`) — **PEDAGOGICAL_ADMIN uniquement**

**Page:** `PedagogicalAdminPage.tsx`
**Endpoints:**
- `GET /pedagogical/pending-courses` — Cours en attente
- `POST /pedagogical/courses/{id}/approve` — Approuver
- `POST /pedagogical/courses/{id}/reject` — Rejeter

- Révision des cours soumis pour approbation pédagogique
- Filtre par statut pédagogique
- Actions : Approuver pour B2B, Demander révision

### 3.8 Arborescence Pédagogique (`/dashboard/admin/arborescence`)

**Page:** `AdminArborescencePage.tsx`

- Éditeur hiérarchique : Niveaux d'étude → Matières → Chapitres → Notions
- Vue arborescente avec expand/collapse
- Édition inline (renommer), Création/Suppression à chaque niveau

### 3.9 Statut de Publication (`/dashboard/admin/publication-status`)

**Page:** `AdminPublicationStatusPage.tsx`

- État de publication de toutes les Notions
- Chaque notion affiche : matière, chapitre, si le contenu est complet (publiable) ou brouillon
- Filtre par statut publiable/brouillon

### 3.10 Centre Financier (`/dashboard/admin/finance`)

**Page:** `FinanceCenter.tsx`
**Endpoints:**
- `GET /wallet/balance` — Soldes
- `PUT /api/admin/users/{id}/balance` — Ajuster solde
- `POST /api/admin/wallets/{id}/add` — Créditer
- `POST /api/admin/wallets/{id}/deduct` — Débiter

- Liste paginée de tous les portefeuilles utilisateurs
- Recherche, Solde DT, Solde tokens
- Actions : Ajouter/Déduire DT ou tokens avec motif
- **Stats globales** : Total utilisateurs, Total DT, Total tokens, Total transactions

### 3.11 Analytics (`/dashboard/admin/analytics`)

**Page:** `AdminAnalyticsPage.tsx`
**Endpoint:** `GET /api/admin/analytics`

- **KPIs** : CA total, MRR, ARR, Transactions, Coût IA estimé, Profit estimé, Utilisateurs actifs, Taux de conversion
- Répartition des revenus par devise
- Résumé plateforme (users, cours, publiés, en attente)
- Distribution par forfait
- Sélecteur de période

### 3.12 File d'attente Enseignants (`/dashboard/admin/teachers`)

**Page:** `AdminTeacherQueuePage.tsx`
**Endpoints:**
- `GET /api/admin/teacher-registrations` — Liste
- `PUT /api/admin/teacher-registrations/{id}` — Approuver/Rejeter

- Table des candidatures enseignants (pending/approved/rejected)
- Infos : nom, email, qualifications, expérience, école
- **KPIs** : Total, En attente, Approuvés, Rejetés
- Actions : Approuver ou Rejeter (avec motif optionnel)

### 3.13 Packages de Tokens (`/dashboard/admin/packages`)

**Page:** `AdminTokenPackagesPage.tsx`

- CRUD des packages de tokens (nom, montant tokens, prix DT, tokens bonus, actif)
- Table avec édition/suppression/création

### 3.14 Codes d'Invitation (`/dashboard/admin/invite-codes`)

**Page:** `AdminInviteCodesPage.tsx`

- Liste de toutes les écoles avec leurs codes d'invitation
- Actions : Copier le code, Régénérer le code

### 3.15 Journal d'Audit (`/dashboard/admin/audit`)

**Page:** `AdminAuditLogPage.tsx`
**Endpoints:**
- `GET /api/admin/logs/audit` — Journal paginé

- Traçabilité de toutes les actions admin : user.create, user.update, user.delete, user.role_change, user.balance_adjust, school.create, school.update, course.publish, course.unpublish, registration.approve, registration.reject
- Affiche : email admin, action, cible, détails, IP, timestamp

### 3.16 Configuration Seuils (`/dashboard/admin/seuils-config`)

**Page:** `AdminSeuilsConfigPage.tsx`
**Endpoint:** `PUT /pedagogical/adaptive-pathway/seuils/{matiere_id}`

- Configuration des seuils par matière : remediation (<40%), standard (<75%), avancé (>75%)
- Valeurs par défaut pour toutes les matières

### 3.17 Spécialités Pédagogiques (`/dashboard/admin/specialites-pedagogiques`)

**Page:** `AdminSpecialitesPedagogiquesPage.tsx`
**Endpoints:**
- `GET /pedagogical/adaptive-pathway/specialites-pedagogiques`
- `POST /pedagogical/adaptive-pathway/specialites-pedagogiques`
- `PUT /pedagogical/adaptive-pathway/specialites-pedagogiques/{id}`
- `DELETE /pedagogical/adaptive-pathway/specialites-pedagogiques/{id}`
- `POST /pedagogical/adaptive-pathway/responsables-pedagogiques`
- `GET /pedagogical/adaptive-pathway/responsables-pedagogiques`

- CRUD des spécialités pédagogiques (nom, cycle scolaire, matières associées)
- Assignation de responsables pédagogiques avec scope niveaux d'étude

### 3.18 AI Factory (`/dashboard/admin/ai-factory`)

**Page:** `ContentCreatorAI.tsx`
**Endpoints:**
- `POST /api/admin/ai-factory/generate-plan` — Générer plan
- `POST /api/admin/ai-factory/generate-content` — Générer contenu
- `POST /api/admin/ai-factory/generate-quiz` — Générer quiz
- `POST /api/admin/ai-factory/stream` — Streaming IA

- **Assistant de création IA en 4 étapes** :
  1. Saisir le sujet, activer RAG optionnel
  2. L'IA génère le plan (modules + leçons), éditable
  3. Générer le contenu leçon par leçon avec streaming
  4. Prévisualiser et publier directement
- Supporte la génération d'images par leçon

### 3.19 Centre de Diffusion (`/dashboard/admin/broadcast`)

**Page:** `BroadcastCenter.tsx`
**Endpoint:** `POST /api/admin/messages`

- Envoi de messages en masse à : tous les utilisateurs, enseignants uniquement, élèves uniquement, admins uniquement
- Sujet + corps du message
- Historique des messages avec nombre de destinataires

### 3.20 Messagerie Admin (`/dashboard/admin/inbox`)

**Page:** `AdminInboxView.tsx`
**Endpoints:**
- `GET /inbox` — Messages reçus
- `GET /inbox/sent` — Messages envoyés
- `POST /inbox` — Envoyer

- Onglets : Boîte de réception, Envoyer, Composer
- Composer supporte diffusion et messages directs

### 3.21 Paramètres Plateforme (`/dashboard/admin/settings`)

**Page:** `AdminSettingsPage.tsx`
**Endpoint:** `GET/PUT /api/admin/settings`

**6 onglets :**
1. **Général** : Nom plateforme, domaine
2. **Fournisseurs IA** : Configuration de 9 fournisseurs (FreeTokenFaucet, NVIDIA, OpenAI, Groq, OpenRouter, MiniMax, Anthropic, Azure, Google) avec clés API et sélection de modèle
3. **Tarification** : Coûts en tokens par fonctionnalité
4. **Limites de tokens** : Limites de débit
5. **Maintenance** : Mode maintenance, autoriser inscriptions enseignants, autoriser nouveaux comptes
6. **Logs d'erreur** : Visualiseur d'erreurs système

### 3.22 Bibliothèque Média (`/dashboard/admin/media`)

**Page:** `AdminMediaLibraryPage.tsx`
**Endpoints:**
- `POST /media/upload` — URL de pré-upload
- `GET /media/download/{id}` — Téléchargement
- `DELETE /media/{id}` — Suppression

- Upload, parcourir, filtrer et supprimer les fichiers média
- Métadonnées : nom, type MIME, taille, date d'upload

---

## 4. Admin Pédagogique

**Rôle :** `pedagogical_admin`
**Portée :** Globale (toutes les écoles)
**Layout :** AdminLayout (partagé avec super_admin)

Le pedagogical_admin a accès à l'ensemble des pages admin avec **une section supplémentaire** : **Révision Pédagogique**. Il n'a PAS accès à la gestion des écoles, des utilisateurs ou des finances.

### Fonctionnalités spécifiques

| Section | Accès | Description |
|---------|-------|-------------|
| Overview | ✅ | Tableau de bord plateforme |
| Users | ✅ | Lecture seule |
| Schools | ✅ | Lecture seule |
| Courses | ✅ | Lecture + révision |
| **Review Pedago.** | ✅ | **Spécifique** — Révision des cours pédagogiques |
| Arborescence | ✅ | Gestion de l'arborescence |
| Statut Publication | ✅ | Suivi de publication |
| Analytics | ✅ | Performances financières |
| AI Factory | ✅ | Génération de contenu IA |
| Inbox | ✅ | Messagerie |

### Actions pédagogiques

1. **Réviser un cours** : Voir les détails, approuver pour B2B ou demander révision
2. **Rapports pédagogiques** : `GET /pedagogical/reports` — Statistiques pédagogiques globales
3. **Escalades** : `GET /pedagogical/escalations` — Voir les cours escaladés
4. **Résoudre une escalade** : `POST /pedagogical/escalations/{id}/resolve`

---

## 5. Admin École

**Rôle :** `admin_school`
**Portée :** École (school_id)
**Layout:** `SchoolAdminLayout.tsx`

### 5.1 Vue d'ensemble (`/dashboard/school`)

**Page:** `SchoolOverview.tsx`
**Endpoint:** `GET /api/admin/dashboard`

- Stats de l'école : total utilisateurs, enseignants, élèves, cours (en attente/publicés), inscriptions enseignants en attente
- Cartes de stats rapides

### 5.2 Gestion des Utilisateurs (`/dashboard/school/users`)

**Page:** `UserManagementView.tsx`
**Endpoints:**
- `GET /api/admin/users` — Liste filtrée par école
- `PUT /api/admin/users/{id}` — Modifier
- `POST /api/admin/user-update` — Mettre à jour

- Mêmes fonctionnalités que le super_admin mais limité à son école
- **Import CSV** : Upload de fichier CSV pour créer plusieurs comptes élèves en une fois
- Recherche, filtre par rôle, Ajouter/Déduire tokens/DT

### 5.3 Finance (`/dashboard/school/finance`)

**Page:** `FinanceCenter.tsx`

- Portefeuilles des utilisateurs de l'école
- Ajouter/Déduire DT ou tokens
- Stats de l'école

### 5.4 Gestion des Cours (`/dashboard/school/courses`)

**Page:** `AdminCoursesPage.tsx` + `CourseEditorPage.tsx`

- Mêmes fonctionnalités que le super_admin pour les cours
- Créer, Modifier, Publier, Archiver, Dupliquer cours
- Éditeur complet avec chapters et leçons
- Gestion des quiz

### 5.5 File d'attente Enseignants (`/dashboard/school/teachers`)

**Page:** `AdminTeacherQueuePage.tsx`

- Candidatures enseignants de l'école
- Approuver/Rejeter

### 5.6 Paramètres École (`/dashboard/school/settings`)

**Page:** `AdminSettingsPage.tsx`

- Paramètres de l'école (nom, domaine, configuration)

### 5.7 Fonctionnalités exclusives admin_school

- **Créer des classes** : `POST /api/admin/classes`
- **Gérer les inscriptions** : `POST /api/admin/enrollments`
- **Créer des devoirs** : `POST /api/admin/assignments`
- **Noter les soumissions** : `PUT /api/admin/submissions/{id}`
- **Assigner des enseignants** : `POST /api/admin/schools/{id}/assign-teacher`
- **Gérer les pools de crédits** : `POST /api/admin/wallet-pools`

---

## 6. Responsable Pédagogique

**Rôle :** `pedagogical_lead`
**Portée :** École (school_id)
**Layout:** `SchoolAdminLayout.tsx`

Le pedagogical_lead a accès aux mêmes pages que admin_school SAUF **Finance** et **Settings**. Il a une section supplémentaire : **Pédagogie**.

### 6.1 Pédagogie (`/dashboard/school/pedagogical`)

**Page:** `PedagogicalLeadPage.tsx`
**Endpoints:**
- `GET /pedagogical-lead/pending-courses` — Cours en attente
- `POST /pedagogical-lead/courses/{id}/approve` — Approuver
- `POST /pedagogical-lead/courses/{id}/reject` — Rejeter
- `POST /pedagogical-lead/courses/{id}/escalate` — Escalader à la plateforme
- `POST /pedagogical-lead/courses/{id}/reassign` — Réassigner
- `POST /pedagogical-lead/courses/{id}/postpone` — Reporter

Fonctionnalités :
- **Stats pédagogiques** : Total enseignants, cours actifs, taux de complétion
- **Filtre** par statut pédagogique
- **Actions** : Approuver, Demander révision, Escalader, Réassigner, Reporter

### 6.2 Gestion des Objectifs (`/pedagogical-lead/goals`)

**Endpoints:**
- `GET /pedagogical-lead/goals` — Objectifs (5 horizons)
- `POST /pedagogical-lead/goals/assign` — Assigner objectifs annuels
- `GET /pedagogical-lead/goals/statistics` — Statistiques

### 6.3 Suivi Adaptatif

**Endpoints:**
- `GET /pedagogical/adaptive-pathway/students/{id}/profile` — Profil d'assimilation
- `GET /pedagogical/adaptive-pathway/students/{id}/pathway` — Parcours chapitre
- `POST /pedagogical/adaptive-pathway/students/{id}/reorient` — Déclencher réorientation
- `GET /pedagogical/adaptive-pathway/students/{id}/notions` — Notions par chapitre

### 6.4 Performance

**Endpoint:** `GET /pedagogical-lead/performance`

- Analytics de performance de l'école

---

## 7. Enseignant

**Rôle :** `teacher`
**Portée :** École (school_id)
**Layout:** `DashboardLayout.tsx` (sidebar enseignant)

### 7.1 Tableau de bord (`/dashboard`)

**Page:** `TeacherDashboard.tsx`

- **Cartes de stats** : Mes Cours (0), Étudiants (0), DT Revenus (0)
- **Accès rapides** : Mes Cours, Devoirs, IA Studio, Revenus

### 7.2 Mon Apprentissage (`/dashboard/teacher/learning`)

**Page:** `MyLearning.tsx`
**Endpoints:**
- `GET /courses` — Catalogue
- `POST /courses/{id}/enroll` — S'inscrire

- Catalogue personnel de formation continue
- Parcourir les cours disponibles, s'inscrire pour s'améliorer
- Cours inscrits avec progression
- Recherche et filtre par catégorie

### 7.3 Gestion de Classe (`/dashboard/teacher/classroom`)

**Page:** `ClassroomManager.tsx`
**Endpoints:**
- `GET /api/teacher/classes` — Classes assignées
- `GET /api/teacher/classes/{id}/students` — Élèves d'une classe

- **Créer des classes** avec nom, code, niveau
- **Ajouter/Retirer** des élèves
- **Assigner des cours** aux classes
- **Créer des devoirs** avec date limite
- **Voir les détails** : liste élèves, cours assignés

### 7.4 Tuteur IA (`/dashboard/ai-tutor`)

**Page:** `LearnerAIChatPage.tsx`
**Endpoints:**
- `POST /ai/ask` — Poser une question
- `POST /ai/explain` — Demander une explication
- `POST /ai/correct` — Demander correction
- `POST /ai/quiz` — Générer un quiz
- `GET /ai/conversations` — Historique

- Chat avec l'assistant IA
- Historique des conversations sidebar
- Citations sources
- Export PDF/DOCX des conversations
- Support RTL pour l'arabe

### 7.5 AI Studio (`/dashboard/teacher/ai-studio`)

**Page:** `TeacherAIStudio.tsx`

- **Génération de contenu IA** pour les enseignants
- Types : Devoir, Leçon, Plan de leçon, Plan annuel, Quiz, Résumé
- Sélection : Matière (10 matières), Niveau (Primaire/Collège/Lycée/Université), Trimestre
- Génération avec streaming
- Export PDF/DOCX
- Historique des générations et solde tokens

### 7.6 Portefeuille (`/dashboard/teacher/wallet`)

**Page:** `TeacherWallet.tsx`
**Endpoint:** `GET /wallet/balance`

- Affichage du solde total
- Soldes par pool (avec dates d'expiration)
- Historique des transactions

### 7.7 Revenus (`/dashboard/teacher/sales`)

**Page:** `TeacherSalesPage.tsx`
**Endpoint:** `GET /subscriptions/status`

- Ventes totales, Revenu total
- Détail par vente : cours, montant, commission plateforme, revenu enseignant, date
- **Visible uniquement** pour les enseignants indépendants (sans école)

### 7.8 Réorientations (`/dashboard/teacher/reorientations`)

**Page:** `TeacherReorientationPage.tsx`

- Notifications de réorientation automatique des élèves
- Infos : nom élève, niveau actuel, niveau proposé, date limite
- Actions : Confirmer ou Annuler

### 7.9 Validation de Contenu (`/dashboard/teacher/validation-contenu`)

**Page:** `TeacherValidationContenuPage.tsx`
**Endpoints:**
- `GET /pedagogical/adaptive-pathway/contenus/pour-responsable`

- File de validation du contenu pédagogique
- Filtre par statut (en_attente/valide/rejete)
- Actions : Valider ou Rejeter avec commentaire

### 7.10 Profil (`/dashboard/profile`)

**Page:** `ProfilePage.tsx`
**Endpoint:** `PUT /users/{id}`

- Modifier : Nom complet, Langue (FR/EN/AR), Niveau scolaire

---

## 8. Élève

**Rôle :** `student`
**Portée :** École (school_id)
**Layout:** `DashboardLayout.tsx` (sidebar élève)

### 8.1 Mon Apprentissage (`/dashboard`)

**Page:** `StudentDashboard.tsx`

- **Badge de palier** : Découverte / Excellence / Établissement
- **Carte objectif du jour** (adaptatif) : Continuer leçon, Commencer cours, Exercice adaptatif, Révision, Leçon du cursus, Pas d'objectif
- **Stats d'inscription** et **actions rapides**

### 8.2 Catalogue de Cours (`/dashboard/courses`)

**Page:** `CatalogPage.tsx`
**Endpoints:**
- `GET /courses` — Catalogue
- `GET /courses/published` — Cours publiés
- `POST /courses/{id}/enroll` — S'inscrire

- Parcourir les cours par recherche, catégorie, niveau
- S'inscrire aux cours gratuits
- Cartes avec titre, enseignant, durée, niveau, nombre d'inscrits

### 8.3 Catalogue Cours Acquérir (`/dashboard/assignments`)

**Page:** `CourseCatalog.tsx`
**Endpoint:** `GET /lms/courses`

- Parcours des cours académiques disponibles à l'achat
- Prix (DT ou tokens)
- Flux d'achat avec option de remboursement
- Cours déjà inscrits

### 8.4 Lecteur de Cours (`/dashboard/courses/:courseId`)

**Page:** `CoursePlayerPage.tsx`
**Endpoints:**
- `GET /courses/{id}` — Détail cours
- `POST /learner/lessons/{id}/progress` — Marquer complété

- **Sidebar** avec navigation chapters/leçons
- **Types de contenu** : Texte, Vidéo (YouTube), PDF, Image, Lien, Quiz
- **Suivi de progression** (marquer leçons complétées)
- **Favoris** et **Notes**
- Navigation suivant/précédent

### 8.5 Tuteur IA (`/dashboard/ai-tutor`)

**Page:** `LearnerAIChatPage.tsx`

- Mêmes fonctionnalités que l'enseignant
- Chat IA contextuel avec l'historique des cours
- Export des conversations

### 8.6 Portefeuille (`/dashboard/wallet`)

**Page:** `StudentWallet.tsx`
**Endpoint:** `GET /wallet/balance`

- Solde total
- Soldes par pool avec expiration
- Historique des transactions

### 8.7 Packs de Cursus (`/dashboard/packs`)

**Page:** `PacksPage.tsx`
**Endpoints:**
- `GET /packs` — Liste packs
- `POST /packs/{id}/purchase` — Acheter

- Parcourir les packs par niveau scolaire
- Détails : nom, description, matières, prix, validité
- Acheter des packs
- Indicateur si déjà inclus par l'école

### 8.8 Mon Niveau (`/dashboard/tier`)

**Page:** `StudentTierPage.tsx`

- Explication du système de paliers
- **3 paliers** :
  - **Découverte** : IA basique, parcours guidé, cours gratuits/payants
  - **Excellence** : Exercices IA, test de positionnement adaptatif, recommandations personnalisées
  - **Établissement** : Contenu aligné au programme scolaire national
- Parcours recommandé et objectifs quotidiens

### 8.9 Test de Positionnement (`/dashboard/placement/:testId`)

**Page:** `PlacementTestPage.tsx`
**Endpoints:**
- `GET /placement/tests` — Tests disponibles
- `POST /placement/tests/{id}/submit` — Soumettre

- Interface de quiz question par question
- Affiche la question + choix multiples
- Avance automatiquement après réponse
- Résultats avec niveau recommandé
- **Auto-enroll** dans le parcours adapté

### 8.10 Profil d'Assimilation (`/dashboard/assimilation`)

**Page:** `StudentAssimilationProfilePage.tsx`
**Endpoint:** `GET /pedagogical/adaptive-pathway/students/{id}/profile`

- Niveau de maîtrise par chapitre
- **3 couleurs** : Rouge (remédiation), Bleu (standard), Vert (avancé)
- Filtre par matière
- Icône de cerveau pour visualiser la maîtrise

### 8.11 Catalogue Parcours (`/dashboard/parcours-catalog`)

**Page:** `PathwayCatalogPage.tsx`
**Endpoints:**
- `GET /pedagogical/adaptive-pathway/catalog` — Catalogue
- `POST /pedagogical/adaptive-pathway/enroll-pathway` — S'inscrire

- Parcourir les parcours disponibles par niveau
- Matières incluses, chapitres, tarification
- Achat et auto-inscription au parcours

### 8.12 Mon Parcours (`/dashboard/mon-parcours`)

**Page:** `MonParcoursPage.tsx`
**Endpoint:** `GET /pedagogical/adaptive-pathway/mon-parcours`

- **Arbre extensible** : Niveaux → Matières → Chapitres → Notions
- Statut par élément : à_commencer / en_cours / terminé / annulé
- **Color coding** par niveau : découverte / standard / avancé

### 8.13 Récompenses (`/dashboard/gamification`)

**Page:** `GamificationPage.tsx`
**Endpoints:**
- `GET /badges` — Tous les badges
- `GET /badges/my-badges` — Badges gagnés
- `GET /badges/check` — Vérifier éligibilité
- `GET /badges/streaks` — Série quotidienne
- `GET /badges/rankings` — Classement

**3 onglets :**
1. **Badges** : Gagnés/Disponibles par catégorie (progression/quiz/streak/spécial)
2. **Série** : Série actuelle, historique activité quotidienne (connexion/quiz/objectif), points
3. **Classement** : Leaderboard avec top élèves et rang personnel

### 8.14 Boîte de réception (`/dashboard/inbox`)

**Page:** `InboxPage.tsx`
**Endpoint:** `GET /inbox`

- Messages de diffusion et directs
- Filtre : Tous/Non lus
- Clic pour lire, marquer comme lu

### 8.15 Profil (`/dashboard/profile`)

**Page:** `ProfilePage.tsx`
**Endpoint:** `PUT /users/{id}`

- Modifier : Nom complet, Langue (FR/EN/AR), Niveau scolaire

---

## 9. Parent

**Rôle :** `parent`
**Portée :** École (school_id)
**Backend endpoints:**
- `GET /parents/children` — Liste des enfants liés
- `GET /parents/children/{id}/progress` — Suivi d'un enfant (lecture seule)

### 9.1 Fonctionnalités

- **Liste des enfants** : Voir tous les enfants rattachés au compte parent
- **Suivi détaillé** par enfant :
  - Solde DT
  - Niveau scolaire
  - Packs actifs
  - Informations de progression (lecture seule)

### 9.2 Sécurité RBAC

- Un parent ne peut voir **que ses propres enfants** (vérification via la table `ParentEnfant`)
- Si le parent n'est pas lié à un enfant → **403 Forbidden**
- Les endpoints sont protégés par `require_parent()`

### 9.3 Pas encore de section frontend dédiée

- Les endpoints parent existent dans le backend
- **Pas de page React dédiée** dans le frontend actuel
- Le parent peut utiliser les API directement

---

## 10. Fonctionnalités Transversales

### 10.1 Tuteur IA

**Endpoints :**
- `POST /ai/ask` — Tutorat
- `POST /ai/correct` — Correction
- `POST /ai/explain` — Explication
- `POST /ai/quiz` — Génération quiz
- `POST /ai/stream` — Streaming

- **6 modes** : Tutor, Correcteur, Expliqueur, Quiz, Image, Streaming
- **RAG** : Ingestion PDF, recherche par similarité FAISS
- **Rate limiting** : 30 req/min (tutorat), 20 req/min (explication), 10 req/min (quiz)
- **Fournisseurs** : Groq (défaut), OpenAI, Anthropic, etc.
- **Export** : PDF/DOCX avec support RTL (Arabe/Français)

### 10.2 Système de Paliers (Tiers)

| Palier | Accès IA | Parcours | Contenu |
|--------|---------|---------|---------|
| **Découverte** | Basique | Guidé | Cours gratuits/payants |
| **Excellence** | Exercices adaptatifs | Test positionnement | Recommandations |
| **Établissement** | Full | Cursus national | Programme scolaire |

- **Détection dynamique** : `get_student_tier(user, db)` calcule à la volée
- Basé sur les StudyPack et PackPurchase de l'élève

### 10.3 Gamification

**Tables :** `BadgeDefinition`, `StudentBadge`, `StudentStreak`, `StudentRanking`

- **10 badges** pré-configurés (progression, quiz, streak, spécial)
- **Série quotidienne** : Login, quiz, objectif quotidien
- **Classement** : Leaderboard par école
- **Attribution automatique** : `check_and_award_badges()` vérifie les critères

### 10.4 Portefeuille (Wallet)

**Tables :** `WalletTransaction` (append-only)

- **Système de ledger** : Toutes les transactions sont traçables
- **Pools** : Token, DT, DT_PURCHASED
- **Flux** : Crédit admin, Débit admin, Achat pack, Achat cours
- **Credit/Debit** : `credit_balance()`, `debit_balance()`, `get_dt_balance()`, `debit_dt()`, `credit_dt()`
- **Append-only** : Aucune modification directe du solde, tout passe par WalletTransaction

### 10.5 Objectifs Pédagogiques

**Endpoints :**
- `GET /learner/goals` — Objectifs élève
- `POST /learner/goals/{id}/check-in` — Check-in quotidien
- `POST /pedagogical-lead/goals/assign` — Assigner (admin)
- `GET /pedagogical-lead/goals/statistics` — Stats

- **5 horizons** : Jour, Semaine, Mois, Trimestre, Année
- **Statut TOUJOURS recalculé** dynamiquement (jamais stocké)
- **Pack Découverte** : Pas d'objectif personnalisé généré automatiquement
- **Calendrier tunisien** : 3 trimestres (T1: 15/9-19/12, T2: 5/1-27/3, T3: 6/4-19/6)
- **Scheduler** : APScheduler daily cron 00:05

### 10.6 Parcours Pédagogique Adaptatif

**Tables :** `NiveauEtude`, `Matiere`, `ChapterPathway`, `Notion`, `ContenuNotion`, `ProfilAssimilationEleve`, `HistoriqueScoreEleve`, `NotificationReorientation`, `SpecialitePedagogique`, `ResponsablePedagogique`

**5 couches :**
1. **Arborescence** : Niveaux → Matières → Chapitres → Notions
2. **Profil d'assimilation** : Granularité par chapitre, repli sur niveau matière
3. **Machine à réorientation** : Auto-immédiate + validation enseignant (silence = acceptation)
4. **Publication** : `publiable` si Standard existe ET (Remédiation OU Avancé)
5. **Accès dynamique** : `scope_achat` = traçabilité, accès réel via `niveau_effectif()`

### 10.7 Système de Paiement

- **Stripe** : Subscriptions mensuelles pour enseignants/écoles
- **Portefeuille interne** : DT (Dirham Tunisien) pour achats in-app
- **Pack de tokens** : Achat via DT
- **Remboursement** : Supporté pour les achats cours

---

## 11. Système de Données

### 11.1 Modèles Principaux (35 total)

| Catégorie | Modèles |
|-----------|---------|
| **Utilisateurs** | User, School, ClassRoom, TeacherClass |
| **Cours** | Course, Module, Lesson, Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer |
| **LMS** | CourseContent, Chapter, LessonContent, ContentQuiz, Enrollment (LMS), Certificate, CertificateTemplate |
| **Finance** | Transaction, WalletPool, WalletTransaction, PackPurchase, TokenPackage, Subscription, Plan |
| **Pédagogique** | NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion, ProfilAssimilationEleve, HistoriqueScoreEleve, NotificationReorientation, SpecialitePedagogique, SpecialitePedagogiqueMatiere, ResponsablePedagogique |
| **Gamification** | BadgeDefinition, StudentBadge, StudentStreak, StudentRanking |
| **Communication** | Message, AIConversation, AIChatMessage |
| **Inscription** | Enrollment, StudentEnrollment, Assignment, Submission, LessonProgress |
| **Infrastructure** | AuditLog, PlatformSetting, MediaAsset |

### 11.2 Enums Principaux

| Enum | Valeurs |
|------|---------|
| `UserRole` | student, teacher, admin_school, super_admin, pedagogical_admin, pedagogical_lead, parent |
| `CourseStatus` | draft, review, published, archived, rejected |
| `StatutValidationPedagogique` | EN_ATTENTE, VALIDE, REJETE |
| `NiveauAssimilation` | remediation, standard, avance |
| `ActionReorientation` | maintain, accelerate, decelerate, remedial |

### 11.3 Niveaux d'Étude (19 niveaux tunisiens)

| Cycle | Niveaux | Matières |
|-------|---------|----------|
| 2ème Cycle (Base) | 7ème, 8ème, 9ème année | 13 × 3 |
| 1ère année secondaire | Général | 15 |
| 2ème année | Lettres, Sciences, Techno, Éco | 9+16+10+9 |
| 3ème année | Lettres, Maths, Sciences Exp, Éco, Info, Tech | 8+10+10+8+8+9 |
| 4ème année (Bac) | Lettres, Maths, Sciences Exp, Éco, Info | 7+11+8+8+7 |

---

## Notes Importantes

1. **Tous les mots de passe de test** : `password123`
2. **Base PostgreSQL** : `DATABASE_URL=postgresql+pg8000://postgres:gill4264@localhost:5432/eduai`
3. **141 tests** passent (tous modules)
4. **Aucun hash bcrypt hardcodé** dans le code source
5. **Multi-tenancy** : Filtre automatique au niveau base de données
6. **Append-only wallet** : Toutes les transactions financières sont traçables

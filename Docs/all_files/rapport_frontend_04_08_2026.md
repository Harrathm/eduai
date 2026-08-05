# RAPPORT D'AUDIT FRONTEND — EDUAI Learning

**Date** : 04 août 2026  
**Périmètre** : React Web (`D:\RAG_APP_new\frontend`) + Flutter Mobile (`D:\RAG_APP_new\mobile`)  
**Méthode** : Analyse en lecture seule, preuves fichier+ligne pour chaque constat

---

## Sommaire

1. [Résumé exécutif](#résumé-exécutif)
2. [Étape 1 — Cartographie structurelle](#étape-1--cartographie-structurelle)
3. [Étape 2 — Inventaire par rôle et par module](#étape-2--inventaire-par-rôle-et-par-module)
4. [Étape 3 — Cohérence frontend/backend](#étape-3--cohérence-frontendbackend)
5. [Étape 4 — Sécurité frontend](#étape-4--sécurité-frontend)
6. [Étape 5 — Qualité UX et accessibilité](#étape-5--qualité-ux-et-accessibilité)
7. [Étape 6 — Qualité de code et dette technique](#étape-6--qualité-de-code-et-dette-technique)
8. [Étape 7 — Synthèse et prioritisation](#étape-7--synthèse-et-priorisation)

---

## Résumé exécutif

**Points critiques identifiés :**

1. **Token JWT stocké en localStorage** (React) — risque XSS. Le token est accessible via `localStorage.getItem("token")` dans 20+ fichiers. Le guard `RequireAuth` ne vérifie que l'existence de la chaîne, pas sa validité (`App.tsx:100-104`).
2. **Route guards bypassables** — `RequireRole` (`App.tsx:106-119`) lit le rôle depuis `localStorage` (contrôle client). Un attaquant peut modifier `user.role` dans DevTools pour accéder à n'importe quel dashboard admin.
3. **Flutter : démo credentials en dur** — `student@demo-academy.edu` / `password123` codés en dur dans `app_constants.dart:6-7` et affichés dans `login_screen.dart:179-180`.
4. **Flutter : HTTP non sécurisé** — `api_service.dart:5` utilise `http://10.0.2.2:8000` (pas de TLS).
5. **i18n quasi-inexistante** — Seulement 4 fichiers sur 100+ utilisent `useTranslation`. Tout le UI est en dur en français malgré l'infrastructure i18next.
6. **RTL structurellement cassé** — 160+ classes Tailwind directionnelles (`ml-`, `pr-`, `text-left`) rendent l'arabe illisible. La police Tajawal est importée mais jamais appliquée.
7. **Couverture de tests : 5.5%** — 3 fichiers de test pour ~55 composants page côté React. Aucun test côté Flutter.
8. **TeacherAbonnementsPage cassé** — Variable `API` non déclarée (`TeacherAbonnementsPage.tsx:69`) — toutes les requêtes échouent avec URL `undefined/api/abonnements/...`.
9. **Soft Skills : route sans garde de rôle** — `SoftSkillsCatalogPage` accessible par tout utilisateur authentifié (`App.tsx:243`).
10. **Pas de refresh token** — Aucun mécanisme de renouvellement JWT. Les sessions expirent silencieusement.

---

## Étape 1 — Cartographie structurelle

### 1.1 React Web (`D:\RAG_APP_new\frontend`)

#### Arborescence

```
frontend/
├── src/
│   ├── App.tsx                    # Point d'entrée routing (273 lignes)
│   ├── index.css                  # CSS global + Tailwind
│   ├── index.jsx                  # ReactDOM.createRoot
│   ├── api/                       # Modules API domaine (7 fichiers)
│   │   ├── catalog.ts
│   │   ├── courses.ts
│   │   ├── adminCourses.ts
│   │   ├── conversations.ts
│   │   ├── lms.ts
│   │   ├── tier.ts
│   │   └── wallet.ts
│   ├── components/                # Composants partagés (9 fichiers)
│   │   ├── ErrorBoundary.tsx
│   │   ├── LanguageSelector.tsx
│   │   ├── Skeleton.tsx
│   │   ├── TeacherStateGuard.tsx
│   │   ├── TierBadge.tsx
│   │   ├── WalletWidget.tsx
│   │   ├── DailyObjective.tsx
│   │   └── layout/DashboardLayout.tsx
│   ├── features/                  # Features par rôle (85 fichiers)
│   │   ├── admin/     (48 fichiers : pages, composants, api)
│   │   ├── auth/      (4 fichiers : login, register, forgot, reset)
│   │   ├── learner/   (1 fichier : PlayerPage)
│   │   ├── parent/    (7 fichiers : dashboard, famille, wallet, pack)
│   │   ├── pathway/   (1 fichier : api/index.ts)
│   │   ├── student/   (14 fichiers : dashboard, wallet, packs, etc.)
│   │   └── teacher/   (14 fichiers : dashboard, parcours, elements, etc.)
│   ├── hooks/                     # Hooks personnalisés (useAIStream, etc.)
│   ├── i18n/                      # i18next + 3 locales (fr, en, ar)
│   ├── pages/                     # Pages hors features (7 fichiers)
│   │   ├── admin/AdminMediaLibraryPage.tsx
│   │   └── learner/ (6 fichiers : catalog, player, AI chat, soft skills)
│   ├── store/                     # Zustand stores (authStore, conversationStore)
│   ├── test/                      # Tests (3 fichiers)
│   └── utils/                     # ApiClient + utilitaires
├── package.json
├── vite.config.js
├── tailwind.config.js
└── .env.local / .env.example / .env.production
```

#### Dépendances (package.json)

| Catégorie | Package | Version |
|-----------|---------|---------|
| **Framework** | react | ^18.2.0 |
| **Routing** | react-router-dom | ^6.22.0 |
| **State** | zustand | ^4.5.0 |
| **HTTP** | axios | ^1.6.0 (❌ jamais importé) |
| **i18n** | i18next | ^26.3.6 |
| **CSS** | tailwindcss | ^3.4.1 |
| **UI** | lucide-react | ^1.11.0 |
| **Charts** | recharts | ^3.8.1 |
| **Sécurité** | dompurify | ^3.4.11 |
| **PDF** | jspdf | ^4.2.1 |
| **Test** | vitest | ^4.1.6 |

**Observations** :
- `axios` listé en dépendance mais **jamais importé** — poids mort (`package.json:18`)
- Le projet utilise nativement `fetch()` partout

#### State Management

**Zustand** v4.5.0 — 2 stores :
- `authStore.ts` : user, token, login/logout/register/restore
- `conversationStore.ts` : conversations, messages, CRUD

#### Routing

**React Router DOM** v6.22.0 — Route tree entier dans `App.tsx` (273 lignes).  
Lazy loading via `React.lazy()` pour toutes les pages (code splitting).

#### Design System

- **CSS** : Tailwind CSS v3.4.1
- **Palette** : `navy #0D1B2A`, `orange #FF6B2B`, `cream #FFF8F0` (définis dans `tailwind.config.js:5-26`)
- **Fonts** : Cormorant Garamond (display), DM Sans (body), Tajawal (arabe — importé mais jamais utilisé)

---

### 1.2 Flutter Mobile (`D:\RAG_APP_new\mobile`)

#### Arborescence

```
mobile/
├── lib/
│   ├── main.dart                    # Point d'entrée (37 lignes)
│   ├── core/
│   │   ├── router.dart              # GoRouter (27 lignes, 3 routes)
│   │   ├── api/api_service.dart     # Client HTTP (125 lignes, 7 endpoints)
│   │   ├── constants/app_constants.dart  # Constantes + credentials démo
│   │   └── storage/secure_storage.dart   # FlutterSecureStorage wrapper
│   └── features/
│       ├── splash/splash_screen.dart
│       ├── auth/
│       │   ├── bloc/auth_bloc.dart
│       │   └── pages/login_screen.dart
│       ├── home/pages/home_screen.dart
│       ├── courses/
│       │   ├── bloc/ (3 fichiers — non utilisés)
│       │   └── pages/courses_screen.dart
│       ├── assignments/pages/assignments_screen.dart
│       └── ai_tutor/pages/ai_tutor_screen.dart
├── pubspec.yaml
└── assets/images/ (vide)
```

**Total** : 15 fichiers Dart

#### Dépendances (pubspec.yaml)

| Package | Version | Utilisé ? |
|---------|---------|-----------|
| flutter_bloc | ^8.1.3 | Oui (AuthBloc) |
| go_router | ^13.0.0 | Oui (3 routes) |
| http | ^1.1.0 | Oui |
| flutter_secure_storage | ^9.0.0 | Oui |
| shared_preferences | ^2.2.2 | ❌ jamais importé |
| equatable | ^2.0.5 | Oui (BLoC) |
| cached_network_image | ^3.3.0 | ❌ jamais importé |
| shimmer | ^3.0.0 | ❌ jamais importé |

#### State Management

**BLoC** (flutter_bloc ^8.1.3) — mais **incomplet** :
- `AuthBloc` : fonctionnel (login, logout, check)
- `CoursesBloc` : défini mais **jamais injecté** dans l'arbre de widgets (`courses_bloc.dart:9`)
- Les écrans utilisent `setState()` directement au lieu du BLoC

#### Routing

**GoRouter** v13.0.0 — seulement 3 routes définies (`router.dart:11-25`) :
- `/` → SplashScreen
- `/login` → LoginScreen
- `/home` → HomeScreen

**Conflit** : `login_screen.dart:44` utilise `Navigator.pushReplacementNamed` (impératif) au lieu de `context.go()` (déclaratif GoRouter). La navigation interne des tabs utilise aussi `Navigator.push`.

---

### 1.3 Dépendances obsolètes / vulnérabilités

| Frontend | Package | Risque |
|----------|---------|--------|
| React | axios ^1.6.0 | Listé mais jamais utilisé (poids mort) |
| React | typescript ^6.0.3 | ❌ non vérifié si compatible avec toutes les dépendances |
| Flutter | shared_preferences ^2.2.2 | Déclaré mais jamais importé |
| Flutter | cached_network_image ^3.3.0 | Déclaré mais jamais importé |
| Flutter | shimmer ^3.0.0 | Déclaré mais jamais importé |

**Note** : L'audit de vulnérabilités npm/gradle n'est pas disponible dans cet environnement (`npm audit` non exécuté).

---

### 1.4 Configuration / Variables d'environnement

#### React Web

| Fichier | Variables | Observation |
|---------|-----------|-------------|
| `.env.local` | `VITE_API_URL=http://localhost:8000` | Utilisé par le dev server |
| `.env.example` | `VITE_API_BASE_URL`, `VITE_STRIPE_PUBLISHABLE_KEY`, `VITE_APP_NAME` | **Incohérent** : `.env.local` utilise `VITE_API_URL`, `.env.example` utilise `VITE_API_BASE_URL` |
| `.env.production` | `VITE_API_URL=https://eduai-backend.onrender.com` | URL production |

**Problème critique** : `API_URL` est codé en dur en chaîne vide `""` dans `authStore.ts:9` et `apiClient.ts:14`. Les variables `VITE_API_URL` ne sont **jamais lues** via `import.meta.env`. Le proxy Vite (`vite.config.js:12-28`) compense en dev, mais en production le frontend appelle des URLs relatives vides.

#### Flutter Mobile

| Variable | Valeur | Fichier |
|----------|--------|---------|
| `baseUrl` | `http://10.0.2.2:8000` | `api_service.dart:5` |
| `apiBaseUrl` | `http://10.0.2.2:8000` | `app_constants.dart:3` (❌ jamais utilisé) |

**Pas de gestion multi-environnement** — l'URL est codée en dur. Pas de `--dart-define` ni de flavour.

---

### 1.5 Point d'entrée et guards de rôle

#### React Web

**Entrée** : `src/index.jsx` → `App.tsx`

**Guards** (`App.tsx:100-119`) :

| Guard | Fichier:Ligne | Ce qu'il vérifie | Bypassable ? |
|-------|---------------|------------------|--------------|
| `RequireAuth` | `App.tsx:100-104` | Existence de `token` dans Zustand store (= `localStorage`) | **OUI** — ne valide pas la signature ni l'expiration |
| `RequireRole` | `App.tsx:106-119` | `user.role` dans Zustand store (= `localStorage`) contre liste autorisée | **OUI** — le rôle est contrôle client |
| `TeacherWriteGuard` | `TeacherStateGuard.tsx:58-81` | État A/B/C du teacher via `is_approved` + `subscription_plan` | **OUI** — utilise `pointer-events-none` (visuel uniquement) |

#### Flutter Mobile

**Entrée** : `main.dart` → `runApp(EDUAIMobileApp())`

**Guards** : **Aucun**. Le `GoRouter` dans `router.dart` n'a pas de callback `redirect`. N'importe qui peut naviguer vers `/home` sans authentification. Le `SplashScreen` redirige toujours vers `/login` après 2 secondes, ignorer l'état d'auth.

---

## Étape 2 — Inventaire par rôle et par module

### 2.1 React Web — Pages par rôle

#### SUPER_ADMIN + PEDAGOGICAL_ADMIN (`/dashboard/admin`)

| Route | Composant | Fichier | Endpoints API | État |
|-------|-----------|---------|---------------|------|
| `/dashboard/admin` | AdminDashboardPage | `features/admin/pages/AdminDashboardPage.tsx` | `GET /api/admin/dashboard` | Complet |
| `/dashboard/admin/users` | AdminUsersPage | `features/admin/pages/AdminUsersPage.tsx` | `GET /api/admin/users` | Complet |
| `/dashboard/admin/schools` | AdminSchoolsPage | `features/admin/pages/AdminSchoolsPage.tsx` | `GET /api/admin/schools` | Complet |
| `/dashboard/admin/courses` | AdminCoursesPage | `features/admin/pages/AdminCoursesPage.tsx` | `GET /api/admin/courses` | Complet |
| `/dashboard/admin/courses/:id` | CourseEditorPage | `features/admin/pages/CourseEditorPage.tsx` | CRUD modules/leçons | Complet |
| `/dashboard/admin/analytics` | AdminAnalyticsPage | `features/admin/pages/AdminAnalyticsPage.tsx` | `GET /api/admin/analytics/*` | Complet |
| `/dashboard/admin/teachers` | AdminTeacherQueuePage | `features/admin/pages/AdminTeacherQueuePage.tsx` | `GET /api/admin/teacher-registrations` | Complet |
| `/dashboard/admin/finance` | FinanceCenter | `features/admin/pages/FinanceCenter.tsx` | `GET /api/admin/wallets` | Complet |
| `/dashboard/admin/media` | AdminMediaLibraryPage | `pages/admin/AdminMediaLibraryPage.tsx` | Upload media | Complet |
| `/dashboard/admin/inbox` | AdminInboxView | `features/admin/pages/AdminInboxView.tsx` | `GET /api/admin/messages` | Complet |
| `/dashboard/admin/ai-factory` | ContentCreatorAI | `features/admin/pages/ContentCreatorAI.tsx` | `POST /api/admin/ai-factory/*` | Complet |
| `/dashboard/admin/broadcast` | BroadcastCenter | `features/admin/pages/BroadcastCenter.tsx` | `POST /api/admin/broadcast` | Complet |
| `/dashboard/admin/settings` | AdminSettingsPage | `features/admin/pages/AdminSettingsPage.tsx` | `GET/PUT /api/admin/settings` | Complet |
| `/dashboard/admin/packages` | AdminTokenPackagesPage | `features/admin/pages/AdminTokenPackagesPage.tsx` | `GET /api/admin/token-packages` | Complet |
| `/dashboard/admin/invite-codes` | AdminInviteCodesPage | `features/admin/pages/AdminInviteCodesPage.tsx` | CRUD invite codes | Complet |
| `/dashboard/admin/audit` | AdminAuditLogPage | `features/admin/pages/AdminAuditLogPage.tsx` | `GET /api/admin/logs/errors` | Complet |
| `/dashboard/admin/pedagogical-review` | PedagogicalAdminPage | `features/admin/pages/PedagogicalAdminPage.tsx` | Pathway admin | Complet |
| `/dashboard/admin/arborescence` | AdminArborescencePage | `features/admin/pages/AdminArborescencePage.tsx` | Pathway structure | Complet |
| `/dashboard/admin/publication-status` | AdminPublicationStatusPage | `features/admin/pages/AdminPublicationStatusPage.tsx` | Publication workflow | Complet |
| `/dashboard/admin/seuils-config` | AdminSeuilsConfigPage | `features/admin/pages/AdminSeuilsConfigPage.tsx` | `PUT /api/pathway/matieres/:id` | Complet |
| `/dashboard/admin/specialites-pedagogiques` | AdminSpecialitesPedagogiquesPage | `features/admin/pages/AdminSpecialitesPedagogiquesPage.tsx` | `GET/POST /api/pathway/specialites-pedagogiques` | Complet |
| `/dashboard/admin/course-distribution` | SchoolCourseDistribution | `features/admin/pages/SchoolCourseDistribution.tsx` | Course distribution | Complet |
| `/dashboard/admin/teacher-catalog` | SuperAdminCourseFactory | `features/admin/pages/SuperAdminCourseFactory.tsx` | Teacher catalog | Complet |

**Total** : 23 pages admin — toutes complètes.

#### ADMIN_SCHOOL + PEDAGOGICAL_LEAD (`/dashboard/school`)

| Route | Composant | Fichier | Endpoints API | État |
|-------|-----------|---------|---------------|------|
| `/dashboard/school` | SchoolOverview | `features/admin/pages/SchoolOverview.tsx` | Dashboard école | Complet |
| `/dashboard/school/users` | UserManagementView | `features/admin/pages/UserManagementView.tsx` | `GET /api/admin/users` | Complet |
| `/dashboard/school/finance` | FinanceCenter | `features/admin/pages/FinanceCenter.tsx` | `GET /api/admin/wallets` | Complet |
| `/dashboard/school/courses` | AdminCoursesPage | `features/admin/pages/AdminCoursesPage.tsx` | `GET /api/admin/courses` | Complet |
| `/dashboard/school/teachers` | AdminTeacherQueuePage | `features/admin/pages/AdminTeacherQueuePage.tsx` | `GET /api/admin/teacher-registrations` | Complet |
| `/dashboard/school/settings` | AdminSettingsPage | `features/admin/pages/AdminSettingsPage.tsx` | `GET/PUT /api/admin/settings` | Complet |
| `/dashboard/school/pedagogical` | PedagogicalLeadPage | `features/admin/pages/PedagogicalLeadPage.tsx` | Pathway lead | Complet |

**Total** : 7 pages école — toutes complètes.

#### TEACHER (`/dashboard/teacher`)

| Route | Composant | Fichier | Endpoints API | État |
|-------|-----------|---------|---------------|------|
| `/dashboard` (index) | TeacherDashboard | `features/teacher/pages/TeacherDashboard.tsx` | `GET /api/courses/my-courses`, `/api/teacher/classes`, `/api/wallet/balance` | Complet |
| `/dashboard/teacher/learning` | MyLearning | `features/teacher/pages/MyLearning.tsx` | `GET /api/courses/my-courses`, `/catalog/courses` | Complet |
| `/dashboard/teacher/classroom` | ClassroomManager | `features/teacher/pages/ClassroomManager.tsx` | CRUD `/api/teacher/classes` | Complet |
| `/dashboard/teacher/ai-studio` | TeacherAIStudio | `features/teacher/pages/TeacherAIStudio.tsx` | `POST /api/conversations` | Complet (TeacherWriteGuard) |
| `/dashboard/teacher/wallet` | TeacherWallet | `features/teacher/pages/TeacherWallet.tsx` | `GET /api/wallet/balance`, `/wallet/history` | Complet |
| `/dashboard/teacher/sales` | TeacherSalesPage | `features/teacher/pages/TeacherSalesPage.tsx` | `GET /api/courses/my-sales` | Complet |
| `/dashboard/teacher/abonnements` | TeacherAbonnementsPage | `features/teacher/pages/TeacherAbonnementsPage.tsx` | `GET /api/abonnements/*` | **CASSÉ** — variable `API` non déclarée (ligne 69) |
| `/dashboard/teacher/reorientations` | TeacherReorientationPage | `features/teacher/pages/TeacherReorientationPage.tsx` | `GET /api/pathway/enseignants/:id/notifications-reorientation` | Complet (TeacherWriteGuard) |
| `/dashboard/teacher/validation-contenu` | TeacherValidationContenuPage | `features/teacher/pages/TeacherValidationContenuPage.tsx` | `GET /api/pathway/responsables-pedagogiques/:id/contenus` | Complet (TeacherWriteGuard) |
| `/dashboard/teacher/parcours` | TeacherParcoursPage | `features/teacher/pages/TeacherParcoursPage.tsx` | CRUD `/api/parcours` via moduleApi | Complet (TeacherWriteGuard) |
| `/dashboard/teacher/elements` | TeacherElementsPage | `features/teacher/pages/TeacherElementsPage.tsx` | CRUD `/api/elements` via moduleApi | Complet (TeacherWriteGuard) |
| `/dashboard/teacher/bibliotheque` | TeacherBibliothequePage | `features/teacher/pages/TeacherBibliothequePage.tsx` | `GET /api/bibliotheque/search` | Complet |

**Total** : 12 pages teacher — 1 cassée (TeacherAbonnementsPage).

#### STUDENT

| Route | Composant | Fichier | Endpoints API | État |
|-------|-----------|---------|---------------|------|
| `/dashboard` (index) | StudentDashboard | `features/student/pages/StudentDashboard.tsx` | `GET /api/learner/dashboard`, `/api/learner/daily-objective` | Complet |
| `/dashboard/my-pack` | StudentPackPage | `features/student/pages/StudentPackPage.tsx` | `GET /api/abonnements/mon-pack`, `POST change-tier`, `DELETE cancel-scheduled` | Complet |
| `/dashboard/wallet` | StudentWallet | `features/student/pages/StudentWallet.tsx` | `GET /api/wallet/balance`, `/wallet/history` | Complet |
| `/dashboard/packs` | PacksPage | `features/student/pages/PacksPage.tsx` | `GET /api/abonnements/packs?niveau_scolaire=` | Complet |
| `/dashboard/tier` | StudentTierPage | `features/student/pages/StudentTierPage.tsx` | `GET /api/learner/dashboard`, `/learner/recommended-path` | Complet |
| `/dashboard/courses` | CatalogPage | `pages/learner/CatalogPage.tsx` | `GET /catalog/courses`, `POST /api/learner/courses/:id/enroll` | Complet |
| `/dashboard/courses/:id` | CoursePlayerPage | `pages/learner/CoursePlayerPage.tsx` | `GET /api/learner/courses/:id/syllabus`, progress, notes, quiz | Complet (595 lignes — page la plus complexe) |
| `/dashboard/ai-tutor` | LearnerAIChatPage | `pages/learner/LearnerAIChatPage.tsx` | `POST /api/ai/ask` (SSE streaming) | Complet (619 lignes) |
| `/dashboard/profile` | ProfilePage | `features/student/pages/ProfilePage.tsx` | `PUT /auth/me/language`, `PUT /users/me` | Complet |
| `/dashboard/placement/:testId` | PlacementTestPage | `features/student/pages/PlacementTestPage.tsx` | `GET /api/placement/tests/:id`, `POST submit` | Complet |
| `/dashboard/inbox` | InboxPage | `features/student/pages/InboxPage.tsx` | `GET /api/inbox/messages` | Complet |
| `/dashboard/soft-skills` | SoftSkillsCatalogPage | `pages/learner/SoftSkillsCatalogPage.tsx` | `GET /catalog/courses?category=soft_skills` | **Placeholder** — pas de RequireRole, message "bientôt disponible" |
| `/dashboard/assimilation` | StudentAssimilationProfilePage | `features/student/pages/StudentAssimilationProfilePage.tsx` | `GET /api/pathway/eleves/:id/profil-assimilation` | Complet |
| `/dashboard/parcours-catalog` | PathwayCatalogPage | `features/student/pages/PathwayCatalogPage.tsx` | `GET /api/pathway/catalog`, `POST enroll-pathway` | Complet |
| `/dashboard/mon-parcours` | MonParcoursPage | `features/student/pages/MonParcoursPage.tsx` | `GET /api/pathway/mon-parcours` | Complet |
| `/dashboard/gamification` | GamificationPage | `features/student/pages/GamificationPage.tsx` | `GET /api/gamification/badges`, `/streak`, `/rankings` | Complet |
| `/dashboard/assignments` | StudentCourseCatalog | (implicit via StudentDashboard) | `GET /api/courses/marketplace` | Complet |
| `/onboarding` | OnboardingPage | `features/student/pages/OnboardingPage.tsx` | `PUT /auth/me/language`, `PUT /users/me`, `PUT /auth/me/onboarding-complete` | Complet |

**Total** : 18 pages student — 1 placeholder (Soft Skills).

#### PARENT (`/dashboard/parent`)

| Route | Composant | Fichier | Endpoints API | État |
|-------|-----------|---------|---------------|------|
| `/dashboard/parent` | ParentDashboardPage | `features/parent/pages/ParentDashboardPage.tsx` | `GET /api/parents/me/dashboard`, `POST /api/parents/me/enfants/lier` | Complet |
| `/dashboard/parent/enfant/:id` | ChildDetailPage | `features/parent/pages/ChildDetailPage.tsx` | `GET /api/parents/me/enfants/:id/suivi`, progression | Complet |
| `/dashboard/parent/enfant/:id/wallet` | ParentWalletPage | `features/parent/pages/ParentWalletPage.tsx` | `POST /api/konnect/parents/me/enfants/:id/credit-wallet` | Complet |
| `/dashboard/parent/enfant/:id/pack` | ParentPackPage | `features/parent/pages/ParentPackPage.tsx` | `GET /api/parents/me/enfants/:id/suivi`, `/api/abonnements/packs` | Complet |
| `/dashboard/parent/famille` | ParentFamillePage | `features/parent/pages/ParentFamillePage.tsx` | `GET /api/famille/compte`, CRUD enfants | Complet |
| `/dashboard/parent/messages` | ParentMessaging | `features/parent/pages/ParentMessaging.tsx` | `GET /api/parents/me/messages` | Complet |

**Total** : 6 pages parent — toutes complètes.

---

### 2.2 Flutter Mobile — Inventaire complet

| Écran | Fichier | Endpoints API | État |
|-------|---------|---------------|------|
| Splash | `splash_screen.dart` | Aucun | Complet (2s delay → /login) |
| Login | `login_screen.dart` | `POST /auth/login` | Complet (credentials démo affichées) |
| Home (dashboard) | `home_screen.dart` | **Aucun** — toutes les données sont **hardcodées** ("4 cours", "3 tâches", "12 complétés") | **Placeholder** |
| Cours (liste) | `courses_screen.dart` | `GET /api/academy/courses` | Partiel — pas de token dans ApiService |
| Détail cours/leçons | `courses_screen.dart` (LessonDetailScreen) | `GET /api/academy/courses/{id}/modules` | Partiel — pas de token |
| Devoirs (liste) | `assignments_screen.dart` | `GET /api/lms/assignments` | Partiel — pas de token |
| Soumission devoir | `assignments_screen.dart` (bottom sheet) | `POST /api/lms/assignments/{id}/submit` | Partiel — pas de token |
| Tuteur IA | `ai_tutor_screen.dart` | `POST /api/ai/ask` | Partiel — pas de token |

**Total** : 5 écrans fonctionnels (sur 8 déclarés), tous avec problème de token manquant.

---

### 2.3 Écarts de parité fonctionnelle React ↔ Flutter

| Fonctionnalité | React Web | Flutter Mobile | Écart |
|----------------|-----------|----------------|-------|
| Login | ✅ Complet | ✅ Complet (credentials démo) | Mineur |
| Register | ✅ Complet (3 types) | ❌ Absent | **Majeur** |
| Forgot/Reset Password | ✅ 2 pages | ❌ Absent | **Majeur** |
| Dashboard Admin | ✅ 23 pages | ❌ Absent | **Majeur** ( Flutter = student only) |
| Dashboard Teacher | ✅ 12 pages | ❌ Absent | **Majeur** |
| Dashboard Student | ✅ 18 pages | ⚠️ Placeholder (données hardcodées) | **Majeur** |
| Dashboard Parent | ✅ 6 pages | ❌ Absent | **Majeur** |
| Mon Pack (scoped) | ✅ Complet | ❌ Absent | **Majeur** |
| Wallet multi-pocket | ✅ Complet | ❌ Absent | **Majeur** |
| Catalogue Soft Skills | ⚠️ Placeholder | ❌ Absent | Mineur |
| Cours (catalogue + player) | ✅ Complet (595 lignes) | ⚠️ Basique (liste + modules) | **Majeur** |
| Devoirs | ✅ (via CoursePlayer) | ⚠️ Basique (liste + submit) | Moyen |
| Tutor IA | ✅ Complet (SSE streaming) | ⚠️ Basique (pas de streaming) | Moyen |
| Gamification | ✅ Complet | ❌ Absent | Moyen |
| i18n FR/AR | ⚠️ Infra présente, 4 fichiers utilisent | ❌ Absent | **Majeur** |
| RTL | ⚠️ Cassé mais tentative | ❌ Absent | **Majeur** |
| Tests | ⚠️ 3 fichiers (5.5%) | ❌ Aucun | **Majeur** |

---

### 2.4 Pages liées aux sujets audités backend

#### Mon Pack (scope niveau, upgrade immédiat, downgrade différé)

**React** — `StudentPackPage.tsx` (372 lignes) :
- Appelle `GET /api/abonnements/mon-pack` (ligne 74)
- Affiche le pack actuel, le tier, la date d'effet planifiée
- Bouton upgrade → `POST /api/abonnements/change-tier` (ligne 93)
- Bouton downgrade différé → notification avec date de prochain trimestre
- Annulation → `DELETE /api/abonnements/cancel-scheduled-change` (ligne 109)
- **État** : ✅ Complet, aligné avec le backend

**Flutter** — ❌ Absent

#### Wallet multi-pocket

**React** — `StudentWallet.tsx` (152 lignes) :
- Appelle `GET /api/wallet/balance` (ligne 42)
- Affiche les pools : trial, subscription, school_allocated, purchased, dt_purchased
- Affiche les dates d'expiration par pool
- Historique des transactions (ligne 43)
- **État** : ✅ Complet

**Flutter** — ❌ Absent

#### Dashboard teacher (états A/B/C)

**React** — `TeacherDashboard.tsx` + `TeacherStateGuard.tsx` :
- `TeacherStateBadge` affiche l'état (Validé/En attente/Essai) — `TeacherDashboard.tsx:119`
- `TeacherWriteGuard` restreint l'écriture pour les états B et C
- Routes protégées : ai-studio, reorientations, validation-contenu, parcours, elements
- **État** : ✅ Complet

**Flutter** — ❌ Absent

#### Catalogue Soft Skills

**React** — `SoftSkillsCatalogPage.tsx` (169 lignes) :
- Route `/dashboard/soft-skills` — **pas de RequireRole** (`App.tsx:243`)
- Appelle `GET /catalog/courses?category=soft_skills` (ligne 31)
- État vide : "Les formations Soft Skills seront bientôt disponibles" (ligne 133)
- **État** : ⚠️ Placeholder, pas de mécanisme d'inscription

**Flutter** — ❌ Absent

---

## Étape 3 — Cohérence frontend/backend

### 3.1 Endpoints orphelins (jamais appelés par les frontends)

L'audit backend a documenté 399 endpoints. Voici les principaux endpoints **jamais consommés** par React ou Flutter :

| Endpoint | Module | Observation |
|----------|--------|-------------|
| `POST /auth/refresh` | Auth | Pas de refresh token côté frontend |
| `GET /api/admin/ai-factory/templates` | AI Factory | Pas de page admin correspondante |
| `POST /api/admin/ai-factory/analyze-course` | AI Factory | Pas de page admin correspondante |
| `GET /api/gamification/achievements` | Gamification | Pas de page achievements (badges/streak/rankings sont appelés) |
| `GET /api/inbox/unread-count` | Inbox | Pas de badge compteur |
| `POST /api/learner/courses/{id}/unenroll` | Learner | Pas de désinscription |
| `GET /api/admin/schools/{id}/stats` | Admin | Pas de vue détaillée école |
| `GET /api/admin/teacher-classes/{classId}/analytics` | Admin | Pas d'analytics par classe |
| `POST /api/pathway/elements/{id}/promote-global` | Pathway | Pas d'interface pour promouvoir un élément |
| Tous les endpoints Konnect (`/api/konnect/checkout`) | Payments | ✅ Appelé par `ParentWalletPage.tsx` |

**Note** : La liste complète des 399 endpoints n'est pas vérifiable sans le rapport backend complet. Seuls les endpoints pertinents pour les fonctionnalités frontend ont été audités.

### 3.2 Frontend → Backend : routes cassées ou incohérentes

| Appel Frontend | Fichier:Ligne | Problème |
|----------------|---------------|----------|
| `${API}/api/abonnements/packs` | `TeacherAbonnementsPage.tsx:69` | Variable `API` non déclarée → URL = `undefined/api/abonnements/packs` |
| `GET /api/lms/assignments` | Flutter `api_service.dart:93` | ❌ non vérifié si cet endpoint existe côté backend |
| `GET /api/academy/courses` | Flutter `api_service.dart:88` | ❌ non vérifié si cet endpoint existe côté backend |
| `GET /api/academy/courses/{id}/modules` | Flutter `api_service.dart:111` | ❌ non vérifié si cet endpoint existe côté backend |
| `VITE_API_URL` | `.env.local` vs `authStore.ts:9` | Variable d'env non lue — `API_URL` codé en dur en `""` |

### 3.3 Gestion des erreurs HTTP

#### React Web

| Code | Gestion | Fichier | Évaluation |
|------|---------|---------|------------|
| **401** | Redirection `/login` + nettoyage localStorage | `apiClient.ts:104-108` | ✅ Géré globalement via ApiClient |
| **403** | Message d'erreur explicite | `TeacherValidationContenuPage.tsx:44`, `TeacherReorientationPage.tsx:31` | ⚠️ Partiel — seulement 2 pages |
| **404** | ❌ Non géré explicitement | — | Les pages affichent des données vides sans message |
| **500** | ❌ Non géré explicitement | — | ErrorBoundary capture les erreurs de rendu mais pas les erreurs réseau |
| **429** | ❌ Non géré | — | Rate limit non traité côté UI |

**Problème** : Beaucoup de composants utilisent `catch (err) { console.error(err) }` sans feedback utilisateur (`TeacherAIStudio.tsx:71`, `MyLearning.tsx:52`, `ClassroomManager.tsx:63`, `ParentWalletPage.tsx:73`, `EnrollmentManager.tsx:39`).

#### Flutter Mobile

| Code | Gestion | Fichier | Évaluation |
|------|---------|---------|------------|
| **401** | Exception `UnauthorizedException` | `api_service.dart:64` | ⚠️ Exception lancée mais pas toujours attrapée |
| **Autre** | Exception `ApiException` avec message | `api_service.dart:66` | ⚠️ `jsonDecode` sur body peut crasher si réponse non-JSON |
| **Réseau** | ❌ Non géré | — | Pas de gestion de timeout ni de network error |

### 3.4 Stockage du token d'authentification

#### React Web — **RISQUE XSS**

| Mécanisme | Fichier:Ligne | Risque |
|-----------|---------------|--------|
| `localStorage.setItem("token", ...)` | `authStore.ts:77,105,120` | **ÉLEVÉ** — XSS = vol de token |
| `localStorage.getItem("token")` | 20+ fichiers (apiClient.ts:26, admin/api/index.ts:4, etc.) | Lecture directe scattered |
| `localStorage.setItem("user", ...)` | `authStore.ts:79,97` | Rôle stocké en clair = escalation de privilèges |

**Contrairement aux bonnes pratiques** : Le token devrait être dans un cookie `httpOnly + secure` pour empêcher l'accès JavaScript. Le stockage localStorage est vulnérable aux attaques XSS.

#### Flutter Mobile — **Sécurisé**

| Mécanisme | Fichier:Ligne | Risque |
|-----------|---------------|--------|
| `FlutterSecureStorage` | `secure_storage.dart:4` | ✅ Keychain (iOS) / EncryptedSharedPreferences (Android) |
| `saveToken()` / `getToken()` | `secure_storage.dart:9-15` | ✅ Encrypted |
| `saveUser()` — **jamais appelé** | `secure_storage.dart:21` | ⚠️ User data non persisté |

**Bogue** : `secure_storage.saveUser()` est défini mais **jamais appelé** (`secure_storage.dart:21-23`). À chaque redémarrage, `getUser()` retourne `null`, et le BLoC émet un user factice `{'email': 'user'}` (`auth_bloc.dart:77`).

### 3.5 Rafraîchissement de session/token

#### React Web

**Aucun mécanisme de refresh token**. Recherche de `refresh_token`, `token_refresh`, `refreshToken` dans le code : **0 résultat**.

Quand le JWT expire :
1. L'appel API échoue avec 401
2. `apiClient.ts:104-108` intercepte, nettoie localStorage, redirige vers `/login`
3. L'utilisateur perd sa session sans avertissement

#### Flutter Mobile

**Aucun mécanisme de refresh token**. Quand le token expire :
1. L'API retourne 401
2. `api_service.dart:64` lance `UnauthorizedException`
3. Si non attrapée → crash potentiel de l'UI

---

## Étape 4 — Sécurité frontend

### 4.1 Secrets/clés API exposés

#### React Web

| Fichier:Ligne | Secret | Sévérité |
|---------------|--------|----------|
| `AdminSettingsPage.tsx:139-153` | Clés API AI providers (OpenAI, Groq, Anthropic, etc.) chargées depuis le backend et affichées dans des champs de formulaire | **HAUTE** — les clés transitéent par le frontend |
| `AdminSettingsPage.tsx:140` | `stripe_secret_key` chargé depuis le backend | **HAUTE** — clé serveur exposée au client |
| `AdminSettingsPage.tsx:216` | Clé envoyée dans le body à `/api/admin/settings/test-provider` | MOYEN |

**Aucune clé n'est codée en dur dans le source** — elles sont toutes fetchées depuis l'API backend. Mais le fait qu'elles transitéent par le frontend est un risque.

#### Flutter Mobile

| Fichier:Ligne | Secret | Sévérité |
|---------------|--------|----------|
| `app_constants.dart:6-7` | `student@demo-academy.edu` / `password123` | **CRITIQUE** — credentials en dur dans le code compilé |
| `login_screen.dart:179-180` | Mêmes credentials affichés dans l'UI | **CRITIQUE** — visibles par n'importe qui |

### 4.2 Guards de rôle — évaluation de robustesse

| Guard | Mécanisme | Contournable ? | Preuve |
|-------|-----------|----------------|--------|
| `RequireAuth` (React) | Vérifie existence chaîne `token` dans localStorage | **OUI** — `localStorage.setItem("token", "fake")` suffit | `App.tsx:100-104` |
| `RequireRole` (React) | Compare `user.role` (localStorage) contre liste | **OUI** — `localStorage.setItem("user", JSON.stringify({role:"SUPER_ADMIN"}))` suffit | `App.tsx:106-119` |
| `TeacherWriteGuard` (React) | `pointer-events-none` CSS + opacity | **OUI** — contenu rendu dans le DOM, inspectable | `TeacherStateGuard.tsx:58-81` |
| Aucun guard (Flutter) | — | **OUI** — navigation directe vers `/home` | `router.dart` (pas de redirect) |

**Conclusion** : Les guards sont **purement visuels**. La seule sécurité réelle est la validation côté serveur sur chaque endpoint API. Si le backend ne vérifie pas le rôle sur chaque requête, l'escalation de privilèges est triviale.

### 4.3 XSS — échappement/sanitization

| Zone | Mécanisme | Fichier | Évaluation |
|------|-----------|---------|------------|
| `dangerouslySetInnerHTML` (4 instances) | `DOMPurify.sanitize()` | `AdminCoursesPage.tsx:416`, `PlayerPage.tsx:418,425`, `CoursePlayerPage.tsx:411` | ✅ Sécurisé |
| Contenu IA affiché | Text interpolation React (`{answer}`) | `LearnerAIChatPage.tsx`, `TeacherAIStudio.tsx` | ✅ Sécurisé (auto-escaping) |
| Contenu utilisateur | Text interpolation React | Tous les formulaires | ✅ Sécurisé |

**DOMPurify** est importé dans 3 fichiers (`AdminCoursesPage.tsx:6`, `PlayerPage.tsx:6`, `CoursePlayerPage.tsx:11`) et utilisé avec les paramètres par défaut (sécurisé).

### 4.4 Validation des formulaires

| Formulaires | Validation client | Validation serveur | Contournable ? |
|-------------|-------------------|--------------------|--------------------|
| LoginPage | HTML5 `required`, `type="email"` | ✅ Oui | **OUI** — minimal |
| RegisterPage | `required`, `minLength={8}`, check school | ✅ Oui | **OUI** — pas de regex password |
| ForgotPassword | `required`, `type="email"` | ✅ Oui | **OUI** |
| ResetPassword | `required`, `minLength={8}`, match confirm | ✅ Oui | **OUI** |
| Formulaires admin | ❌ Pas de validation client systématique | ✅ Oui | **OUI** — tous contournables |

**Pas de bibliothèque de validation** (zod, yup, joi) — chaque formulaire gère la validation de manière ad hoc.

### 4.5 Token en URL (React)

**Fichier** : `conversations.ts:71`
```typescript
export function getExportUrl(conversationId: number, format: "pdf" | "docx"): string {
  const token = localStorage.getItem("token");
  return `/api/conversations/${conversationId}/export/${format}?token=${token}`;
}
```
Le JWT est passé en **query parameter** pour les exports PDF/DOCX. Risque : logs serveur, header Referer, monitoring réseau.

---

## Étape 5 — Qualité UX et accessibilité

### 5.1 États de chargement et états vides

#### React Web

| Catégorie | Fichiers concernés | Observation |
|-----------|-------------------|-------------|
| **Skeleton personnalisé** | `StudentDashboard.tsx` (StatSkeleton, ObjectiveSkeleton), `PacksPage.tsx` (PackSkeleton) | ✅ Bonne pratique |
| **Spinner générique** | `ChildDetailPage.tsx:60`, `ParentDashboardPage.tsx:41`, `ParentMessaging.tsx:77`, `PlacementTestPage.tsx:75` | ⚠️ Acceptable mais basique |
| **Texte "..."** | `TeacherDashboard.tsx:132-168` | ⚠️ Pas visuellement clair |
| **Composant Skeleton dispo** | `components/Skeleton.tsx` (Skeleton, CardSkeleton, ListSkeleton, TableSkeleton) | ❌ Sous-utilisé — la plupart des pages réinventent |
| **Pas d'état de chargement** | `AdminCoursesPage.tsx` (loading existe mais pas de spinner), `PlatformSettings.tsx` | ⚠️ Flash de contenu vide |

**États vides** : Présents dans ~12 pages (AdminTable par défaut : "Aucune donnée", StudentPackPage : "Aucun pack", etc.) mais absents dans les dashboards, wallet, gamification, inbox.

#### Flutter Mobile

| Écran | Loading | Empty | Error |
|-------|---------|-------|-------|
| Splash | `CircularProgressIndicator` | N/A | N/A |
| Login | Spinner dans le bouton | N/A | Red SnackBar |
| Home Dashboard | **AUCUN** (données hardcodées) | **AUCUN** | **AUCUN** |
| Cours | `CircularProgressIndicator` | "No courses available" | Texte + Retry |
| Détail cours | `CircularProgressIndicator` | "No lessons yet" | **Silencieux** (pas de message) |
| Devoirs | `CircularProgressIndicator` | "No assignments" | Texte + Retry |
| AI Tutor | "Thinking..." + spinner | Message initial | Message d'erreur dans le chat |

### 5.2 i18n Français/Arabe

#### React Web

**Infrastructure** : i18next + 3 locales (fr, en, ar) — `i18n/index.ts`

**Adoption** : **QUASI-INEXISTANTE**

| Fichier | Utilise `useTranslation` ? | Langues UI |
|---------|---------------------------|------------|
| `PlacementTestPage.tsx` | ✅ Oui | FR/AR/EN |
| `ProfilePage.tsx` | ✅ Oui | FR/AR/EN |
| `OnboardingPage.tsx` | ✅ Oui | FR/AR/EN |
| `LanguageSelector.tsx` | ✅ Oui | FR/AR/EN |
| **Tous les autres ~96 fichiers** | ❌ Non | **FR uniquement (hardcodé)** |

**Preuve** : Les locales contiennent 119 clés chacune, mais le vocabulaire réel du UI (boutons, messages, labels) est estimé à 500+ termes. Seuls nav, dashboard, tier, catalog, packs, profile, language, placement, onboarding, auth sont couverts.

### 5.3 RTL (Right-to-Left)

#### React Web — **STRUCTURELLEMENT CASSÉ**

| Problème | Preuve | Impact |
|----------|--------|--------|
| `document.documentElement.dir` pas initialisé au démarrage | `App.tsx` ne contient aucun `useEffect` pour le `dir` | Les utilisateurs arabes voient LTR jusqu'à naviguer vers Profile/Onboarding |
| 160+ classes physiques directionnelles (`ml-`, `pr-`, `text-left`) | `StudentDashboard.tsx:261`, `StudentWallet.tsx:105,128`, `FinancialHub.tsx:181-283`, etc. | **Layout cassé en RTL** — les marges/paddings ne s'inversent pas |
| 106 instances `text-left`/`text-right` | `TeacherSalesPage.tsx:159-164`, `AdminDashboardPage.tsx:320-339`, etc. | Texte aligné à gauche en mode arabe |
| Police Tajawal importée mais jamais appliquée | `tailwind.config.js:30` définit `font-arabic: Tajawal` mais aucune classe `font-arabic` dans les TSX | Texte arabe en DM Sans |

**Seuls 4 fichiers ont une tentative de RTL** :
- `LanguageSelector.tsx:19` — set `dir="rtl"`
- `ProfilePage.tsx:32` — set `dir="rtl"`
- `OnboardingPage.tsx:26` — set `dir="rtl"`
- `LearnerAIChatPage.tsx:50-55` — détection direction input

#### Flutter Mobile — **ABSENT TOTAL**

Aucun `locale`, `localizationsDelegates`, `supportedLocales`, ni `Directionality` widget. Toute l'UI est LTR.

### 5.4 Cohérence du design system

#### Palette

| Couleur | Définie dans Tailwind | Utilisation | Fichiers hors charte |
|---------|----------------------|-------------|----------------------|
| `navy #0D1B2A` | ✅ `tailwind.config.js:8` | 502+ références | — |
| `orange #FF6B2B` | ✅ `tailwind.config.js:5` | 386+ références | — |
| `indigo` (défaut Tailwind) | ❌ Non définie | **58 occurrences** | `PlacementTestPage.tsx`, `OnboardingPage.tsx`, `CourseEditorPage.tsx`, `PlayerPage.tsx`, `CoursePlayerPage.tsx`, `CatalogPage.tsx`, `CourseBuilderPage.tsx`, `AdminMediaLibraryPage.tsx` |

**Le indigo n'est pas dans la charte EDUAI** — il dérive de la palette par défaut de Tailwind.

#### Fonts

| Police | Rôle | Définie | Utilisée |
|--------|------|---------|----------|
| Cormorant Garamond | Display (titres) | `tailwind.config.js:27` | `font-display` (59 uses) |
| DM Sans | Body | `tailwind.config.js:28` | Par défaut |
| Tajawal | Arabe | `tailwind.config.js:30` | **Jamais appliquée** |

**Incohérence** : `font-[300]` (173 uses) vs `font-display` (59 uses). `font-[300]` applique le weight 300 à DM Sans (pas à Cormorant Garamond), ce qui est visuellement différent de `font-display`.

#### Flutter

Palette indigo `#4F46E5` et purple `#9333EA` — **ne correspond pas** à la charte navy/orange du React. La charte n'est pas partagée entre les deux frontends.

### 5.5 Accessibilité de base

| Critère | React | Flutter |
|---------|-------|---------|
| Labels de formulaires | ⚠️ Présents mais `htmlFor` pas systématique | ⚠️ `labelText` sur certains TextField |
| Contraste | ⚠️ Non vérifié systématiquement | ❌ Non vérifié |
| Navigation clavier | ⚠️ Non testé | N/A |
| ARIA attributes | ❌ Quasi-absents | N/A |

### 5.6 Responsive design

| Breakpoint | Utilisation | Observation |
|------------|-------------|-------------|
| `sm:` | Peu utilisé | Quelques grilles seulement |
| `md:` | **Le plus utilisé** | Grilles 1→2 colonnes, 2→4 colonnes |
| `lg:` | Utilisé pour sidebar | Sidebar responsive (cachée sur mobile) |
| `xl:` | **Jamais utilisé** | Pas d'optimisation grand écran |

**Layouts sidebar** : `DashboardLayout.tsx:127-129` — sidebar cachée sur mobile avec bouton toggle. Utilisable sur tablette/mobile.

**Auth pages** : Split layout (`lg:flex`) — panneau branding caché sur mobile.

**Évaluation** : Les dashboards sont **utilisables** sur mobile/tablette grâce aux grilles responsive, mais pas **optimisés** (pas de `xl:`, pas de `sm:` sur les stat cards).

---

## Étape 6 — Qualité de code et dette technique

### 6.1 Composants dupliqués

| Pattern dupliqué | Nombre de copies | Exemples |
|------------------|-----------------|----------|
| Loading spinner boilerplate | 68+ fichiers | `animate-spin rounded-full h-8 w-8 border-b-2 border-orange` |
| Toast notification | 15+ copies identiques | `fixed top-4 right-4 z-50 px-4 py-2 rounded-xl text-white` |
| TIER_COLORS object | 3 copies | `StudentPackPage.tsx:40-45`, `ParentPackPage.tsx:30-37`, `TeacherAbonnementsPage.tsx:28-45` |
| Fetch + header + error boilerplate | 50+ fichiers | Pattern `headers={Authorization: Bearer}`, `res.ok`, `res.json()` |
| Search input | 5+ copies | `MyLearning.tsx:117-122`, `EnrollmentManager.tsx:106-111`, etc. |

### 6.2 Code mort et console.log

| Type | Nombre | Détails |
|------|--------|---------|
| `console.log` en production | **5+** | `UserManagementView.tsx:115,179,191`, `apiClient.ts:168` (global interceptor log), `hooks/index.ts:46,57` |
| `console.error` (catch) | ~95 | Acceptable pour le logging mais devrait utiliser un logger structuré |
| `console.warn` | 1+ | `PlatformSettings.tsx:206` |
| TODO/FIXME/HACK | **0** | Aucun trouvé |
| Code mort Flutter | Multiple | `AppConstants.appName` (jamais importé), `CoursesBloc` (jamais injecté), `SecureStorage.saveUser()` (jamais appelé), 3 packages non importés |

### 6.3 Couverture de tests

#### React Web

| Métrique | Valeur |
|----------|--------|
| Fichiers de test | 3 (`LoginPage.test.tsx`, `CourseCatalog.test.tsx`, `MyLearning.test.tsx`) |
| Composants page testés | 3 / ~55 = **5.5%** |
| Framework | Vitest + @testing-library/react |

**Pages testées** : LoginPage (7 tests), CourseCatalog (9 tests), MyLearning (10 tests)  
**Pages NON testées** : Toutes les pages admin (23), parent (6), teacher (11 sauf MyLearning), student (17 sauf CourseCatalog), learner (5), auth (3 sauf Login)

#### Flutter Mobile

| Métrique | Valeur |
|----------|--------|
| Fichiers de test | **0** |
| Widget tests | **0** |
| Framework | flutter_test (déclaré mais jamais utilisé) |

### 6.4 Performance

| Aspect | React | Flutter |
|--------|-------|---------|
| Lazy loading | ✅ `React.lazy()` sur toutes les pages (`App.tsx:15-89`) | N/A (15 fichiers, pas de lazy) |
| Code splitting | ✅ Automatique via Vite | N/A |
| Bundle size | ❌ Non mesurable dans cet environnement | N/A |
| Images non optimisées | ❌ Non vérifié | `assets/images/` vide |
| Bundle Flutter | ❌ Non buildable dans cet environnement | — |

### 6.5 Gestion d'état — state dupliqué

| Donnée | Sources multiples | Risque |
|--------|-------------------|--------|
| Token | `authStore.ts` (Zustand) + `localStorage` (20+ lectures directes) | Désynchronisation si modification externe |
| User | `authStore.ts` (Zustand) + `localStorage` | Idem |
| Abonnements | `StudentPackPage.tsx`, `TeacherAbonnementsPage.tsx`, `ParentPackPage.tsx` — chacun fetch indépendamment | Pas de cache partagé |
| Wallet balance | `StudentWallet.tsx`, `TeacherWallet.tsx`, `ParentWalletPage.tsx` — fetch indépendant | Pas de source unique |

### 6.6 Architecture API — incohérences

| Pattern | Nombre | Exemples |
|---------|--------|----------|
| `ApiClient` singleton (`apiClient.ts`) | Utilisé par ~20% des pages | `StudentPackPage`, `StudentWallet`, `PlacementTestPage` |
| Raw `fetch()` avec headers manuels | Utilisé par ~60% des pages | `TeacherDashboard`, `ClassroomManager`, `GamificationPage`, etc. |
| Feature-specific API modules | Utilisé par ~20% des pages | `tierAPI`, `parentAPI`, `pathway API`, `moduleApi` |

**11 wrappers de fetch indépendants** identifiés, chacun ré-injectant le token et gérant les erreurs différemment. Le `ApiClient` centralisé a des intercepteurs 401 mais la majorité du code l'ignore.

---

## Étape 7 — Synthèse et prioritisation

### 7.1 Risques classés par sévérité

#### CRITIQUE (sécurité / casse fonctionnelle)

| # | Risque | Frontend | Fichier:Ligne | Impact |
|---|--------|----------|---------------|--------|
| C1 | Token JWT en localStorage (XSS) | React | `authStore.ts:77` + 20 fichiers | Vol de session |
| C2 | Route guards bypassables (rôle en localStorage) | React | `App.tsx:106-119` | Escalation de privilèges |
| C3 | Démo credentials en dur + affichés | Flutter | `app_constants.dart:6-7`, `login_screen.dart:179-180` | Accès non autorisé |
| C4 | HTTP non sécurisé (pas de TLS) | Flutter | `api_service.dart:5` | Interception réseau |
| C5 | TeacherAbonnementsPage cassé (API undefined) | React | `TeacherAbonnementsPage.tsx:69` | Page entièrement non fonctionnelle |
| C6 | Clés API AI/Stripe transitées par le frontend | React | `AdminSettingsPage.tsx:139-153` | Fuite de secrets serveur |

#### IMPORTANT (fiabilité / UX)

| # | Risque | Frontend | Fichier:Ligne | Impact |
|---|--------|----------|---------------|--------|
| I1 | Pas de refresh token | Les deux | — | Déconnexions brutales |
| I2 | i18n quasi-inexistante (4/100 fichiers) | React | `i18n/index.ts` + 4 fichiers | UI 100% français |
| I3 | RTL structurellement cassé (160+ classes physiques) | React | Tous les fichiers directionnels | Layout arabe illisible |
| I4 | Pas de RTL du tout | Flutter | — | Pas d'arabe |
| I5 | ApiService sans token dans les écrans Flutter | Flutter | `courses_screen.dart:29`, `assignments_screen.dart:52,165`, `ai_tutor_screen.dart:53` | 401 sur toutes les requêtes |
| I6 | Dashboard Flutter entièrement hardcodé | Flutter | `home_screen.dart:138,148,156` | Données fictives affichées |
| I7 | Couverture tests 5.5% React, 0% Flutter | Les deux | 3 fichiers test React, 0 Flutter | Régressions non détectées |
| I8 | SoftSkillsCatalogPage sans RequireRole | React | `App.tsx:243` | Accès non contrôlé |
| I9 | Token en URL query parameter | React | `conversations.ts:71` | Fuite via logs/Referer |
| I10 | console.log en production | React | `UserManagementView.tsx:115,179,191` | Fuite d'infos debug |
| I11 | Police Tajawal importée mais jamais appliquée | React | `tailwind.config.js:30` | Texte arabe en DM Sans |
| I12 | Indigo hors charte (58 occurrences) | React | 12+ fichiers | Incohérence visuelle |

#### MINEUR (dette technique)

| # | Risque | Frontend | Impact |
|---|--------|----------|--------|
| M1 | axios en dépendance mais jamais importé | React | Poids mort |
| M2 | 3 packages Flutter déclarés mais jamais importés | Flutter | Poids mort |
| M3 | 15+ copies de toast notification | React | Maintenance difficile |
| M4 | 68+ copies de loading spinner | React | Maintenance difficile |
| M5 | TIER_COLORS dupliqué 3 fois | React | Maintenance difficile |
| M6 | 11 wrappers fetch indépendants | React | Incohérence architecture |
| M7 | `font-[300]` vs `font-display` (173 vs 59 uses) | React | Incohérence typographique |
| M8 | `VITE_API_URL` jamais lu via import.meta.env | React | Variable d'env inutile |
| M9 | `AppConstants.apiBaseUrl` jamais importé | Flutter | Code mort |
| M10 | `CoursesBloc` défini mais jamais injecté | Flutter | Code mort |
| M11 | `SecureStorage.saveUser()` jamais appelé | Flutter | Code mort |
| M12 | `shared_preferences` déclaré mais jamais importé | Flutter | Dépendance inutile |
| M13 | Erreurs silencieuses (`catch(() => {})`) | React | Debug difficile |
| M14 | Token lu au niveau module (stale) | React | `AdminTokenPackagesPage.tsx:6` |
| M15 | GoRouter vs Navigator冲突 | Flutter | Navigation incohérente |

### 7.2 Tableau des pages manquantes / écarts de parité

| Fonctionnalité | React Web | Flutter Mobile | Action requise |
|----------------|-----------|----------------|----------------|
| Auth (Register) | ✅ | ❌ | Créer RegisterScreen Flutter |
| Auth (Forgot/Reset) | ✅ | ❌ | Créer ou reporter |
| Dashboard Admin (23 pages) | ✅ | ❌ | Hors périmètre Flutter (student only) |
| Dashboard Teacher (12 pages) | ✅ | ❌ | Hors périmètre Flutter (student only) |
| Dashboard Student | ✅ (18 pages) | ⚠️ Placeholder | Implémenter les données réelles |
| Dashboard Parent | ✅ (6 pages) | ❌ | Hors périmètre Flutter (student only) |
| Mon Pack | ✅ | ❌ | Implémenter dans Flutter |
| Wallet | ✅ | ❌ | Implémenter dans Flutter |
| Cours (catalogue + player) | ✅ | ⚠️ Basique | Enrichir le player Flutter |
| Tutor IA | ✅ (SSE streaming) | ⚠️ Basique | Ajouter le streaming |
| Gamification | ✅ | ❌ | Implémenter dans Flutter |
| i18n FR/AR | ⚠️ Infra seule | ❌ | Implémenter les deux côtés |
| RTL | ⚠️ Cassé | ❌ | Corriger React + créer Flutter |

### 7.3 Incohérences frontend/backend

| Type | Détails |
|------|---------|
| **Variable API undefined** | `TeacherAbonnementsPage.tsx:69` — toutes les URLs contiennent `undefined` |
| **URLs Flutter non vérifiées** | `GET /api/academy/courses`, `GET /api/lms/assignments`, `GET /api/academy/courses/{id}/modules` — ❌ non vérifié si ces routes existent côté backend |
| **VITE_API_URL non lu** | `authStore.ts:9` et `apiClient.ts:14` codent `API_URL = ""` au lieu de lire `import.meta.env.VITE_API_URL` |
| **Token en URL** | `conversations.ts:71` — JWT passé en query parameter pour les exports |
| **Refresh token absent** | Backend a `/auth/refresh` mais le frontend ne l'appelle jamais |

### 7.4 Statistiques globales

| Métrique | React Web | Flutter Mobile |
|----------|-----------|----------------|
| Pages/écrans | ~55 composants page | 5 écrans fonctionnels |
| Appels API distincts | ~180 endpoints | 7 endpoints |
| Fichiers source TSX/TS | 100+ | 15 fichiers Dart |
| Tests | 3 fichiers (26 tests) | 0 |
| Couverture tests | 5.5% des pages | 0% |
| Écarts RTL identifiés | 160+ classes physiques, 106 text-left/right | N/A (pas de RTL) |
| Dépendances inutilisées | 1 (axios) | 3 (shared_preferences, cached_network_image, shimmer) |
| console.log production | 5+ | 0 |
| Guards de rôle | 3 (tous bypassables) | 0 |
| i18n files avec useTranslation | 4 / 100+ | 0 / 15 |

---

*Rapport généré le 04 août 2026 par analyse en lecture seule du code source.*

# FRONTEND ARCHITECTURE AUDIT — EDUAI Learning

**Date :** 05/08/2026
**Scope :** `frontend/src/` — React 18 + TypeScript + Vite + Tailwind
**Auteur :** Architecte Frontend Senior

---

## 1. CARTOGRAPHIE DE L'ARBORESCENCE

```
src/
├── __tests__/                    3 fichiers  (token, tokenStorage, apiClient)
├── api/                          6 fichiers  (couche service centralisée)
│   ├── catalog.ts
│   ├── conversations.ts
│   ├── courses.ts
│   ├── lms.ts
│   ├── tier.ts
│   └── wallet.ts
├── components/                   9 fichiers  (composants partagés)
│   ├── layout/
│   │   └── DashboardLayout.tsx
│   ├── DailyObjective.tsx
│   ├── ErrorBoundary.tsx
│   ├── LanguageSelector.tsx
│   ├── RecommendedPath.tsx
│   ├── Skeleton.tsx
│   ├── TeacherStateGuard.tsx
│   ├── TierBadge.tsx
│   └── WalletWidget.tsx
├── features/                    89 fichiers  (logique métier par rôle)
│   ├── admin/                   41 pages + 6 composants + 1 API
│   │   ├── api/index.ts
│   │   ├── components/ (AdminTable, KPICard, Modal, PaginationControls, StatusBadge, index)
│   │   └── pages/ (41 fichiers — old/ vide)
│   ├── auth/                     4 pages
│   │   └── pages/ (LoginPage, RegisterPage, ForgotPassword, ResetPassword)
│   ├── learner/                  1 page + 1 dossier vide
│   │   ├── components/ (vide)
│   │   └── pages/ (PlayerPage)
│   ├── parent/                   6 pages + 1 API
│   │   ├── api/index.ts
│   │   └── pages/ (6 fichiers)
│   ├── pathway/                  1 API
│   │   └── api/index.ts
│   ├── student/                 14 pages
│   │   └── pages/ (14 fichiers)
│   └── teacher/                 13 pages + 2 API
│       ├── api/ (index.ts, moduleApi.ts)
│       └── pages/ (13 fichiers)
├── hooks/                        2 fichiers
│   ├── index.ts (useOnlineStatus, useDebounce, useLocalStorage, useClickOutside)
│   └── useAIStream.ts
├── i18n/                         4 fichiers
│   ├── index.ts
│   └── locales/ (ar.json, en.json, fr.json)
├── pages/                        7 fichiers  (pages « orphelines » hors features/)
│   ├── admin/
│   │   └── AdminMediaLibraryPage.tsx
│   └── learner/ (CatalogPage, CoursePlayerPage, LearnerAIChatPage, SoftSkillsCatalogPage)
├── resources/                    (dossier assets)
├── store/                        2 fichiers  (Zustand)
│   ├── authStore.ts
│   └── conversationStore.ts
├── test/                         (config de test)
├── utils/                        2 fichiers
│   ├── apiClient.ts
│   └── tokenStorage.ts
├── App.tsx                       (routeur principal — 288 lignes)
├── index.css
└── index.jsx
```

**Résumé :**

| Dossier | Fichiers TSX | Fichiers TS | Total |
|---------|-------------|-------------|-------|
| `features/admin/` | 41 | 2 | 43 |
| `features/student/` | 14 | 0 | 14 |
| `features/teacher/` | 13 | 2 | 15 |
| `features/parent/` | 6 | 1 | 7 |
| `features/auth/` | 4 | 0 | 4 |
| `features/learner/` | 1 | 0 | 1 |
| `pages/` (orphelins) | 7 | 0 | 7 |
| `components/` | 9 | 0 | 9 |
| `api/` | 0 | 6 | 6 |
| `store/` | 0 | 2 | 2 |
| `hooks/` | 0 | 2 | 2 |
| `utils/` | 0 | 2 | 2 |
| `__tests__/` | 0 | 3 | 3 |
| **TOTAL** | **103** | **23** | **126** |

**Lignes de code :** ~23 500 lignes TSX, ~2 500 lignes TS → **~26 000 lignes totales**

---

## 2. INVENTAIRE DES PAGES ET ROUTAGE

### 2.1 — Architecture de routage

- **Router :** React Router v6 (`react-router-dom ^6.22.0`)
- **Lazy loading :** Toutes les pages utilisent `React.lazy()` + `Suspense`
- **Layout :** `DashboardLayout` pour teacher/student/parent, `AdminLayout` pour super_admin, `SchoolAdminLayout` pour admin_school
- **Guard auth :** `RequireAuth` (vérifie token + expiration JWT)
- **Guard rôle :** `RequireRole` (compare `user.role` aux rôles autorisés)
- **Guard teacher :** `TeacherWriteGuard` (vérifie `is_approved` + `subscription_plan`)

### 2.2 — Inventaire complet des routes

| Route | Page | Rôle requis |
|-------|------|-------------|
| `/login` | LoginPage | Public |
| `/register` | RegisterPage | Public |
| `/forgot-password` | ForgotPasswordPage | Public |
| `/reset-password` | ResetPasswordPage | Public |
| `/onboarding` | OnboardingPage | Auth |
| **Admin (super_admin, pedagogical_admin)** | | |
| `/dashboard/admin` | AdminDashboardPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/users` | AdminUsersPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/schools` | AdminSchoolsPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/courses` | AdminCoursesPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/courses/:id` | CourseEditorPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/analytics` | AdminAnalyticsPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/teachers` | AdminTeacherQueuePage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/finance` | FinanceCenter | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/media` | AdminMediaLibraryPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/inbox` | AdminInboxView | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/ai-factory` | ContentCreatorAI | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/course-distribution` | SchoolCourseDistribution | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/teacher-catalog` | SuperAdminCourseFactory | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/broadcast` | BroadcastCenter | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/settings` | AdminSettingsPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/packages` | AdminTokenPackagesPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/invite-codes` | AdminInviteCodesPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/audit` | AdminAuditLogPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/pedagogical-review` | PedagogicalAdminPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/arborescence` | AdminArborescencePage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/publication-status` | AdminPublicationStatusPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/seuils-config` | AdminSeuilsConfigPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| `/dashboard/admin/specialites-pedagogiques` | AdminSpecialitesPedagogiquesPage | SUPER_ADMIN, PEDAGOGICAL_ADMIN |
| **School Admin** | | |
| `/dashboard/school` | SchoolOverview | ADMIN_SCHOOL, PEDAGOGICAL_LEAD |
| `/dashboard/school/users` | UserManagementView | ADMIN_SCHOOL, PEDAGOGICAL_LEAD |
| `/dashboard/school/finance` | FinanceCenter | ADMIN_SCHOOL, PEDAGOGICAL_LEAD |
| `/dashboard/school/courses` | AdminCoursesPage | ADMIN_SCHOOL, PEDAGOGICAL_LEAD |
| `/dashboard/school/teachers` | AdminTeacherQueuePage | ADMIN_SCHOOL, PEDAGOGICAL_LEAD |
| `/dashboard/school/settings` | AdminSettingsPage | ADMIN_SCHOOL, PEDAGOGICAL_LEAD |
| `/dashboard/school/pedagogical` | PedagogicalLeadPage | ADMIN_SCHOOL, PEDAGOGICAL_LEAD |
| **Teacher** | | |
| `/dashboard` (index) | TeacherDashboard | TEACHER |
| `/dashboard/teacher/learning` | MyLearning | TEACHER |
| `/dashboard/teacher/classroom` | ClassroomManager | TEACHER |
| `/dashboard/teacher/ai-studio` | TeacherAIStudio | TEACHER + TeacherWriteGuard |
| `/dashboard/teacher/wallet` | TeacherWallet | TEACHER |
| `/dashboard/teacher/sales` | TeacherSalesPage | TEACHER |
| `/dashboard/teacher/abonnements` | TeacherAbonnementsPage | TEACHER |
| `/dashboard/teacher/reorientations` | TeacherReorientationPage | TEACHER + TeacherWriteGuard |
| `/dashboard/teacher/validation-contenu` | TeacherValidationContenuPage | TEACHER + TeacherWriteGuard |
| `/dashboard/teacher/parcours` | TeacherParcoursPage | TEACHER + TeacherWriteGuard |
| `/dashboard/teacher/elements` | TeacherElementsPage | TEACHER + TeacherWriteGuard |
| `/dashboard/teacher/bibliotheque` | TeacherBibliothequePage | TEACHER |
| **Student** | | |
| `/dashboard` (index) | StudentDashboard | STUDENT |
| `/dashboard/courses` | CatalogPage | STUDENT |
| `/dashboard/courses/:id` | CoursePlayerPage | STUDENT, TEACHER |
| `/dashboard/courses/:id/lessons/:lessonId` | CoursePlayerPage | STUDENT, TEACHER |
| `/dashboard/assignments` | StudentCourseCatalog | STUDENT |
| `/dashboard/ai-tutor` | LearnerAIChatPage | STUDENT, TEACHER |
| `/dashboard/wallet` | StudentWallet | STUDENT |
| `/dashboard/packs` | PacksPage | STUDENT |
| `/dashboard/my-pack` | StudentPackPage | STUDENT |
| `/dashboard/tier` | StudentTierPage | STUDENT |
| `/dashboard/soft-skills` | SoftSkillsCatalogPage | Auth |
| `/dashboard/placement/:testId` | PlacementTestPage | STUDENT |
| `/dashboard/profile` | ProfilePage | STUDENT, TEACHER |
| `/dashboard/assimilation` | StudentAssimilationProfilePage | STUDENT |
| `/dashboard/parcours-catalog` | PathwayCatalogPage | STUDENT, TEACHER |
| `/dashboard/mon-parcours` | MonParcoursPage | STUDENT |
| `/dashboard/gamification` | GamificationPage | STUDENT, TEACHER |
| `/dashboard/inbox` | InboxPage | Auth |
| **Parent** | | |
| `/dashboard/parent` | ParentDashboardPage | PARENT |
| `/dashboard/parent/enfant/:id` | ChildDetailPage | PARENT |
| `/dashboard/parent/enfant/:id/wallet` | ParentWalletPage | PARENT |
| `/dashboard/parent/enfant/:id/pack` | ParentPackPage | PARENT |
| `/dashboard/parent/famille` | ParentFamillePage | PARENT |
| **Public** | | |
| `/learn/courses` | CatalogPage | Public |
| `/learn/courses/:id` | CoursePlayerPage | Public |
| `/learn/courses/:id/lessons/:lessonId` | CoursePlayerPage | Public |

**Total :** ~65 routes, ~55 pages lazy-loadées

---

## 3. ANALYSE DES APPELS API

### 3.1 — Couche service centralisée (`src/api/`)

| Fichier | Entités couvertes | Méthodes |
|---------|-------------------|----------|
| `lms.ts` | Courses, Chapters, Lessons, Quizzes, Learner | `adminCoursesAPI`, `adminChaptersAPI`, `adminLessonsAPI`, `adminQuizzesAPI`, `learnerAPI` |
| `courses.ts` | Courses (admin) | `coursesAdmin` (list, get, create, update, delete, publish, unpublish) |
| `catalog.ts` | Catalogue learner, Player, Certificats | `catalogAPI`, `enrollmentAPI`, `playerAPI` |
| `tier.ts` | Dashboard étudiant, Tier, Objectifs | `tierAPI` |
| `wallet.ts` | Wallet balance, history, purchase | `getWalletBalance`, `getWalletHistory`, `purchaseCredits` |
| `conversations.ts` | Conversations IA | CRUD conversations, messages, export PDF/DOCX |

### 3.2 — API features (`src/features/*/api/`)

| Fichier | Entités | Méthodes |
|---------|---------|----------|
| `admin/api/index.ts` (776 lignes) | Users, Schools, Settings, Wallets, Invitations, Audit, Pedagogical | ~30 méthodes |
| `teacher/api/index.ts` (158 lignes) | Classes, Students, Courses assignés | CRUD classes |
| `teacher/api/moduleApi.ts` | Modules pédagogiques | CRUD modules |
| `parent/api/index.ts` (86 lignes) | Enfants, Wallet parent, Pack parent | getChildren, getWallet, getPack |
| `pathway/api/index.ts` (228 lignes) | Parcours, Matières, Spécialités, Éléments | CRUD pathway |

### 3.3 — Client API centralisé (`src/utils/apiClient.ts`)

`ApiClient` class avec intercepteurs request/response, refresh token sur 401, gestion d'erreurs 429/404/500.

### 3.4 — ⚠️ PROBLÈME : Appels `fetch()` direct dans les composants

**70+ appels `fetch()` inline** dans les pages admin, 18 dans student, 26 dans teacher. Ces appels bypassent le client API centralisé (`apiClient.ts`) et dupliquent la logique d'authentification.

**Exemples critiques :**

| Fichier | Appels `fetch()` inline | Endpoints appelés |
|---------|------------------------|-------------------|
| `AdminSettingsPage.tsx` | 1 | `/api/admin/settings/test-provider` |
| `UserManagementView.tsx` | 6 | `/api/admin/users`, `/api/admin/schools`, toggle-active, approve |
| `AdminCoursesPage.tsx` | 0 (utilise `lms.ts`) | — |
| `CourseEditorPage.tsx` | 1 + `lms.ts` | Mix des deux approches |
| `AdminDashboard.tsx` | 5 | `/api/admin/dashboard/stats`, users, courses, approve, status |
| `PlatformOverview.tsx` | 4 | dashboard, users, courses, transactions |
| `AdminInboxView.tsx` | 4 | messages CRUD |
| `ContentModerationView.tsx` | 6 | courses CRUD, enrollments |
| `GamificationPage.tsx` | 3 | badges, streak, rankings |
| `TeacherDashboard.tsx` | 3 | my-courses, classes, wallet |
| `ClassroomManager.tsx` | 5 | classes CRUD, students |
| `TeacherAbonnementsPage.tsx` | 5 | abonnements CRUD |

### 3.5 — ⚠️ DOUBLONS D'ENTITÉS

| Entité | Fichiers qui la gèrent | Conflit |
|--------|------------------------|---------|
| **Courses** | `api/lms.ts` (`adminCoursesAPI`), `api/courses.ts` (`coursesAdmin`), `features/admin/api/index.ts` | 3 sources de vérité pour les mêmes endpoints `/api/admin/courses` |
| **Wallet** | `api/wallet.ts`, inline `fetch()` dans 5+ pages | Le service centralisé existe mais n'est pas utilisé partout |
| **Abonnements** | `features/teacher/api/index.ts` (non), inline `fetch()` dans `TeacherAbonnementsPage.tsx` et `StudentDashboard.tsx` | Pas de service dédié |
| **Settings** | `features/admin/api/index.ts`, inline `fetch()` dans `AdminSettingsPage.tsx` et `PlatformSettings.tsx` | 2 pages admin pour les settings |
| **Users** | `features/admin/api/index.ts`, inline `fetch()` dans `UserManagementView.tsx` et `AdminUsersPage.tsx` | 2 pages admin pour les users |

---

## 4. GESTION D'ÉTAT

### 4.1 — Stores Zustand

| Store | Fichier | Responsabilité |
|-------|---------|----------------|
| `useAuthStore` | `store/authStore.ts` (163 lignes) | Token JWT, profil utilisateur, login/logout/register/restore |
| `useConversationStore` | `store/conversationStore.ts` (105 lignes) | Conversations IA (CRUD, message actif, loading) |

### 4.2 — Authentification

```
authStore.ts
├── user: User | null          ← Profil (id, email, role, school_id, etc.)
├── token: string | null       ← JWT access token
├── isLoading: boolean
├── error: string | null
├── login(email, password)     → POST /auth/login → GET /auth/me
├── register(...)              → POST /auth/register → GET /auth/me
├── registerTrialTeacher(...)  → POST /auth/register-trial-teacher → GET /auth/me
├── registerTeacher(...)       → POST /auth/teacher-register
├── logout()                   → clearAll
├── setUser(user)              → met à jour le store + localStorage
└── restore()                  → relit le token/user depuis localStorage, vérifie avec /auth/me
```

**Persistance :** `tokenStorage.ts` (localStorage wrapper) — token, refresh_token, user data
**Résolution du rôle :** `user.role` en DB (string) → comparaison `.toUpperCase()` dans `RequireRole` et `DashboardLayout`

### 4.3 — Patterns d'état dans les composants

- **États locaux (`useState`) :** La majorité des pages utilisent des états locaux pour `loading`, `data`, `error`
- **Aucun React Query / SWR :** Pas de cache serveur, pas de stale-while-revalidate, pas de refetch automatique
- **Aucun Context API :** Tout passe par Zustand stores ou props
- **Pas de state management pour les données transversales :** Le wallet, les abonnements, les packs sont re-fetchés à chaque navigation

---

## 5. COMPOSANTS UI ET DESIGN SYSTEM

### 5.1 — Composants réutilisables (`src/components/`)

| Composant | Type | Usage |
|-----------|------|-------|
| `DashboardLayout` | Layout | Sidebar + outlet (teacher/student/parent) |
| `ErrorBoundary` | Error | Catch React errors |
| `LanguageSelector` | UI | Switcher FR/EN/AR |
| `Skeleton` | UI | Loading states (shimmer) |
| `TeacherStateGuard` | Guard | Cache les boutons d'écriture pour teachers non approuvés |
| `TierBadge` | UI | Badge coloré par tier |
| `WalletWidget` | Widget | Mini-solde wallet dans la sidebar |
| `DailyObjective` | Widget | Objectif quotidien |
| `RecommendedPath` | Widget | Parcours recommandé |

### 5.2 — Composants admin (`features/admin/components/`)

| Composant | Type |
|-----------|------|
| `AdminTable` | Table réutilisable avec tri |
| `KPICard` | Carte de métrique |
| `Modal` | Modal générique |
| `PaginationControls` | Pagination |
| `StatusBadge` | Badge de statut |

### 5.3 — ⚠️ COMPOSANTS « DOUBLEURS »

**Aucun design system formalisé.** Les composants UI sont inline dans chaque page.

| Pattern | Occurrences | Différences |
|---------|-------------|-------------|
| **Boutons** | ~15 styles différents | `bg-indigo-600`, `bg-navy`, `bg-orange`, `bg-green-500` — aucune standardisation |
| **Cartes** | ~10 variantes | `rounded-xl shadow-sm`, `rounded-2xl shadow-dp`, `border border-black/5` |
| **Inputs** | ~8 variantes | `border-gray-300 rounded-lg`, `border-black/10 rounded-xl` |
| **Tables** | 2 implémentations | `AdminTable` (feature admin) + tables inline dans chaque page |
| **Loading spinners** | ~12 implémentations | `animate-spin rounded-full h-10 w-10 border-b-2` avec couleurs variées |
| **Empty states** | ~8 implémentations | Chaque page a son propre "Aucun résultat" |
| **Stat cards** | ~6 implémentations | Dashboard admin, school, teacher, student — chacun avec son style |
| **Modals** | ~4 implémentations | `AdminTable` modal, inline modals, `Modal` component |

### 5.4 — Tailwind CSS

- **Approche :** 100% inline, aucune factorisation via `@apply` ou composants
- **Palette :** `navy` (primary), `orange` (accent), `cream`, `gray` — définie dans `tailwind.config.js`
- **Consistance :** Faible — les classes varient d'un fichier à l'autre
- **Responsive :** Majoritairement `sm:` et `md:`, peu de `lg:` ou `xl:`
- **Dark mode :** Non implémenté

---

## 6. TOP 5 DES PAGES LES PLUS COMPLEXES

| # | Fichier | Lignes | Problèmes |
|---|---------|--------|-----------|
| 1 | `CourseEditorPage.tsx` | 822 | Logique édition cours + chapitres + leçons + quiz + drag-and-drop dans un seul composant. Mix UI + business logic + API calls. |
| 2 | `AdminSettingsPage.tsx` | 746 | Settings plateforme + provider test + toggle switches. 1 appel `fetch()` inline malgré le service dédié. |
| 3 | `UserManagementView.tsx` | 711 | CRUD users + balance management + school filter + invite codes. 6 appels `fetch()` inline. |
| 4 | `ContentCreatorAI.tsx` | 651 | Génération IA + upload PDF + historique + configuration. |
| 5 | `LearnerAIChatPage.tsx` | 584 | Chat IA streaming + conversations + export PDF/DOCX + historique. |

**Score de dette technique estimé :** Chacune de ces pages devrait être découpée en 3-5 sous-composants avec la logique métier extraite dans des hooks personnalisés ou des services.

---

## 7. CONCLUSION — 3 POINTS FAIBLES MAJEURS

### 1. Absence de couche API cohérente

**70+ appels `fetch()` inline** dans les composants, en plus des services centralisés dans `src/api/`. Cela crée :
- **Duplication de code** : chaque page ré-implémente la gestion du token, des erreurs, du Content-Type
- **Incohérence** : certains fichiers utilisent `apiClient.ts`, d'autres `api/lms.ts`, d'autres `fetch()` brut
- **Maintenance difficile** : un changement d'endpoint nécessite de modifier 3-5 fichiers
- **3 implémentations de `adminCoursesAPI`** qui appellent les mêmes endpoints

### 2. Pas de séparation UI / Business Logic

Les composants de 400-800 lignes mélangent :
- Appels API (`fetch`)
- Logique métier (calculs, transformations de données)
- État local (`useState` × 5-10 par composant)
- Rendu JSX complexe

**Aucun custom hook** pour extraire la logique (hors `hooks/index.ts` qui contient 4 utilitaires génériques). Pas de React Query pour la gestion du cache serveur.

### 3. Design System absent — composants non factorisés

- **15+ styles de boutons** différents
- **12+ implémentations de loading spinner**
- **8+ variantes de cartes**
- **Tables dupliquées** (AdminTable existe mais 80% des pages ont leur propre table inline)
- **Skeleton** existe mais n'est utilisé que dans 2-3 fichiers

Résultat : chaque page « réinvente » les mêmes éléments UI avec des classes Tailwind légèrement différentes, rendant la maintenance visuelle impossible et les refactorisations UI chronophages.

---

**Rapport généré le 05/08/2026 — Audit frontend EDUAI Learning**

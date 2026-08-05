# I18N Migration Plan — EDUAI Learning Frontend

> **Objectif** : Migrer les ~75 fichiers TSX restants vers `useTranslation()`/`t()` pour une couverture i18n complète (FR → EN → AR).
> **Règle** : Aucun string utilisateur ne reste en dur après ce plan.

---

## 1. État Actuel

| Métrique | Valeur |
|----------|--------|
| Fichiers TSX totaux | ~103 |
| Fichiers avec `useTranslation` | 12 (11.6%) |
| Fichiers **sans** `useTranslation` | ~75 (72.8%) |
| Fichiers non pertinents (App.tsx, ErrorBoundary, UI, tests) | ~16 |
| Clés `t()` existantes | ~137 |
| Clés dans `fr.json` | ~250 |
| Clés dans `en.json` | ~250 |
| Clés dans `ar.json` | ~250 |
| Strings hardcodées estimées à extraire | **~650+** |

### Fichiers déjà migrés (12)

| Dossier | Fichier |
|---------|---------|
| `features/student/pages/` | StudentDashboard, CourseCatalog, StudentPackPage, PacksPage, PlacementTestPage, OnboardingPage, ProfilePage, InboxPage, MonParcoursPage |
| `features/parent/pages/` | ParentDashboardPage |
| `components/` | LanguageSelector |
| (StudentWallet — vérifier) | — |

### Fichiers non pertinents (pas de strings UI)

- `App.tsx` (route config only)
- `components/ErrorBoundary.tsx` (error boundary only)
- `components/Skeleton.tsx` (no text)
- `components/ui/Button.tsx`, `Spinner.tsx`, `Modal.tsx`, `EmptyState.tsx`, `Input.tsx` (reçoivent children/txt via props)
- `components/TeacherStateGuard.tsx` (no text)
- `components/TierBadge.tsx` (reçoit props)
- `features/admin/components/course-editor/*`, `features/admin/components/content-creator/*`, `features/admin/components/settings/*` (sub-components reçoivent props)
- `features/learner/components/chat/*` (reçoivent props)
- `test/*.tsx` (tests only)

---

## 2. Convention de Clés

### Structure : `role.feature.element`

```
{role}.{feature}.{element}
```

| Segment | Exemples | Description |
|---------|----------|-------------|
| `role` | `admin`, `teacher`, `parent`, `student`, `learner`, `auth` | Rôle utilisateur ou zone |
| `feature` | `courses`, `users`, `schools`, `classroom`, `elements`, `parcours`, `wallet`, `pack`, `broadcast`, `finance`, `queue`, `gamification`, `tier`, `catalog`, `player` | Module fonctionnel |
| `element` | `title`, `subtitle`, `searchPlaceholder`, `emptyState`, `confirmDelete`, `btnCreate`, `toastSuccess`, `fieldLabel`, etc. | Élément d'interface |

### Sous-structurations fréquentes

```jsonc
{
  "admin.courses": {
    "title": "Gestion des Cours",
    "subtitle": "cours sur la plateforme",
    "searchPlaceholder": "Rechercher un cours...",
    "btnNew": "Nouveau Cours",
    "kpi": {
      "total": "Total",
      "published": "Publiés",
      "draft": "Brouillons",
      "inReview": "En revue",
      "archived": "Archivés"
    },
    "status": {
      "draft": "Brouillon",
      "published": "Publié",
      "archived": "Archivé",
      "pendingReview": "En revue",
      "rejected": "Rejeté",
      "approvedPlatform": "Approuvé (Plateforme)",
      "approvedB2b": "Approuvé (B2B)",
      "revisionRequested": "Révision demandée"
    },
    "level": {
      "beginner": "Débutant",
      "intermediate": "Intermédiaire",
      "advanced": "Avancé"
    },
    "filter": {
      "allStatus": "Tous les statuts",
      "allCategories": "Toutes catégories",
      "allLevels": "Tous niveaux",
      "allPedagogicalStatus": "Tous statuts pédago."
    },
    "empty": {
      "noResults": "Aucun cours trouvé",
      "noResultsDesc": "Aucun cours ne correspond à vos filtres.",
      "startCreate": "Commencez par créer votre premier cours."
    },
    "modal": {
      "confirmDelete": {
        "title": "Supprimer le cours",
        "message": "Supprimer \"{name}\" ? Cette action est irréversible.",
        "confirm": "Supprimer"
      },
      "preview": {
        "title": "Aperçu du cours",
        "chapters": "Chapitres",
        "lessons": "Leçons",
        "duration": "Durée",
        "prerequisites": "Prérequis",
        "objectives": "Objectifs pédagogiques",
        "program": "Programme du cours"
      },
      "create": {
        "title": "Créer un cours",
        "titleLabel": "Titre *",
        "titlePlaceholder": "Titre du cours",
        "descLabel": "Description courte",
        "descPlaceholder": "Résumé du cours en quelques lignes",
        "fullDescLabel": "Description complète",
        "categoryLabel": "Catégorie",
        "categoryPlaceholder": "Ex: Informatique",
        "levelLabel": "Niveau",
        "visibilityLabel": "Visibilité",
        "enrollmentLabel": "Inscription",
        "tagsLabel": "Tags (séparés par virgules)",
        "tagsPlaceholder": "python, débutant, programmation",
        "prereqLabel": "Prérequis",
        "prereqPlaceholder": "Connaissances requises",
        "objectivesLabel": "Objectifs pédagogiques",
        "objectivesPlaceholder": "Ce que les apprenants sauront faire",
        "btnCancel": "Annuler",
        "btnCreate": "Créer"
      }
    },
    "toast": {
      "published": "Cours publié avec succès",
      "unpublished": "Cours dépublié",
      "publishBlocked": "Publication bloquée: champs obligatoires manquants",
      "submittedReview": "Cours soumis pour review pédagogique",
      "archived": "Cours archivé",
      "duplicated": "Cours dupliqué avec succès",
      "deleted": "Cours supprimé",
      "created": "Cours créé avec succès"
    },
    "table": {
      "colTitle": "Cours",
      "colStatus": "Statut",
      "colContent": "Contenu",
      "colPedagogical": "Statut Pédago.",
      "colOwner": "Propriétaire",
      "colPrice": "Prix",
      "colActions": "Actions",
      "chaptersCount": "{count} chapitres",
      "lessonsCount": "{count} leçons",
      "free": "Gratuit",
      "currency": "TND"
    },
    "btn": {
      "edit": "Éditer",
      "preview": "Aperçu",
      "duplicate": "Dupliquer",
      "unpublish": "Dépublier",
      "publish": "Publier",
      "archive": "Archiver",
      "submitReview": "Soumettre pour review",
      "delete": "Supprimer"
    }
  }
}
```

---

## 3. Groupes de Migration (5 Lots)

### Lot 1 — Admin Pages (priorité haute, ~30 fichiers, ~330 strings)

| # | Fichier | Strings estimées | Difficulté |
|---|---------|-----------------|------------|
| 1 | `AdminCoursesPage.tsx` | ~65 | Élevée (label maps, modals, table, filtres, toast) |
| 2 | `AdminUsersPage.tsx` | ~60 | Élevée (4 modals, CSV, filtres, toasts) |
| 3 | `AdminDashboardPage.tsx` | ~35 | Moyenne (KPIs, chart labels) |
| 4 | `AdminSchoolsPage.tsx` | ~30 | Moyenne (table, modals, CSV) |
| 5 | `AdminTeacherQueuePage.tsx` | ~20 | Faible (table, 1 modal) |
| 6 | `BroadcastCenter.tsx` | ~20 | Faible (formulaire, historique) |
| 7 | `FinanceCenter.tsx` | ~20 | Faible (table, modal) |
| 8 | `CourseBuilderPage.tsx` | ~30 | Moyenne (constants, cards, modal) |
| 9 | `EnrollmentManager.tsx` | ~15 | Faible (table, filtres) |
| 10 | `AdminInviteCodesPage.tsx` | ~15 | Faible (table, KPIs) |
| 11 | `AdminArborescencePage.tsx` | ~10 | Faible |
| 12 | `AdminPublicationStatusPage.tsx` | ~10 | Faible |
| 13 | `AdminFinancePage.tsx` | ~10 | Faible |
| 14 | `AdminAnalyticsPage.tsx` | ~10 | Faible |
| 15 | `AdminAuditLogPage.tsx` | ~10 | Faible |
| 16 | `AdminSeuilsConfigPage.tsx` | ~10 | Faible |
| 17 | `AdminSpecialitesPedagogiquesPage.tsx` | ~10 | Faible |
| 18 | `AdminTokenPackagesPage.tsx` | ~10 | Faible |
| 19 | `AdminInboxView.tsx` | ~8 | Faible |
| 20 | `ContentModerationView.tsx` | ~8 | Faible |
| 21 | `PlatformOverview.tsx` | ~8 | Faible |
| 22 | `PlatformSettings.tsx` | ~8 | Faible |
| 23 | `SchoolOverview.tsx` | ~8 | Faible |
| 24 | `SchoolCourseDistribution.tsx` | ~8 | Faible |
| 25 | `CsvImportStudents.tsx` | ~8 | Faible |
| 26 | `PedagogicalAdminPage.tsx` | ~8 | Faible |
| 27 | `PedagogicalLeadPage.tsx` | ~8 | Faible |
| 28 | `UGCModeration.tsx` | ~8 | Faible |
| 29 | `SuperAdminCourseFactory.tsx` | ~8 | Faible |
| 30 | `FinancialHub.tsx` | ~8 | Faible |
| | **Total Lot 1** | **~380** | |

**Sous-lot 1A** (5 fichiers prioritaires — les plus gros) : AdminCoursesPage, AdminUsersPage, AdminDashboardPage, AdminSchoolsPage, CourseBuilderPage

### Lot 2 — Teacher Pages (~13 fichiers, ~120 strings)

| # | Fichier | Strings estimées | Difficulté |
|---|---------|-----------------|------------|
| 1 | `TeacherDashboard.tsx` | ~15 | Faible |
| 2 | `ClassroomManager.tsx` | ~18 | Faible (1 modal, listes) |
| 3 | `TeacherParcoursPage.tsx` | ~20 | Moyenne (CRUD, modal) |
| 4 | `TeacherElementsPage.tsx` | ~40 | Élevée (3 modals, filtres) |
| 5 | `TeacherAIStudio.tsx` | ~35 | Élevée (constants, formulaire, historique) |
| 6 | `TeacherBibliothequePage.tsx` | ~10 | Faible |
| 7 | `TeacherReorientationPage.tsx` | ~10 | Faible |
| 8 | `TeacherValidationContenuPage.tsx` | ~10 | Faible |
| 9 | `TeacherSalesPage.tsx` | ~10 | Faible |
| 10 | `TeacherAbonnementsPage.tsx` | ~10 | Faible |
| 11 | `TeacherWallet.tsx` | ~10 | Faible |
| 12 | `MyLearning.tsx` | ~10 | Faible |
| 13 | `AddStudentModal.tsx` | ~8 | Faible |
| | **Total Lot 2** | **~196** | |

### Lot 3 — Parent + Student Pages (~12 fichiers, ~170 strings)

| # | Fichier | Strings estimées | Difficulté |
|---|---------|-----------------|------------|
| 1 | `ParentFamillePage.tsx` | ~21 | Moyenne (discount info, listes) |
| 2 | `ParentWalletPage.tsx` | ~21 | Moyenne (pool labels, recharge) |
| 3 | `ParentPackPage.tsx` | ~20 | Moyenne (tier labels, quotas) |
| 4 | `ParentMessaging.tsx` | ~10 | Faible |
| 5 | `ChildDetailPage.tsx` | ~10 | Faible |
| 6 | `GamificationPage.tsx` | ~21 | Moyenne (badges, classements) |
| 7 | `StudentTierPage.tsx` | ~30 | Élevée (3 tiers, features, progression) |
| 8 | `PathwayCatalogPage.tsx` | ~18 | Moyenne (achat, badges) |
| 9 | `StudentAssimilationProfilePage.tsx` | ~10 | Faible |
| 10 | `CatalogPage.tsx` | ~19 | Moyenne (filtres, cards) |
| 11 | `CoursePlayerPage.tsx` | ~34 | Élevée (certificate, quiz, notes) |
| 12 | `SoftSkillsCatalogPage.tsx` | ~8 | Faible |
| | **Total Lot 3** | **~222** | |

### Lot 4 — Learner Pages + Auth Pages (~8 fichiers, ~60 strings)

| # | Fichier | Strings estimées | Difficulté |
|---|---------|-----------------|------------|
| 1 | `LearnerAIChatPage.tsx` | ~10 | Faible (déjà partiellement migré via sub-components) |
| 2 | `PlayerPage.tsx` | ~10 | Faible |
| 3 | `ConversationHistoryPage.tsx` | ~8 | Faible |
| 4 | `ConversationDetailPage.tsx` | ~8 | Faible |
| 5 | `LoginPage.tsx` | ~16 | Faible (branding, formulaire) |
| 6 | `RegisterPage.tsx` | ~15 | Faible |
| 7 | `ForgotPassword.tsx` | ~10 | Faible |
| 8 | `ResetPassword.tsx` | ~10 | Faible |
| | **Total Lot 4** | **~87** | |

### Lot 5 — Shared Components + Remaining (~10 fichiers, ~30 strings)

| # | Fichier | Strings estimées | Difficulté |
|---|---------|-----------------|------------|
| 1 | `DashboardLayout.tsx` | ~10 | Faible (sidebar labels) |
| 2 | `WalletWidget.tsx` | ~5 | Faible |
| 3 | `DailyObjective.tsx` | ~5 | Faible |
| 4 | `RecommendedPath.tsx` | ~5 | Faible |
| 5 | `AdminDashboardContainer.tsx` | ~5 | Faible |
| 6 | `AdminLayout.tsx` | ~5 | Faible |
| 7 | `SchoolAdminLayout.tsx` | ~5 | Faible |
| 8 | `SchoolAdminDashboard.tsx` | ~5 | Faible |
| 9 | `AdminDashboard.tsx` | ~5 | Faible |
| 10 | `CourseBuilder.tsx` | ~5 | Faible |
| | **Total Lot 5** | **~55** | |

---

## 4. Avant / Après — Exemple Complet (AdminCoursesPage)

### AVANT (hardcoded)

```tsx
// Status label maps (line 25-30)
const statusLabels: Record<string, string> = {
  draft: "Brouillon",
  pending_review: "En revue",
  rejected: "Rejeté",
  approved_for_platform: "Approuvé (Plateforme)",
  approved_for_b2b: "Approuvé (B2B)",
  revision_requested: "Révision demandée",
};

// Page title (line 289)
<h1 className="text-2xl font-bold text-navy-800">
  Courses <span className="text-gray-400 font-normal">Management</span>
</h1>
<p className="text-sm text-gray-500 mt-1">
  {courses.length} cours sur la plateforme
</p>

// Button (line 297)
<button className="...">
  + Nouveau Cours
</button>

// Toast (line 92)
toast.success("Cours publié avec succès");

// Confirm modal (line 387)
<ConfirmModal
  title="Supprimer le cours"
  message={`Supprimer "${courseToDelete.title}" ? Cette action est irréversible.`}
  confirmLabel="Supprimer"
/>

// Table header (line 178)
<th className="...">Cours</th>
```

### APRÈS (migré)

```tsx
import { useTranslation } from "react-i18next";

const { t } = useTranslation();

// Status labels — plus de map hardcoded, utiliser t() directement
// Supprimer le statusLabels constant, remplacer par:
<span>{t(`admin.courses.status.${status}`)}</span>

// Page title (line 289)
<h1 className="text-2xl font-bold text-navy-800">
  {t("admin.courses.title")} <span className="text-gray-400 font-normal">{t("admin.courses.titleSuffix")}</span>
</h1>
<p className="text-sm text-gray-500 mt-1">
  {t("admin.courses.subtitle", { count: courses.length })}
</p>

// Button (line 297)
<button className="...">
  + {t("admin.courses.btnNew")}
</button>

// Toast (line 92)
toast.success(t("admin.courses.toast.published"));

// Confirm modal (line 387)
<ConfirmModal
  title={t("admin.courses.modal.confirmDelete.title")}
  message={t("admin.courses.modal.confirmDelete.message", { name: courseToDelete.title })}
  confirmLabel={t("admin.courses.modal.confirmDelete.confirm")}
/>

// Table header (line 178)
<th className="...">{t("admin.courses.table.colTitle")}</th>
```

### CLÉS AJOUTÉES dans `fr.json`

```jsonc
{
  "admin": {
    "courses": {
      "title": "Cours",
      "titleSuffix": "Management",
      "subtitle": "{{count}} cours sur la plateforme",
      "btnNew": "Nouveau Cours",
      "status": {
        "draft": "Brouillon",
        "published": "Publié",
        "archived": "Archivé",
        "pendingReview": "En revue",
        "rejected": "Rejeté",
        "approvedPlatform": "Approuvé (Plateforme)",
        "approvedB2b": "Approuvé (B2B)",
        "revisionRequested": "Révision demandée"
      },
      "toast": {
        "published": "Cours publié avec succès",
        "unpublished": "Cours dépublié",
        "publishBlocked": "Publication bloquée: champs obligatoires manquants",
        "submittedReview": "Cours soumis pour review pédagogique",
        "archived": "Cours archivé",
        "duplicated": "Cours dupliqué avec succès",
        "deleted": "Cours supprimé",
        "created": "Cours créé avec succès"
      },
      "table": {
        "colTitle": "Cours",
        "colStatus": "Statut"
      },
      "modal": {
        "confirmDelete": {
          "title": "Supprimer le cours",
          "message": "Supprimer \"{{name}}\" ? Cette action est irréversible.",
          "confirm": "Supprimer"
        }
      }
    }
  }
}
```

### CLÉS AJOUTÉES dans `en.json`

```jsonc
{
  "admin": {
    "courses": {
      "title": "Courses",
      "titleSuffix": "Management",
      "subtitle": "{{count}} courses on the platform",
      "btnNew": "New Course",
      "status": {
        "draft": "Draft",
        "published": "Published",
        "archived": "Archived",
        "pendingReview": "In Review",
        "rejected": "Rejected",
        "approvedPlatform": "Approved (Platform)",
        "approvedB2b": "Approved (B2B)",
        "revisionRequested": "Revision Requested"
      },
      "toast": {
        "published": "Course published successfully",
        "unpublished": "Course unpublished",
        "publishBlocked": "Publish blocked: required fields missing",
        "submittedReview": "Course submitted for pedagogical review",
        "archived": "Course archived",
        "duplicated": "Course duplicated successfully",
        "deleted": "Course deleted",
        "created": "Course created successfully"
      },
      "table": {
        "colTitle": "Course",
        "colStatus": "Status"
      },
      "modal": {
        "confirmDelete": {
          "title": "Delete Course",
          "message": "Delete \"{{name}}\"? This action cannot be undone.",
          "confirm": "Delete"
        }
      }
    }
  }
}
```

---

## 5. Interpolation de Variables

### Syntaxe i18next

```jsonc
// fr.json
{
  "admin.users.modal.deleteConfirm": {
    "title": "Supprimer l'utilisateur",
    "message": "Êtes-vous sûr de vouloir supprimer {{name}} ? Cette action est irréversible.",
    "confirm": "Supprimer"
  }
}
```

```tsx
// TSX
<ConfirmModal
  title={t("admin.users.modal.deleteConfirm.title")}
  message={t("admin.users.modal.deleteConfirm.message", { name: user.name })}
  confirmLabel={t("admin.users.modal.deleteConfirm.confirm")}
/>
```

### Interpolation avec compteur (pluriels i18next)

```jsonc
// fr.json
{
  "admin.courses.subtitle": "{{count}} cours sur la plateforme",
  "admin.courses.table.chaptersCount": "{{count}} chapitres",
  "admin.courses.table.lessonsCount": "{{count}} leçons"
}
```

```tsx
// TSX
<p>{t("admin.courses.subtitle", { count: courses.length })}</p>
<span>{t("admin.courses.table.chaptersCount", { count: course.chapters })}</span>
```

### Config i18n (déjà en place)

```ts
// src/i18n/index.ts
interpolation: { escapeValue: false }  // React échappe déjà
```

---

## 6. Gestion des Pluriels

### Pattern i18next `_one` / `_other`

```jsonc
// fr.json
{
  "admin.users.kpi": {
    "total_one": "{{count}} utilisateur",
    "total_other": "{{count}} utilisateurs"
  },
  "admin.courses.table.chaptersCount_one": "{{count}} chapitre",
  "admin.courses.table.chaptersCount_other": "{{count}} chapitres",
  "admin.courses.table.lessonsCount_one": "{{count}} leçon",
  "admin.courses.table.lessonsCount_other": "{{count}} leçons"
}
```

```tsx
// TSX — i18next gère automatiquement le pluriel
<p>{t("admin.users.kpi.total", { count: users.length })}</p>
// → "1 utilisateur" ou "25 utilisateurs"
```

### Cas spécifiques FR/AR

```jsonc
// ar.json — l'arabe a 6 formes de pluriel ( zero, one, two, few, many, other )
{
  "admin.users.kpi": {
    "total_zero": "لا مستخدمين",
    "total_one": "مستخدم واحد",
    "total_two": "مستخدمان",
    "total_few": "{{count}} مستخدمين",
    "total_many": "{{count}} مستخدماً",
    "total_other": "{{count}} مستخدم"
  }
}
```

---

## 7. Stratégie d'Extraction des Strings

### Étape 1 — Scanner les strings hardcodées

```bash
# Identifier les strings dans le JSX/TSX (exclure les imports, types, hooks)
grep -rn "\"[A-ZÀ-Ü][a-zà-ü]" src/features/admin/pages/AdminCoursesPage.tsx
grep -rn "'[A-ZÀ-Ü][a-zà-ü]" src/features/admin/pages/AdminCoursesPage.tsx
```

### Étape 2 — Regrouper par contexte

Pour chaque fichier, regrouper les strings par:
- **Titres/labels de page** → `{role}.{feature}.title`, `.subtitle`
- **Boutons** → `{role}.{feature}.btn.{action}`
- **Table headers** → `{role}.{feature}.table.col{Name}`
- **Filtres** → `{role}.{feature}.filter.{name}`
- **Modals** → `{role}.{feature}.modal.{modalName}.{field}`
- **Toasts** → `{role}.{feature}.toast.{type}`
- **Empty states** → `{role}.{feature}.empty.{type}`
- **KPIs** → `{role}.{feature}.kpi.{name}`
- **Form labels** → `{role}.{feature}.form.{field}`

### Étape 3 — Ajouter les clés aux 3 locales

```bash
# Pour chaque clé ajoutée, ajouter dans fr.json, en.json, ar.json
# Utiliser la même structure hiérarchique
```

### Étape 4 — Remplacer dans le TSX

```tsx
// AVANT
<h1>Gestion des Cours</h1>

// APRÈS
const { t } = useTranslation();
<h1>{t("admin.courses.title")}</h1>
```

---

## 8. Règles de Migration

### Règle 1 : Ne jamais traduire les noms de variables/logique

```tsx
// ❌ FAUX
toast.success(t("admin.courses.toast." + type));

// ✅ BON
toast.success(t(`admin.courses.toast.${type}`));
// OU avec clé complète
toast.success(type === "published" ? t("admin.courses.toast.published") : t("admin.courses.toast.unpublished"));
```

### Règle 2 : Les status badges utilisent des clés préfixées

```tsx
// ❌ FAUX
const statusLabels: Record<string, string> = {
  draft: "Brouillon",
  published: "Publié",
};

// ✅ BON — supprimer le map, utiliser t() directement
<span>{t(`admin.courses.status.${status}`)}</span>
```

### Règle 3 : Les constantes de liste ne sont PAS traduites (marche arrière)

```tsx
// ❌ FAUX — ne pas traduire les values de select
const STATUS_OPTIONS = [
  { value: "draft", label: t("admin.courses.status.draft") },
  // ERROR: useTranslation n'est pas appelé au niveau module
];

// ✅ BON — garder les values en anglais, traduire le label au render
const STATUS_OPTIONS = ["draft", "published", "archived"];

// Dans le JSX:
<select>
  {STATUS_OPTIONS.map(s => (
    <option key={s} value={s}>{t(`admin.courses.status.${s}`)}</option>
  ))}
</select>
```

### Règle 4 : Interpolation pour les chaînes dynamiques

```tsx
// ❌ FAUX
<p>{courses.length} cours sur la plateforme</p>

// ✅ BON
<p>{t("admin.courses.subtitle", { count: courses.length })}</p>
```

### Règle 5 : Les toasts utilisent des clés imbriquées

```tsx
// ❌ FAUX
toast.success("Cours publié avec succès");

// ✅ BON
toast.success(t("admin.courses.toast.published"));
```

### Règle 6 : Les confirm dialogs utilisent `{{variable}}`

```tsx
// ❌ FAUX
message={`Supprimer "${name}" ? Cette action est irréversible.`}

// ✅ BON
message={t("admin.courses.modal.confirmDelete.message", { name })}
// fr.json: "message": "Supprimer \"{{name}}\" ? Cette action est irréversible."
// en.json: "message": "Delete \"{{name}}\"? This action cannot be undone."
```

### Règle 7 : Les label maps statiques → supprimer, utiliser t() dynamiquement

```tsx
// ❌ AVANT
const ownerTypeLabels: Record<string, string> = {
  school: "École",
  independent_teacher: "Enseignant indépendant",
  eduai_catalog: "Catalogue EDUAI",
};

// ✅ APRÈS — supprimer le map, traduire au render
<span>{t(`admin.courses.owner.${course.owner_type}`)}</span>
```

---

## 9. Estimation des Nouvelles Clés

| Lot | Clés nouvelles estimées | Taille par locale |
|-----|------------------------|-------------------|
| Lot 1 (Admin) | ~200 | ~200 × 3 langues = ~600 lignes |
| Lot 2 (Teacher) | ~100 | ~100 × 3 = ~300 lignes |
| Lot 3 (Parent+Student) | ~120 | ~120 × 3 = ~360 lignes |
| Lot 4 (Learner+Auth) | ~50 | ~50 × 3 = ~150 lignes |
| Lot 5 (Shared) | ~30 | ~30 × 3 = ~90 lignes |
| **Total** | **~500** | **~1500 lignes ajoutées** |

Taille finale estimée par locale : ~750 lignes (250 actuelles + 500 nouvelles)

---

## 10. Ordre d'Exécution Recommandé

```
Phase 1 — Lot 1A (5 fichiers critiques)
  → AdminCoursesPage, AdminUsersPage, AdminDashboardPage,
    AdminSchoolsPage, CourseBuilderPage
  → Validation : build passe, 0 erreurs TS

Phase 2 — Lot 1B (25 fichiers admin restants)
  → Tous les autres admin/pages/*
  → Validation : build passe

Phase 3 — Lot 2 (Teacher)
  → 13 fichiers teacher/pages/*
  → Validation : build passe

Phase 4 — Lot 3 (Parent+Student)
  → 12 fichiers parent + student + learner pages
  → Validation : build passe

Phase 5 — Lot 4 (Auth)
  → 4 fichiers auth/pages/*
  → Validation : build passe

Phase 6 — Lot 5 (Shared)
  → 10 fichiers components + layouts
  → Validation : build passe + test manuel RTL (ar)
```

---

## 11. Checklist de Validation par Lot

Pour chaque lot complété :

- [ ] `npm run build` — 0 erreurs TypeScript
- [ ] Toutes les clés ajoutées dans `fr.json` existent dans `en.json` et `ar.json`
- [ ] Aucune string utilisateur en dur dans les fichiers migrés (grep)
- [ ] `useTranslation` importé dans chaque fichier migré
- [ ] `t()` utilisé pour tous les textes UI visibles
- [ ] Les strings dynamiques utilisent `{{variable}}` interpolation
- [ ] Les pluriels utilisent `_one`/`_other` suffix
- [ ] Les toasts utilisent `t()` pas de string brute
- [ ] Les confirm dialogs utilisent `t()` avec interpolation
- [ ] Les status badges traduits dynamiquement (pas de label map hardcoded)
- [ ] Test RTL : switcher langue FR → EN → AR, vérifier absence de textes non traduits

---

## 12. Fichiers à Modifier par Lot

### Lot 1 — Admin (30 fichiers)

**Pages** (`src/features/admin/pages/`):
```
AdminCoursesPage.tsx
AdminUsersPage.tsx
AdminDashboardPage.tsx
AdminSchoolsPage.tsx
AdminTeacherQueuePage.tsx
BroadcastCenter.tsx
FinanceCenter.tsx
CourseBuilderPage.tsx
EnrollmentManager.tsx
AdminInviteCodesPage.tsx
AdminArborescencePage.tsx
AdminPublicationStatusPage.tsx
AdminFinancePage.tsx
AdminAnalyticsPage.tsx
AdminAuditLogPage.tsx
AdminSeuilsConfigPage.tsx
AdminSpecialitesPedagogiquesPage.tsx
AdminTokenPackagesPage.tsx
AdminInboxView.tsx
ContentModerationView.tsx
PlatformOverview.tsx
PlatformSettings.tsx
SchoolOverview.tsx
SchoolCourseDistribution.tsx
CsvImportStudents.tsx
PedagogicalAdminPage.tsx
PedagogicalLeadPage.tsx
UGCModeration.tsx
SuperAdminCourseFactory.tsx
FinancialHub.tsx
```

**Locales** : `fr.json`, `en.json`, `ar.json`

### Lot 2 — Teacher (13 fichiers)

**Pages** (`src/features/teacher/pages/`):
```
TeacherDashboard.tsx
ClassroomManager.tsx
TeacherParcoursPage.tsx
TeacherElementsPage.tsx
TeacherAIStudio.tsx
TeacherBibliothequePage.tsx
TeacherReorientationPage.tsx
TeacherValidationContenuPage.tsx
TeacherSalesPage.tsx
TeacherAbonnementsPage.tsx
TeacherWallet.tsx
MyLearning.tsx
AddStudentModal.tsx
```

### Lot 3 — Parent + Student (12 fichiers)

**Parent** (`src/features/parent/pages/`):
```
ParentFamillePage.tsx
ParentWalletPage.tsx
ParentPackPage.tsx
ParentMessaging.tsx
ChildDetailPage.tsx
```

**Student** (`src/features/student/pages/`):
```
GamificationPage.tsx
StudentTierPage.tsx
PathwayCatalogPage.tsx
StudentAssimilationProfilePage.tsx
```

**Learner** (`src/pages/learner/`):
```
CatalogPage.tsx
CoursePlayerPage.tsx
SoftSkillsCatalogPage.tsx
```

### Lot 4 — Auth (4 fichiers)

**Auth** (`src/features/auth/pages/`):
```
LoginPage.tsx
RegisterPage.tsx
ForgotPassword.tsx
ResetPassword.tsx
```

### Lot 5 — Shared (10 fichiers)

```
components/layout/DashboardLayout.tsx
components/WalletWidget.tsx
components/DailyObjective.tsx
components/RecommendedPath.tsx
features/admin/pages/AdminDashboardContainer.tsx
features/admin/pages/AdminLayout.tsx
features/admin/pages/SchoolAdminLayout.tsx
features/admin/pages/SchoolAdminDashboard.tsx
features/admin/pages/AdminDashboard.tsx
features/admin/pages/CourseBuilder.tsx
```

---

## 13. Risques et Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Clés manquantes en ar.json | Texte brut affiché en AR | Vérifier chaque lot avec grep `"français"` dans ar.json |
| Clés dupliquées | Conflit silencieux | Prefixed par rôle/feature, pas de collision |
| Strings dynamiques oubliées | Non traduit | Grep `"[A-ZÀ-Ü][a-zà-ü]"` dans chaque fichier après migration |
| Taille des JSON trop grande | Performance loading | i18next lazy loading disponible si >1000 clés |
| RTL cassé par nouvelle clé | Layout brisé | `applyDir()` gère déjà le RTL, test manuel requis |
| Toast non traduit | Erreur affichée en dur | Pattern : toujours `t("...toast.{type}")` |

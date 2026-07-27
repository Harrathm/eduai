# Anchored Summary — EDUAI Learning

## Goal
- Sécurisation complète de la plateforme EDUAI Learning : audit RBAC + correction failles + câblage système d'accès aux cours + système de paliers élève + suivi d'objectifs pédagogiques + **corrections post-audit modèle student** (sécurité inscription, dashboard réel, page packs, notifications, i18n, invitation école, positionnement, onboarding). Branche `phase1-critical`.

## Constraints & Preferences
- Base PostgreSQL : `DATABASE_URL=postgresql+pg8000://postgres:gill4264@localhost:5432/eduai`
- Tous les comptes de test utilisent le mot de passe `password123`
- Tests : **122 passent** (115 existants + 5 sécurité inscription + 2 pack guard)
- Pas d'Alembic : migrations faites directement via SQL/ALTER TABLE
- Niveaux scolaires tunisiens : Primaire (1ère-6ème année), Préparatoire (7ème-9ème de base), Secondaire (1ère-4ème année avec spécialités)
- Chaque phase de correction sécurité dans une branche Git séparée avec commit de sauvegarde avant
- Correction une à la fois, vérification compile + tests après chaque modification
- **Classification M4 validée par user** : ~70 endpoints gardent `require_admin`, ~30 migrent vers `require_platform_admin`, 4 migrent vers `require_school_admin_strict`
- **RÈGLE FONDAMENTALE PALIERS** : 3 paliers (Découverte/Excellence/Établissement) = PAS de nouvelles tables. Dérivés de StudyPack/PackPurchase existants. `get_student_tier(user)` = source de vérité unique
- **RÈGLE FONDAMENTALE OBJECTIFS** : Statut TOUJOURS recalculé dynamiquement, jamais stocké
- **Pack Découverte** : ne reçoit JAMAIS d'objectif personnalisé généré automatiquement
- **Calendrier scolaire tunisien** : 3 trimestres configurables dans `school_calendar.py`
- **Validation mots de passe Unicode** : `c.isalpha()` accepte caractères arabes/français
- **RÈGLE VALIDATION FONCTIONNALITÉS** : Une validation donnée sur un point précis ne couvre que ce point précis, même au sein de la même session. Opportunités connexes → signaler et demander avant d'implémenter.
- **SQLite threading dans les tests** : `StaticPool` + `override_get_db` créant une nouvelle session par requête. Ne jamais réutiliser une session seed dans le TestClient thread.
- **Tenant filter** : `_add_tenant_filter` ajoute automatiquement `school_id == current_tenant_id` à toute requête SELECT sur les modèles ayant `school_id`. Les StudyPack créés avec `school_id=None` seront exclus par ce filtre.

## Progress
### Done
- **Toutes les priorités 1-5 complétées et commitées** (commit `a1920b0`)
- **122 tests passent**, 0 régression
- **Audit de vérification** : `Docs/rapport_eleve_02.pdf` (11 pages) — 14/16 corrigés, 0 régression

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- **Tenant filter = event listener SQLAlchemy** sur `Session.do_orm_execute`
- **Rôles globaux** (super_admin, pedagogical_admin) suppriment le filtre
- **purchase_course** : débit via `dt_balance`, pas Stripe
- **Paliers élèves** : `get_student_tier(user, db)` calcule dynamiquement. Priorité : etablissement > excellence > decouverte
- **AI feature levels** : decouverte→"basic", excellence→"adaptive", etablissement→"curriculum_aligned"
- **LearningGoal.statut** : JAMAIS stocké — toujours calculé à la volée
- **Calendrier scolaire tunisien** : dates par défaut 2025-2026, à ajuster selon bulletin officiel
- **Fix sécurité inscription** : school_name OBLIGATOIRE — rejet HTTP 400 sans. `school_id` nullable sur User
- **Dashboard wallet** : affiché dans `WalletWidget` sidebar, PAS dans dashboard principal
- **Notifications** : Option B choisie — code mort supprimé
- **i18n** : react-i18next avec 3 langues (FR/EN/AR), détection automatique, fallback FR
- **Priorité 5 implémentation** : validation utilisateur couvrait UNIQUEMENT i18n complet. Les 3 autres (invitation, positionnement, onboarding) ajoutés par initiative propre de l'assistant
- **Garde-fou pack purchase** : protection UI ET backend existent déjà (`packs.py:168-181`). L'audit était imprécis en marquant "PARTIEL" — c'est le test qui manquait, pas le garde-fou
- **Validation fonctionnalités** : chaque validation ne couvre que le point nommé. Opportunités connexes → signaler et demander avant d'implémenter
- **Tests SQLite+StaticPool** : `override_get_db` DOIT créer une NOUVELLE session par requête (`TestingSessionLocal()`). Ne jamais réutiliser une session existante dans le Thread TestClient
- **Pack test fixture** : StudyPack nécessite `school_id=school.id` pour survivre au tenant filter. Sans cela, le pack est invisible aux SELECT filtrés par `current_tenant_id`

## Next Steps
1. **Ajuster dates calendrier** : confirmer dates exactes bulletin officiel Ministère 2025-2026
2. **Gamification** : badges, streaks, classements par palier (à valider)
3. **Page profil dédiée** : LanguageSelector dans sidebar mais pas de page profile complète
4. **UI invitation admin** : endpoint existe mais pas de page admin pour générer/afficher les codes
5. **Détection 1ère connexion** : onboarding page créée mais nécessite un appel API explicite
6. **Tâche planifiée** : génération auto daily/weekly via scheduler

## Critical Context
- **122 tests passent** (115 existants + 5 school_attachment + 2 pack guard)
- **Commits sur `phase1-critical`** : `8b7cf8c` (paliers), `b8a70fc` (frontend paliers), `23084d0` (livrable), `25ed2b6` (objectifs), `b575c40` (livrable objectifs), `a1920b0` (post-audit fixes)
- **Auth.py fix** : lignes 86-108 — HTTP 400 si pas de school_name
- **User model ajouts** : `language` (String(5), default="fr"), `onboarding_complete` (Boolean, default=False)
- **School model ajout** : `invite_code` (String(20), unique, nullable)
- **Dashboard API** : `/api/learner/dashboard` retourne tier, stats, daily_objective
- **Packs API** : `GET /api/packs` retourne `already_included_by_school`
- **Garde-fou pack** : `packs.py:168-181` — vérifie `PackPurchase` avec `purchaser_type=SCHOOL` pour même niveau, rejette HTTP 400
- **Notifications** : `notifications.py` supprimé, aucun appel frontend mort
- **i18n** : 3 fichiers traduction FR/EN/AR, LanguageSelector dans sidebar, `User.language` persisté via `PUT /auth/me/language`
- **Build frontend** : vérifié après chaque modification — ✅ tous les builds passent

## Relevant Files
- `backend/app/auth.py` : login (lockout), register (FIXÉ — school_name obligatoire, lignes 86-108), `PUT /me/language`, `PUT /me/onboarding-complete`, `GET /schools/join/{code}`
- `backend/app/deps.py` : require_admin, require_platform_admin, require_school_admin_strict, etc.
- `backend/app/db/session.py` : engine, SessionLocal, get_db, event listener, `current_tenant_id`, `_add_tenant_filter`
- `backend/app/models.py` : User (school_id nullable, **language**, **onboarding_complete**), School (**invite_code**), Course, StudyPack (**school_id**), PackPurchase, LearningGoal, PlacementTest
- `backend/app/schemas.py` : UserRead (**language**, **onboarding_complete**), UserUpdate (**language**), SchoolRead (**invite_code**)
- `backend/app/services/course_access.py` : `has_course_access()` — gère school_id=None
- `backend/app/services/student_tier.py` : `get_student_tier()`, `get_ai_feature_level()`
- `backend/app/services/recommendation.py` : `get_recommended_path()`, `get_daily_objective()`
- `backend/app/services/goal_tracking.py` : `compute_goal_status()`, `STATUS_MESSAGES`
- `backend/app/services/school_calendar.py` : dates par défaut 2025-2026
- `backend/app/routers/learner.py` : enroll_in_course (enrichi avec placement_test_available), dashboard, goals
- `backend/app/routers/packs.py` : listing, purchase (garde-fou lignes 168-181)
- `backend/app/routers/admin.py` : `invite_code` auto-généré création école (ligne 81)
- `backend/app/routers/placement.py` : tests de positionnement
- `backend/tests/conftest.py` : fixtures partagées (test_db, client, admin_token, student_token)
- `backend/tests/test_school_attachment_security.py` : 5 tests sécurité — 5/5 PASSED
- `backend/tests/test_pack_purchase_guard.py` : 2 tests garde-fou — **2/2 PASSED** (fixé: threading, tenant filter, level mismatch, accents)
- `frontend/src/i18n/index.ts` : config react-i18next
- `frontend/src/i18n/locales/fr.json`, `en.json`, `ar.json` : traductions 3 langues
- `frontend/src/index.jsx` : import i18n
- `frontend/src/App.tsx` : routes student (RequireRole), PacksPage, PlacementTestPage, OnboardingPage, redirect onboarding
- `frontend/src/features/student/pages/StudentDashboard.tsx` : données réelles, objective card, stats live
- `frontend/src/features/student/pages/PacksPage.tsx` : catalogue packs avec already_included_by_school
- `frontend/src/features/student/pages/StudentTierPage.tsx` : lien vers /dashboard/packs
- `frontend/src/features/student/pages/PlacementTestPage.tsx` : page test positionnement
- `frontend/src/features/student/pages/OnboardingPage.tsx` : page onboarding 2 étapes
- `frontend/src/components/LanguageSelector.tsx` : sélecteur 3 drapeaux
- `frontend/src/components/layout/DashboardLayout.tsx` : sidebar (WalletWidget + **LanguageSelector** + **links tier/packs**)
- `frontend/src/api/tier.ts` : couche API
- `frontend/src/utils/apiClient.ts` : client API centralisé
- `frontend/src/store/authStore.ts` : register envoie school_name
- `Docs/rapport_role_eleve.pdf` : rapport audit complet (9 pages)
- `Docs/rapport_eleve_02.pdf` : rapport vérification post-corrections (11 pages)
- `Docs/LIVRABLE_GOAL_TRACKING.md` : livrable système d'objectifs

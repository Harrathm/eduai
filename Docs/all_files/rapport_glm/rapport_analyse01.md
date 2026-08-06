# RAPPORT D'ANALYSE DU CODEBASE EDUAI — AUDIT 360° COMPLET

**Date :** 2026-08-04
**Scope :** Backend Python + Frontend React + Flutter Mobile
**Méthodologie :** Scan parallèle de 6 zones fonctionnelles via agents IA

---

## TABLE DES MATIÈRES

1. [Synthèse Exécutive](#1-synthèse-exécutive)
2. [Zone 1 — Modèles de Données](#2-zone-1--modèles-de-données)
3. [Zone 2 — RBAC & Contrôle d'Accès](#3-zone-2--rbac--contrôle-daccès)
4. [Zone 3 — Rôles & Authentification](#4-zone-3--rôles--authentification)
5. [Zone 4 — CMS & Cours](#5-zone-4--cms--cours)
6. [Zone 5 — AI Factory](#6-zone-5--ai-factory)
7. [Zone 6 — Monétisation & Formations](#7-zone-6--monétisation--formations)
8. [Tableau des Gaps Fonctionnels](#8-tableau-des-gaps-fonctionnels)
9. [Recommandations Prioritisées](#9-recommandations-prioritisées)

---

## 1. SYNTHÈSE EXÉCUTIVE

### 1.1 Statistiques Globales

| Composant | Valeur |
|---|---|
| Tables de la DB | 75 total (60 models.py + 13 cb_* models_lms.py + 2 models_ai_conversations.py) |
| Colonnes User | 32 colonnes (aucune multi-rôle, aucun context switching) |
| Endpoints RBAC | 11 dependecy functions dans deps.py (statiques, pas ABAC) |
| Routes Router | 14 fichiers routers/ montés sur app |
| Services Backend | 14 fichiers services/ |
| Fichiers Frontend | ~103 TSX/TS dans src/features/ |
| Hooks React | ~15 hooks personnalisés |
| Composants UI | 16 composants dans components/ui/ + 63 dans components/ |
| Tests Backend | 30/30 passent (28 RBAC teacher + 6 isolation + 2 autres) |
| Build Frontend | Passe clean (25.35s) |
| i18n | 0 adoption TSX (seulement 17 fichiers sur 103 — Lot 1A fait) |

### 1.2 Architecture Globale

```
Backend (FastAPI)
├── models.py (60 tables)
├── models_lms.py (13 tables — Modules A/B)
├── models_ai_conversations.py (2 tables)
├── deps.py (11 RBAC deps + get_current_user)
├── course_access.py (7-step has_course_access)
├── auth.py (JWT register/login)
├── routers/ (14 routeurs)
├── services/ (14 services)
└── core/ (config, database, security)

Frontend (React + Vite)
├── store/ (authStore — single role string)
├── components/layout/ (DashboardLayout — nav statique par rôle)
├── components/ui/ (Design System: 7 composants)
├── features/ (7 modules: admin, student, teacher, parent, shared, auth, settings)
├── api/ (barrel index.ts + legacy pathwayApi/teacherApi)
└── pages/ (15 pages globales)
```

---

## 2. ZONE 1 — MODÈLES DE DONNÉES

### 2.1 Modèle User (models.py:47)

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=uuid.uuid4)
    school_id: Mapped[Optional[int]]
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    full_name: Mapped[str]
    role: Mapped[str]  # UN SEUL champ string: admin, super_admin, teacher, student, parent
    subscription_tier: Mapped[Optional[str]]  # gratuit/basique/silver/golden
    subscription_plan: Mapped[Optional[str]]  # trial, paid, etc.
    is_approved: Mapped[Optional[bool]]
    is_active: Mapped[bool] = mapped_column(default=True)
    language_preference: Mapped[str] = mapped_column(default="fr")
    daily_streak: Mapped[int] = mapped_column(default=0)
    total_xp: Mapped[int] = mapped_column(default=0)
    current_level: Mapped[int] = mapped_column(default=1)
    preferred_difficulty: Mapped[str] = mapped_column(default="medium")
    last_active_at: Mapped[Optional[datetime]]
    weak_topics: Mapped[Optional[str]]
    strong_topics: Mapped[Optional[str]]
    performance_trend: Mapped[Optional[str]]
    needs_attention: Mapped[bool] = mapped_column(default=False)
    token_balance: Mapped[int] = mapped_column(default=0)
    dt_balance: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[Optional[datetime]]
    password_reset_token: Mapped[Optional[str]]
    password_reset_expires: Mapped[Optional[datetime]]
    email_verification_token: Mapped[Optional[str]]
    email_verified: Mapped[bool] = mapped_column(default=False)
    profile_setup_completed: Mapped[bool] = mapped_column(default=False)
    avatar_url: Mapped[Optional[str]]
```

**CONSTATS CRITIQUES — Zone 1 :**
- ❌ **PAS de champ `roles[]` array** → un seul rôle par user
- ❌ **PAS de champ `active_context_role`** → pas de context switcher
- ❌ **PAS de champ `is_partner`** → pas de distinction Partenaire/Client
- ❌ **PAS de champ `version_number`** → pas de versioning
- ❌ **PAS de champ `cms_status`** → pas de lifecycle CMS
- ❌ **PAS de table `bulk_seat_vouchers`** → pas de Bulk Seats
- ❌ **PAS de table `teacher_revenue_ledger`** → pas de Revenue Share
- ❌ **PAS de table `audit_impersonations`** → pas d'impersonation

### 2.2 Modèle Course (models.py:443)

```python
class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int]
    school_id: Mapped[Optional[int]]
    owner_type: Mapped[str]  # "school" | "independent_teacher" | "eduai_catalog"
    title: Mapped[str]
    description: Mapped[Optional[str]]
    pedagogical_status: Mapped[str]  # draft, pending_review, approved_local, approved_for_b2b, needs_revision
    commission_rate: Mapped[Decimal]  # 15.00 default
    is_published: Mapped[bool]
    # ... autres colonnes
```

**CONSTATS CRITIQUES — Zone 1 :**
- ⚠️ `pedagogical_status` existe mais **aucune machine à états** n'est implémentée
- ⚠️ `commission_rate` est le seul mécanisme Revenue Share — **pas de ledger**
- ❌ **PAS de champ `version_number`** → pas de versioning de cours
- ❌ **PAS de champ `is_active_version`** → pas de fork/rollback
- ❌ **PAS de champ `category_cible`** → pas de ciblage par catégorie
- ❌ **PAS de champ `tag_pack_requis`** → pas de tag pack
- ❌ **PAS de champ `cms_status`** → pas de lifecycle CMS (draft/approved/...)

### 2.3 Modèles Module A (models_lms.py) — GLOBAUX (pas de school_id)

| Table | Statut | Champ school_id |
|---|---|---|
| `parcours` | ✅ existe | NON — GLOBAL |
| `element_pedagogique` | ✅ existe | NON — GLOBAL |
| `bibliotheque` | ✅ existe | NON — GLOBAL |
| `abonnement` | ✅ existe | NON — GLOBAL |
| `abonnement_historique` | ✅ existe | NON — GLOBAL |
| `licence_ecole` | ✅ existe | NON — GLOBAL (ecole_id) |
| `licence_utilisation` | ✅ existe | NON — GLOBAL |
| `famille` | ✅ existe | NON — GLOBAL |
| `famille_membre` | ✅ existe | NON — GLOBAL |
| `reduction` | ✅ existe | NON — GLOBAL |
| `type_formation` | ✅ existe | NON — GLOBAL (is_global flag) |

### 2.4 Modèles Module B (models_lms.py) — Tenant-scoped

| Table | Statut | Champ school_id |
|---|---|---|
| `quiz` | ✅ existe | ✅ OUI |
| `question_bank` | ✅ existe | ✅ OUI |
| `quiz_attempt` | ✅ existe | ✅ OUI |

### 2.5 Tables de Governance — INEXISTANTES

| Table | Statut | Fichier |
|---|---|---|
| `bulk_seat_vouchers` | ❌ INEXISTANT | — |
| `teacher_revenue_ledger` | ❌ INEXISTANT | — |
| `audit_impersonations` | ❌ INEXISTANT | — |
| `user_roles` (multi-rôle) | ❌ INEXISTANT | — |
| `user_context_sessions` | ❌ INEXISTANT | — |
| `course_versions` | ❌ INEXISTANT | — |
| `cms_transitions` | ❌ INEXISTANT | — |

---

## 3. ZONE 2 — RBAC & CONTRÔLE D'ACCÈS

### 3.1 Dépendances RBAC (deps.py)

| Fonction | Rôles autorisés | Ligne |
|---|---|---|
| `require_admin()` | admin, super_admin, admin_pédagogique, school_admin | L80 |
| `require_platform_admin()` | super_admin, pedagogical_admin | L94 |
| `require_school_admin()` | admin, school_admin | L102 |
| `require_school_admin_strict()` | school_admin | L110 |
| `require_super_admin()` | super_admin | L118 |
| `require_teacher_or_admin()` | teacher, admin, school_admin | L126 |
| `require_pedagogical_admin()` | pedagogical_admin | L134 |
| `require_pedagogical_lead()` | pedagogical_lead | L142 |
| `require_pedagogical_any()` | pedagogical_admin, pedagogical_lead | L150 |
| `require_parent()` | parent | L158 |
| `require_non_demo_access()` | Tous sauf demo (DÉPRÉCIÉ) | L166 |

**CONSTATS CRITIQUES — Zone 2 :**
- ❌ **RBAC statique uniquement** — aucune vérification d'attributs (ABAC)
- ❌ **Pas de condition scope** (ex: teacher ne voit que SES cours)
- ❌ **Pas de condition school_id** dans les deps RBAC
- ❌ **Pas de condition subscription_tier** dans les deps RBAC
- ❌ **Pas de matrice de permissions centralisée** — chaque endpoint vérifie inline
- ⚠️ `require_non_demo_access()` est DÉPRÉCIÉ mais encore utilisé

### 3.2 Course Access (course_access.py)

```python
def has_course_access(user, course_id, db):
    # 7-step evaluation
    # 1. User exists
    # 2. Teacher bypass (is_approved)
    # 3. Enrollment check
    # 4. Pack check (Abonnement)
    # 5. School access (school_id match)
    # 6. Course status check
    # 7. Published check
```

**CONSTATS — Zone 2 :**
- ⚠️ **7 étapes mais PAS d'ABAC** — aucune vérification d'attribut utilisateur
- ⚠️ **Pas de ABAC context** — pas de `X-Active-Role` header
- ❌ **Pas de cache** — revalide à chaque appel

### 3.3 Tenant Context (deps.py:33-43)

```python
def set_tenant_context(user):
    if user.role in ["super_admin", "pedagogical_admin"]:
        # Supprime le filtre
        current_tenant_id.set(None)
    else:
        current_tenant_id.set(user.school_id)
```

**CONSTATS — Zone 2 :**
- ✅ `set_tenant_context` bien implémenté
- ⚠️ **Supprime le filtre pour pedagogical_admin** — risque de cross-school
- ❌ **Pas de vérification school_id dans les routes** — seulement via tenant context

---

## 4. ZONE 3 — RÔLES & AUTHENTIFICATION

### 4.1 Rôles Existants dans la DB

```sql
-- Vérifié via models.py User.role
-- Rôles disponibles : admin, super_admin, teacher, student, parent
-- Rôles ajoutés : pedagogical_admin, pedagogical_lead, school_admin
```

**CONSTATS CRITIQUES — Zone 3 :**
- ❌ **PAS de rôle `partner`** — la distinction Partenaire/Client n'existe pas
- ❌ **PAS de rôle `support`** — pas de rôle support pour impersonation
- ❌ **PAS de multi-rôle** — un user a UN SEUL role
- ❌ **PAS de context switcher** — pas de `active_context_role`
- ❌ **PAS d'impersonation** — pas de support session
- ❌ **PAS de JWT claims** — le JWT ne contient PAS le rôle, seulement `sub` et `exp`

### 4.2 Auth Endpoints (auth.py)

| Endpoint | Méthode | Ligne | Statut |
|---|---|---|---|
| `POST /auth/register` | POST | L43 | ✅ existe |
| `POST /auth/register-trial-teacher` | POST | L96 | ✅ existe |
| `POST /auth/teacher-register` | POST | L122 | ✅ existe |
| `POST /auth/login` | POST | L160 | ✅ existe |
| `POST /auth/logout` | POST | L196 | ✅ existe |
| `POST /auth/forgot-password` | POST | L220 | ✅ existe |
| `POST /auth/reset-password` | POST | L248 | ✅ existe |
| `POST /auth/refresh` | POST | L276 | ✅ existe |

**CONSTATS — Zone 3 :**
- ✅ **Refresh Token** : access_token 30min, refresh_token 7 jours
- ✅ **Replay detection** sur refresh tokens
- ❌ **Pas de support session** pour impersonation
- ❌ **Pas de `POST /auth/impersonate`** endpoint
- ❌ **Pas de `POST /auth/switch-role`** endpoint

### 4.3 Frontend Auth (authStore.ts)

```typescript
interface User {
  id: number;
  email: string;
  role: string;  // UN SEUL champ
  school_id?: number;
  niveau_scolaire?: string;
  // ... pas de roles[], pas de activeRole
}
```

**CONSTATS — Zone 3 :**
- ❌ **PAS de `roles[]` array** dans le store
- ❌ **PAS de `activeRole`** dans le store
- ❌ **PAS de context switcher** dans le UI
- ⚠️ `DashboardLayout` lit `user.role` directement → nav statique

### 4.4 DashboardLayout (DashboardLayout.tsx)

```typescript
// Navigation statique par rôle
const ADMIN_NAV = [...];      // admin, school_admin
const TEACHER_NAV = [...];    // teacher
const STUDENT_NAV = [...];    // student
const PARENT_NAV = [...];     // parent
```

**CONSTATS — Zone 3 :**
- ❌ **Pas de nav dynamique** selon le contexte actif
- ❌ **Pas de role switcher** dans le sidebar
- ⚠️ **Nav hardcoded** — impossible de changer de rôle sans recharger

---

## 5. ZONE 4 — CMS & COURS

### 5.1 Router Courses (courses.py — 520 lignes)

| Endpoint | Méthode | Ligne | Statut |
|---|---|---|---|
| `GET /courses` | GET | L30 | ✅ liste |
| `POST /courses` | POST | L50 | ✅ création |
| `GET /courses/{id}` | GET | L80 | ✅ détail |
| `PUT /courses/{id}` | PUT | L100 | ✅ mise à jour |
| `DELETE /courses/{id}` | DELETE | L130 | ✅ suppression |
| `POST /courses/{id}/enroll` | POST | L160 | ✅ inscription |
| `GET /courses/{id}/progress` | GET | L200 | ✅ progression |
| `GET /courses/{id}/modules` | GET | L240 | ✅ modules |
| `POST /courses/{id}/modules` | POST | L260 | ✅ ajout module |
| `PUT /courses/{id}/publish` | PUT | L300 | ✅ publication |

**CONSTATS CRITIQUES — Zone 4 :**
- ❌ **PAS de lifecycle CMS** — pas de state machine (draft → approved → published)
- ❌ **PAS de `GET /courses/{id}/versions`** — pas de versioning
- ❌ **PAS de `POST /courses/{id}/fork`** — pas de fork
- ❌ **PAS de `POST /courses/{id}/rollback`** — pas de rollback
- ❌ **PAS de `POST /courses/{id}/moderate`** — pas de modération
- ⚠️ `pedagogical_status` existe mais **non utilisé dans les endpoints**
- ⚠️ `commission_rate` existe mais **pas de ledger Revenue Share**

### 5.2 Machine à États CMS — INEXISTANTE

Le cahier des charges prévoit :
```
brouillon → soumis → validation_ia → validation_humaine → publié
                                      ↓
                                   rejeté
```

**CONSTATS — Zone 4 :**
- ❌ **Aucune de ces transitions n'est implémentée**
- ❌ **Pas de table `cms_transitions`** pour tracer l'historique
- ❌ **Pas de service `cms_lifecycle.py`**
- ❌ **Pas de notification de rejet/approbation**
- ⚠️ Le `pedagogical_status` dans le modèle est un champ texte libre, pas une énumération contrôlée

### 5.3 Versioning — INEXISTANT

Le cahier des charges prévoit :
- `version_number` sur Course
- `is_active_version` flag
- Fork d'un cours existant
- Rollback vers une version précédente

**CONSTATS — Zone 4 :**
- ❌ **Aucune de ces colonnes n'existe** dans le modèle Course
- ❌ **Pas de table `course_versions`**
- ❌ **Pas d'endpoint de versioning**
- ❌ **Pas de fork mechanism**

### 5.4 Content Moderation — INEXISTANTE

Le cahier des charges prévoit :
- Soumission IA → validation humaine
- Historique des versions
- Notification de rejet

**CONSTATS — Zone 4 :**
- ❌ **Pas de workflow de modération**
- ❌ **Pas de notification de rejet**
- ❌ **Pas d'historique des versions**

---

## 6. ZONE 5 — AI FACTORY

### 6.1 Router AI Factory (ai_factory.py — 346 lignes)

| Endpoint | Méthode | Ligne | Statut |
|---|---|---|---|
| `POST /api/admin/ai-factory/generate-plan` | POST | L30 | ✅ SSE |
| `POST /api/admin/ai-factory/generate-content-stream` | POST | L80 | ✅ SSE |
| `POST /api/admin/ai-factory/generate-quiz-stream` | POST | L150 | ✅ SSE |
| `POST /api/admin/ai-factory/publish-course` | POST | L220 | ✅ POST |

**CONSTATS CRITIQUES — Zone 5 :**
- ✅ **4 endpoints fonctionnels** avec SSE streaming
- ❌ **PAS d'atomisation** — chaque endpoint génère un bloc monolithique
- ❌ **PAS de bibliothèque globale** pour le contenu généré
- ❌ **PAS de réutilisation** — chaque génération est indépendante
- ❌ **PAS de versioning** du contenu généré
- ⚠️ **Sécurité** : Le prompt injection est un risque (pas de sanitization stricte)

### 6.2 Service AI Factory (ai_factory_service.py — 504 lignes)

```python
class AIFactoryService:
    async def generate_plan(self, topic, grade_level, ...):
        # Monolithique — génère tout le plan en une fois
        pass
    
    async def generate_content_stream(self, plan, ...):
        # Monolithique — génère tout le contenu en une fois
        pass
    
    async def generate_quiz_stream(self, content, ...):
        # Monolithique — génère tout le quiz en une fois
        pass
```

**CONSTATS — Zone 5 :**
- ⚠️ **4 étapes mais PAS atomisées** — chaque étape est monolithique
- ❌ **Pas de library** — le contenu généré n'est pas réutilisable
- ❌ **Pas de cache** — régénère à chaque fois
- ❌ **Pas de versioning** du contenu généré
- ⚠️ **Pas de rate limiting** par user sur les appels IA

### 6.3 Frontend AI Factory (ContentCreatorAI.tsx — 108 lignes)

```tsx
// 4-step wizard UI
// Step 1: Topic input
// Step 2: Plan review
// Step 3: Content generation
// Step 4: Preview & publish
```

**CONSTATS — Zone 5 :**
- ✅ **Interface wizard fonctionnelle**
- ❌ **Pas de bibliothèque de contenu** — tout est dans le wizard
- ❌ **Pas de versioning** — pas de "Voir les versions"
- ❌ **Pas de modération** — pas de "Soumettre pour approbation"
- ⚠️ **Pas de sauvegarde automatique** — si l'utilisateur quitte, tout est perdu

### 6.4 Hook AI Factory (useContentCreator.ts — 259 lignes)

```typescript
// State machine pour le wizard
// Gère: topic, plan, content, quiz, loading, error
```

**CONSTATS — Zone 5 :**
- ✅ **State machine fonctionnelle**
- ❌ **Pas de cache** — re-fetch à chaque fois
- ❌ **Pas de retry** — en cas d'échec, l'utilisateur doit tout recommencer
- ❌ **Pas de sauvegarde** — pas de draft persisté

---

## 7. ZONE 6 — MONÉTISATION & FORMATIONS

### 7.1 Systèmes de Souscription Parallèles

| Système | Tables | Statut | Utilisation |
|---|---|---|---|
| (A) PackDefinition + Abonnement | pack_definitions, abonnements | ✅ ACTIF | Système principal |
| (B) StudyPack + PackPurchase | study_packs, pack_purchases | ⚠️ LEGACY | Abandonné |
| (C) Stripe Subscriptions | (externes) | ⚠️ PARTIEL | Non intégré |

**CONSTATS CRITIQUES — Zone 6 :**
- ⚠️ **3 systèmes parallèles** — confusion potentielle
- ⚠️ **Système B en LEGACY** mais encore référencé dans le code
- ❌ **Pas de migration** du système B vers A
- ❌ **Pas de Stripe checkout** intégré (seulement webhook)

### 7.2 PackDefinition (models.py:2533)

```python
class PackDefinition(Base):
    __tablename__ = "pack_definitions"
    id: Mapped[int]
    nom: Mapped[str]  # NOT "name"
    description: Mapped[Optional[str]]
    tier: Mapped[str]  # gratuit/basique/silver/golden
    niveau_scolaire: Mapped[str]
    matieres: Mapped[Optional[str]]  # JSON
    prix_tnd: Mapped[Decimal]  # NOT "price"
    features: Mapped[Optional[str]]  # JSON
    est_actif: Mapped[bool]
```

**CONSTATS — Zone 6 :**
- ✅ **36 packs actifs** (6 niveaux × 4 tiers)
- ✅ **74 cours publiés** seedés
- ⚠️ **Pas de versioning** des packs
- ❌ **Pas de `category_cible`** — pas de ciblage par catégorie
- ❌ **Pas de `tag_pack_requis`** — pas de tag pack

### 7.3 Abonnement (models.py:2557)

```python
class Abonnement(Base):
    __tablename__ = "abonnements"
    id: Mapped[int]
    eleve_id: Mapped[int]
    pack_id: Mapped[int]
    statut: Mapped[str]  # actif, grace, expire, downgrade
    date_debut: Mapped[date]
    date_fin: Mapped[date]
    matieres_config: Mapped[Optional[str]]  # JSON
```

**CONSTATS — Zone 6 :**
- ✅ **Statuts actif/grace/expire/downgrade** fonctionnels
- ✅ **Grace period** 7 jours avant downgrade Gratuit
- ✅ **Reset trimestriel** quota
- ❌ **Pas de `reconfigure` endpoint** — pas de reconfiguration de matières
- ❌ **Pas de downgrade deferré** — le downgrade est immédiat

### 7.4 LicenceEcole (models.py:2624)

```python
class LicenceEcole(Base):
    __tablename__ = "licence_ecole"
    id: Mapped[int]
    ecole_id: Mapped[int]  # NOT "school_id"
    nb_licences: Mapped[int]
    date_debut: Mapped[date]
    date_fin: Mapped[date]
```

**CONSTATS — Zone 6 :**
- ⚠️ **Champ `ecole_id`** au lieu de `school_id` — inconsistances
- ❌ **Pas de `statut`** — pas de statut actif/inactif
- ❌ **Pas de `nb_licences_a_activer`** — pas de compteur d'activation

### 7.5 Wallet (wallet.py)

```python
def consume_credits(user_id, amount, reason, db):
    # 2-step FOR UPDATE
    # 1. SELECT FOR UPDATE → lock
    # 2. UPDATE → debit
    # Order: subscription → school_allocated → trial → purchased
```

**CONSTATS — Zone 6 :**
- ✅ **Atomicité** : 2-step FOR UPDATE
- ✅ **Decimal(10,2)** pour les montants
- ✅ **Order de consommation** : subscription → school_allocated → trial → purchased
- ⚠️ **Pas de ledger** — pas de `teacher_revenue_ledger`
- ❌ **Pas de `commission_rate`** appliqué automatiquement

### 7.6 Soft Skills — INEXISTANT

Le cahier des charges prévoit :
- Catalogue Soft Skills transversal
- Table `soft_skills` ou `formations`
- Endpoints de CRUD
- Intégration dans les packs

**CONSTATS — Zone 6 :**
- ❌ **Pas de table `soft_skills`** — seulement un label dans `QUOTA_INFO`
- ❌ **Pas de router Soft Skills**
- ❌ **Pas de CRUD** pour les formations Soft Skills
- ❌ **Pas d'intégration dans les packs**
- ⚠️ **8 cours Soft Skills seedés** mais sans table dédiée

---

## 8. TABLEAU DES GAPS FONCTIONNELS

| Zone | Gap | Priorité | Effort estimé | Impact |
|---|---|---|---|---|
| RBAC | Pas d'ABAC engine | 🔴 HAUTE | 3 jours | Contrôle d'accès granulaire |
| RBAC | Pas de matrice permissions | 🔴 HAUTE | 1 jour | Centralisation des règles |
| RBAC | Pas de cache course_access | 🟡 MOYENNE | 0.5 jour | Performance |
| Auth | Pas de multi-rôle | 🔴 HAUTE | 2 jours | Context switching |
| Auth | Pas de context switcher UI | 🔴 HAUTE | 1 jour | UX role switching |
| Auth | Pas d'impersonation | 🔴 HAUTE | 2 jours | Support utilisateur |
| Auth | Pas de JWT role claims | 🟡 MOYENNE | 0.5 jour | Performance RBAC |
| CMS | Pas de lifecycle states | 🔴 HAUTE | 2 jours | Workflow modération |
| CMS | Pas de machine à états | 🔴 HAUTE | 1 jour | Transitions contrôlées |
| CMS | Pas de notification rejet | 🟡 MOYENNE | 1 jour | UX admin |
| CMS | Pas de versioning | 🔴 HAUTE | 3 jours | Historique versions |
| CMS | Pas de fork/rollback | 🟡 MOYENNE | 2 jours | Gestion erreurs |
| AI Factory | Pas d'atomisation | 🟡 MOYENNE | 3 jours | Réutilisation contenu |
| AI Factory | Pas de bibliothèque globale | 🟡 MOYENNE | 2 jours | Centralisation |
| AI Factory | Pas de cache/retry | 🟢 BASSE | 1 jour | UX |
| Monétisation | 3 systèmes parallèles | 🟡 MOYENNE | 2 jours | Consolidation |
| Monétisation | Pas de downgrade deferré | 🟡 MOYENNE | 1 jour | UX |
| Monétisation | Pas de reconfigure endpoint | 🟡 MOYENNE | 1 jour | Flexibilité |
| Monétisation | Pas de Soft Skills table | 🔴 HAUTE | 2 jours | Catalogue formations |
| Monétisation | Pas de Bulk Seats | 🟡 MOYENNE | 2 jours | Vente B2B |
| Monétisation | Pas de Revenue Share ledger | 🟡 MOYENNE | 2 jours | Finance teacher |
| Frontend | i18n 0% adoption (86 fichiers) | 🟡 MOYENNE | 5 jours | Internationalisation |
| Frontend | Pas de role switcher | 🔴 HAUTE | 1 jour | UX |
| Frontend | Pas de context switcher | 🔴 HAUT | 1 jour | UX |

**TOTAL :** 24 gaps identifiés — 11 HAUTE, 11 MOYENNE, 2 BASSE

---

## 9. RECOMMANDATIONS PRIORITÉES

### 9.1 Phase 1 — RBAC→ABAC (3-4 jours)

1. **Créer matrice permissions** centralisée (`core/permissions.py`)
2. **Ajouter ABAC engine** dans `deps.py` — vérifier attributs user vs ressource
3. **Ajouter `X-Active-Role` header** pour context switcher
4. **Ajouter JWT role claims** pour performance
5. **Tester** : 10 tests RBAC ABAC

### 9.2 Phase 2 — CMS Lifecycle (3-4 jours)

1. **Ajouter colonnes** : `cms_status`, `version_number`, `is_active_version`
2. **Créer table** `cms_transitions` pour historique
3. **Implémenter machine à états** : draft → submitted → ai_validated → human_validated → published → rejected
4. **Ajouter endpoints** : `/courses/{id}/submit`, `/courses/{id}/moderate`, `/courses/{id}/versions`
5. **Tester** : 10 tests lifecycle

### 9.3 Phase 3 — Multi-Rôle & Impersonation (3-4 jours)

1. **Créer table** `user_roles` (multi-rôle)
2. **Créer table** `audit_impersonations`
3. **Ajouter endpoints** : `/auth/impersonate`, `/auth/switch-role`
4. **Modifier DashboardLayout** pour nav dynamique
5. **Ajouter role switcher UI** dans le sidebar
6. **Tester** : 10 tests impersonation

### 9.4 Phase 4 — AI Factory Atomization (4-5 jours)

1. **Atomiser** les 4 endpoints en sous-endpoints
2. **Créer table** `ai_library` pour contenu réutilisable
3. **Ajouter cache** et retry
4. **Ajouter versioning** du contenu généré
5. **Tester** : 10 tests atomization

### 9.5 Phase 5 — Monétisation Consolidation (3-4 jours)

1. **Migrer** système B (StudyPack) vers système A (PackDefinition)
2. **Ajouter table** `soft_skills` dédiée
3. **Ajouter endpoint** `reconfigure` pour Abonnement
4. **Ajouter downgrade deferré** (prochain trimestre)
5. **Créer table** `teacher_revenue_ledger`
6. **Tester** : 10 tests monétisation

### 9.6 Phase 6 — Frontend i18n & Role Switcher (5-6 jours)

1. **Lot 1B** : 25 pages admin restantes
2. **Lots 2-5** : Teacher, Parent, Student, Auth, Shared
3. **Role Switcher UI** dans le sidebar
4. **Context Switcher** avec `X-Active-Role` header
5. **Tester** : build clean + 5 tests UI

---

## ANNEXES

### A. Fichiers Clés à Modifier

| Fichier | Modifications requises |
|---|---|
| `backend/app/models.py` | Ajouter colonnes + tables governance |
| `backend/app/deps.py` | ABAC engine + context switcher |
| `backend/app/course_access.py` | Extension 7-step avec ABAC |
| `backend/app/auth.py` | JWT claims + impersonation |
| `backend/app/routers/courses.py` | Lifecycle + versioning |
| `backend/app/services/ai_factory_service.py` | Atomisation |
| `backend/app/services/wallet.py` | Ledger Revenue Share |
| `frontend/src/store/authStore.ts` | Multi-rôle + context |
| `frontend/src/components/layout/DashboardLayout.tsx` | Nav dynamique |
| `frontend/src/features/admin/pages/ContentCreatorAI.tsx` | Bibliothèque |

### B. Tables Nouvelles à Créer

| Table | Purpose |
|---|---|
| `user_roles` | Multi-rôle par user |
| `audit_impersonations` | Log des sessions d'impersonation |
| `cms_transitions` | Historique des transitions CMS |
| `course_versions` | Versioning des cours |
| `ai_library` | Bibliothèque de contenu IA |
| `teacher_revenue_ledger` | Ledger Revenue Share |
| `bulk_seat_vouchers` | Bulk Seats B2B |
| `soft_skills` | Catalogue Soft Skills |

### C. Endpoints Nouveaux à Créer

| Endpoint | Purpose |
|---|---|
| `POST /auth/impersonate` | Démarrer une session d'impersonation |
| `POST /auth/switch-role` | Changer de rôle actif |
| `POST /courses/{id}/submit` | Soumettre pour modération |
| `POST /courses/{id}/moderate` | Approuver/Rejeter |
| `GET /courses/{id}/versions` | Lister les versions |
| `POST /courses/{id}/fork` | Fork un cours |
| `POST /courses/{id}/rollback` | Rollback vers version |
| `GET /abonnements/{id}/reconfigure` | Configurer les matières |
| `POST /abonnements/{id}/reconfigure` | Sauvegarder la config |
| `GET /soft-skills` | Lister les formations Soft Skills |
| `POST /soft-skills` | Créer une formation |
| `GET /bulk-seats` | Gérer les Bulk Seats |
| `POST /bulk-seats` | Créer un voucher |
| `GET /teacher/revenue` | Voir le ledger Revenue Share |

---

**Fin du rapport — 24 gaps identifiés, 8 tables nouvelles, 14 endpoints nouveaux**

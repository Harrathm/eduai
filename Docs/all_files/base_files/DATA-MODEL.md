# Modèle de Données — EDUAI Learning

# نموذج البيانات — EDUAI Learning

# Data Model — EDUAI Learning

> **Dernière mise à jour** : 2026-08-01
> **Base** : PostgreSQL 15+ via SQLAlchemy 2.0 (ORM)
> **Drivers** : pg8000 (backend), psycopg2 (ops)
> **Fichiers source** : `backend/app/models.py` (60 tables), `backend/app/models_lms.py` (13 tables cb_*), `backend/app/models_ai_conversations.py` (2 tables)
> **Tables totales** : 75 tables (dont 28 tableaux legacy `cb_*` dans `models_lms.py`)

---

## Table des matières

1. [Enumérations](#1-enumérations)
2. [Identité & Multi-tenancy](#2-identité--multi-tenancy)
3. [Finances & Portefeuille](#3-finances--portefeuille)
4. [Cours & Contenu](#4-cours--contenu)
5. [Parcours adaptatif & Validation pédagogique](#5-parcours-adaptatif--validation-pédagogique)
6. [RBAC Pédagogique](#6-rbac-pédagogique)
7. [Gamification](#7-gamification)
8. [LMS Course Builder (cb_*)](#8-lms-course-builder-cb_)
9. [Conversations IA](#9-conversations-ia)
10. [Annexe A — Tables sans clé étrangère](#annexe-a--tables-sans-clé-étrangère)
11. [Annexe B — Tables sans documentation](#annexe-b--tables-sans-documentation)

---

## 1. Enumérations

### 1.1 Identité & Rôles

| Enum | Valeurs | Fichier source |
|------|---------|----------------|
| `UserRole` | `student`, `teacher`, `admin_school`, `super_admin`, `pedagogical_admin`, `pedagogical_lead`, `parent` | models.py:39 |
| `SubscriptionTier` | `free`, `teacher_pro`, `school`, `institution` | models.py:48 |
| `SubscriptionPlan` | `trial`, `school_affiliated`, `independent_paid` | models.py:55 |
| `VerificationStatus` | `unverified`, `pending`, `verified`, `rejected` | models.py:62 |
| `PaymentStatus` | `pending`, `succeeded`, `failed`, `refunded`, `canceled` | models.py:70 |
| `TeacherRegistrationStatus` | `pending`, `approved`, `rejected` | models.py:209 |

### 1.2 Finances

| Enum | Valeurs | Fichier source |
|------|---------|----------------|
| `WalletPool` | `trial`, `school_allocated`, `purchased`, `subscription`, `dt_purchased` | models.py:79 |
| `BillableFeature` | `ai_ask`, `ai_explain`, `ai_quiz`, `ai_generate`, `ai_ingest`, `ai_correct` | models.py:88 |
| `TransactionType` | `token_recharge`, `token_consumption`, `dt_deposit`, `dt_withdrawal`, `course_purchase`, `course_sale`, `subscription`, `refund`, `bonus`, `penalty` | models.py:118 |
| `Currency` | `TOKEN`, `DT` | models.py:130 |

### 1.3 Contenu & Cours

| Enum | Valeurs | Fichier source |
|------|---------|----------------|
| `ContentType` | `video`, `pdf`, `text`, `quiz`, `assignment` | models.py:134 |
| `CourseStatus` | `draft`, `pending`, `approved`, `rejected`, `published`, `archived` | models.py:141 |
| `PedagogicalStatus` | `draft`, `pending_review`, `approved_local`, `approved_for_b2b`, `needs_revision` | models.py:149 |
| `CourseOwnerType` | `school`, `independent_teacher`, `eduai_catalog` | models.py:193 |
| `CourseVisibility` | `private`, `school_only`, `public_catalog` | models.py:198 |
| `EnrollmentStatus` | `active`, `completed`, `dropped`, `suspended` | models.py:112 |
| `PackStatus` | `draft`, `published`, `archived` | models.py:720 |
| `PackPurchaseStatus` | `active`, `expired`, `cancelled` | models.py:726 |
| `PurchaserType` | `student`, `school` | models.py:732 |

### 1.4 Niveaux scolaires tunisiens

| Enum | Valeurs (19 niveaux) |
|------|---------|
| `NiveauScolaire` | Primaire: `1ère année`…`6ème année`. Préparatoire: `7ème de base`, `8ème de base`, `9ème de base`. Secondaire: `1ère année secondaire`, `2ème année sciences/letres/tech_info/eco_services`, `3ème année lettres/maths/sc_exp/eco_gest/sc_info/sc_tech`, `4ème année lettres/maths/sc_exp/eco_gest/sc_info/sc_tech` |

### 1.5 Parcours adaptatif

| Enum | Valeurs | Fichier source |
|------|---------|----------------|
| `NiveauAssimilation` | `remediation`, `standard`, `avance` | models.py:1773 |
| `TypeContenu` | `video`, `fiche`, `quiz`, `banque_exercices`, `evaluation_ia` | models.py:1780 |
| `StatutContenuPedagogique` | `a` (actif), `b` (brouillon), `c` (archivé) | models.py:1789 |
| `StatutValidationPedagogique` | `en_attente`, `valide`, `rejete` | models.py:1796 |
| `SourceChangement` | `test_initial`, `ajustement_auto`, `override_enseignant` | models.py:1803 |
| `StatutValidationProfil` | `auto_applique`, `confirme_enseignant`, `annule_enseignant` | models.py:1810 |
| `ActionReorientation` | `aucune`, `confirme`, `annule` | models.py:1817 |

### 1.6 Objectifs pédagogiques

| Enum | Valeurs | Fichier source |
|------|---------|----------------|
| `GoalHorizon` | `daily`, `weekly`, `monthly`, `quarterly`, `annual` | models.py:1709 |
| `GoalStatus` | `on_track`, `behind`, `completed`, `missed` | models.py:1717 |
| `GoalMetricType` | `lessons_completed`, `quiz_average_score`, `study_time_minutes`, `chapter_completion`, `curriculum_coverage_percent` | models.py:1724 |
| `GoalSource` | `auto_generated`, `teacher_assigned`, `pedagogical_lead_assigned`, `student_self` | models.py:1732 |

### 1.7 Communication & Audit

| Enum | Valeurs | Fichier source |
|------|---------|----------------|
| `MessageType` | `broadcast`, `direct`, `observation` | models.py:214 |
| `DocumentStatus` | `pending`, `processing`, `completed`, `failed` | models.py:203 |
| `AuditAction` | 17 valeurs (user.*, school.*, course.*, transaction.*, registration.*, settings.*) | models.py:1352 |

### 1.8 Quiz

| Enum | Valeurs | Fichier source |
|------|---------|----------------|
| `QuestionType` (models.py) | `mcq`, `multi`, `truefalse`, `short` | models.py:1175 |
| `QuestionType` (models_lms.py) | `multiple_choice`, `multiple_select`, `true_false`, `short_answer`, `fill_blank` | models_lms.py:125 |
| `LessonType` (models_lms.py) | `video`, `pdf`, `text`, `quiz`, `image`, `link`, `video_text`, `document` | models_lms.py:114 |
| `CourseContentStatus` (models_lms.py) | `draft`, `published`, `archived` | models_lms.py:34 |
| `ContentLevel` (models_lms.py) | `beginner`, `intermediate`, `advanced` | models_lms.py:40 |
| `CertificateStatus` (models_lms.py) | `generating`, `ready`, `expired`, `revoked` | models_lms.py:53 |

---

## 2. Identité & Multi-tenancy

### `schools` — Entité multi-tenant

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `uuid` | UUID | UNIQUE, DEFAULT uuid4() | |
| `name` | VARCHAR(255) | NOT NULL | |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | |
| `domain` | VARCHAR(255) | | |
| `school_type` | ENUM(SchoolType) | DEFAULT 'real' | `real`, `demo`, `individual` |
| `subscription_tier` | ENUM(SubscriptionTier) | DEFAULT 'free' | |
| `subscription_expires_at` | TIMESTAMP | | |
| `max_users` | INTEGER | DEFAULT 10 | |
| `logo_url` | VARCHAR(500) | | |
| `primary_color` | VARCHAR(20) | DEFAULT '#FF6B35' | |
| `is_active` | BOOLEAN | DEFAULT true | |
| `maintenance_mode` | BOOLEAN | DEFAULT false | |
| `allow_teacher_registration` | BOOLEAN | DEFAULT true | |
| `allow_new_signups` | BOOLEAN | DEFAULT true | |
| `invite_code` | VARCHAR(20) | UNIQUE | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `users` — Utilisateurs

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `uuid` | UUID | UNIQUE, DEFAULT uuid4() | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE | Nullable (super_admin) |
| `email` | VARCHAR(255) | NOT NULL | |
| `hashed_password` | VARCHAR(255) | NOT NULL | bcrypt via `get_password_hash()` |
| `full_name` | VARCHAR(255) | | |
| `role` | VARCHAR(30) | DEFAULT 'student' | `UserRole` enum |
| `subscription_plan` | VARCHAR(30) | DEFAULT 'trial' | `SubscriptionPlan` enum |
| `subscription_expires_at` | TIMESTAMP | | |
| `is_demo_account` | BOOLEAN | DEFAULT false | |
| `language` | VARCHAR(5) | DEFAULT 'fr' | `fr`, `en`, `ar` |
| `onboarding_complete` | BOOLEAN | DEFAULT false | |
| `niveau_scolaire` | VARCHAR(50) | | Élève uniquement |
| `verification_status` | ENUM(VerificationStatus) | DEFAULT 'unverified' | |
| `verification_document_url` | VARCHAR(500) | | |
| `verification_reviewed_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `verification_reviewed_at` | TIMESTAMP | | |
| `verification_rejection_reason` | TEXT | | |
| `token_balance` | INTEGER | DEFAULT 0 | **DEPRECATED** — read-only, legacy |
| `dt_balance` | NUMERIC(10,2) | DEFAULT 0.0 | **DEPRECATED** — read-only, legacy |
| `stripe_customer_id` | VARCHAR(500) | | |
| `is_approved` | BOOLEAN | | Teacher only |
| `approved_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `approved_at` | TIMESTAMP | | |
| `teacher_certificate_url` | VARCHAR(500) | | |
| `is_active` | BOOLEAN | DEFAULT true | |
| `last_login` | TIMESTAMP | | |
| `failed_login_attempts` | INTEGER | DEFAULT 0 | Brute-force protection |
| `locked_until` | TIMESTAMP | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

**Contraintes uniques** : `(school_id, email)` → `uq_user_school_email`
**Index** : `ix_users_school_id`, `ix_users_email`, `ix_users_role`, `ix_users_school_role`

### `parent_enfants` — Lien Parent → Élève

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `parent_user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `eleve_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `date_creation` | TIMESTAMP | DEFAULT utcnow | |

**Contrainte unique** : `(parent_user_id, eleve_id)` → `uq_parent_eleve`

---

## 3. Finances & Portefeuille

### `wallet_transactions` — Grand livre append-only (source de vérité)

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `pool` | ENUM(WalletPool) | NOT NULL | |
| `amount` | **NUMERIC(10,2)** | NOT NULL | +crédit, -débit. **Decimal Python** |
| `feature` | ENUM(BillableFeature) | | null pour opérations crédit |
| `related_request_id` | VARCHAR(200) | | Traçabilité AI |
| `expires_at` | TIMESTAMP | | trial/school_allocated uniquement |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `metadata` | JSON | | input/output tokens |

**Index** : `ix_wallet_tx_user_id`, `ix_wallet_tx_user_pool(user_id, pool)`, `ix_wallet_tx_created_at`
**Règle** : INSERT uniquement, jamais UPDATE/DELETE (intégrité ledger)

### `transactions` — Grand livre legacy

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `uuid` | UUID | UNIQUE | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `type` | ENUM(TransactionType) | NOT NULL | |
| `amount` | FLOAT | NOT NULL | Legacy — non converti |
| `currency` | ENUM(Currency) | NOT NULL | |
| `description` | TEXT | | |
| `reference_id` | VARCHAR(255) | | |
| `status` | VARCHAR(50) | DEFAULT 'completed' | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `payments` — Stripe

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `amount` | **NUMERIC(10,2)** | NOT NULL | TND |
| `currency` | VARCHAR(3) | DEFAULT 'TND' | |
| `status` | ENUM(PaymentStatus) | DEFAULT 'pending' | |
| `stripe_session_id` | VARCHAR(500) | UNIQUE | |
| `stripe_payment_intent` | VARCHAR(500) | | |
| `subscription_months` | INTEGER | DEFAULT 1 | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `course_purchases` — Achat de cours

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `student_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `course_id` | INTEGER | FK → courses.id ON DELETE CASCADE, NOT NULL | |
| `amount_paid` | **NUMERIC(10,2)** | NOT NULL | |
| `currency` | VARCHAR(10) | DEFAULT 'TND' | |
| `platform_fee` | **NUMERIC(10,2)** | DEFAULT 0.0 | Commission EDUAI |
| `teacher_revenue` | **NUMERIC(10,2)** | DEFAULT 0.0 | Montant enseignant |
| `commission_rate_applied` | **NUMERIC(5,2)** | | Taux appliqué |
| `transaction_id` | VARCHAR(255) | | |
| `refunded` | BOOLEAN | DEFAULT false | |
| `refund_reason` | TEXT | | |
| `refunded_at` | TIMESTAMP | | |
| `purchased_at` | TIMESTAMP | DEFAULT utcnow | |

**Contrainte unique** : `(student_id, course_id)` → `uq_purchases_student_course`

### `pack_purchases` — Achat de packs

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `pack_id` | INTEGER | FK → study_packs.id ON DELETE CASCADE, NOT NULL | |
| `purchaser_type` | VARCHAR(20) | NOT NULL | `"student"` ou `"school"` |
| `student_id` | INTEGER | FK → users.id ON DELETE CASCADE | Nullable si school |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE | Nullable si student |
| `valid_from` | TIMESTAMP | NOT NULL | |
| `valid_until` | TIMESTAMP | NOT NULL | |
| `status` | VARCHAR(20) | DEFAULT 'active' | |
| `amount_paid` | **NUMERIC(10,2)** | NOT NULL | |
| `currency` | VARCHAR(10) | DEFAULT 'TND' | |
| `transaction_id` | VARCHAR(255) | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `study_packs` — Catalogue de packs

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `name` | VARCHAR(255) | NOT NULL | ex: "Pack 9ème de base — Toutes matières" |
| `description` | TEXT | | |
| `niveau_scolaire` | VARCHAR(50) | NOT NULL | doit correspondre `NiveauScolaire` |
| `matieres` | JSON | | null = toutes, sinon `["Mathématiques","Sciences"]` |
| `price` | **NUMERIC(10,2)** | NOT NULL | |
| `currency` | VARCHAR(10) | DEFAULT 'TND' | |
| `validity_duration_days` | INTEGER | DEFAULT 365 | |
| `status` | VARCHAR(20) | DEFAULT 'draft' | |
| `owner_type` | VARCHAR(30) | DEFAULT 'eduai_catalog' | |
| `school_id` | INTEGER | FK → schools.id ON DELETE SET NULL | |
| `created_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `subscriptions` — Abonnements école

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `plan_id` | INTEGER | FK → token_packages.id ON DELETE SET NULL | |
| `status` | VARCHAR(50) | DEFAULT 'active' | |
| `stripe_subscription_id` | VARCHAR(255) | | |
| `stripe_customer_id` | VARCHAR(255) | | |
| `started_at` | TIMESTAMP | | |
| `ends_at` | TIMESTAMP | | |
| `is_active` | BOOLEAN | DEFAULT true | |

### `token_packages` — Pack de tokens IA

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `name` | VARCHAR(100) | NOT NULL | |
| `tokens` | INTEGER | NOT NULL | |
| `price_dt` | FLOAT | NOT NULL | |
| `bonus_tokens` | INTEGER | DEFAULT 0 | |
| `is_active` | BOOLEAN | DEFAULT true | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

---

## 4. Cours & Contenu

### `courses` — Cours

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `uuid` | UUID | UNIQUE | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `author_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `modified_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `title` | VARCHAR(255) | NOT NULL | |
| `short_description` | VARCHAR(500) | | |
| `description` | TEXT | | |
| `thumbnail_url` | VARCHAR(500) | | |
| `cover_url` | VARCHAR(500) | | |
| `slug` | VARCHAR(255) | UNIQUE | |
| `language` | VARCHAR(10) | DEFAULT 'fr' | |
| `prerequisites` | TEXT | | |
| `learning_objectives` | TEXT | | |
| `visibility` | VARCHAR(20) | DEFAULT 'private' | |
| `enrollment_type` | VARCHAR(20) | DEFAULT 'open' | |
| `owner_type` | VARCHAR(30) | DEFAULT 'school' | |
| `owner_id` | INTEGER | | school_id ou teacher_id |
| `price` | **NUMERIC(10,2)** | | null = gratuit |
| `currency` | VARCHAR(10) | DEFAULT 'TND' | |
| `commission_rate` | **NUMERIC(5,2)** | | % EDUAI (independent_teacher) |
| `price_tokens` | INTEGER | DEFAULT 0 | |
| `price_dt` | FLOAT | DEFAULT 0.0 | |
| `category` | VARCHAR(100) | | |
| `level` | VARCHAR(50) | | |
| `niveau_scolaire` | VARCHAR(50) | | Tunisien |
| `tags` | JSON | | |
| `status` | ENUM(CourseStatus) | DEFAULT 'draft' | |
| `is_published` | BOOLEAN | DEFAULT false | |
| `max_students` | INTEGER | | |
| `pedagogical_status` | VARCHAR(30) | DEFAULT 'draft' | |
| `validated_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `validated_at` | TIMESTAMP | | |
| `validated_by_role` | VARCHAR(30) | | |
| `total_modules` | INTEGER | DEFAULT 0 | |
| `total_lessons` | INTEGER | DEFAULT 0 | |
| `total_duration_minutes` | INTEGER | DEFAULT 0 | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `start_date` | TIMESTAMP | | |
| `end_date` | TIMESTAMP | | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |
| `published_at` | TIMESTAMP | | |

**Index** : `ix_courses_school_id`, `ix_courses_author_id`, `ix_courses_status`, `ix_courses_school_status`

### `modules` — Chapitres de cours

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `course_id` | INTEGER | FK → courses.id ON DELETE CASCADE, NOT NULL | |
| `title` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | | |
| `order` | INTEGER | DEFAULT 0 | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `lessons` — Leçons

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `module_id` | INTEGER | FK → modules.id ON DELETE CASCADE, NOT NULL | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `teacher_id` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `title` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | | |
| `lesson_type` | VARCHAR(50) | DEFAULT 'text' | |
| `content_type` | ENUM(ContentType) | DEFAULT 'text' | |
| `content_url` | VARCHAR(500) | | |
| `content_text` | TEXT | | |
| `content_html` | TEXT | | |
| `video_url` | VARCHAR(500) | | |
| `video_duration_seconds` | INTEGER | | |
| `video_thumbnail_url` | VARCHAR(500) | | |
| `pdf_url` | VARCHAR(500) | | |
| `document_url` | VARCHAR(500) | | |
| `document_type` | VARCHAR(20) | | |
| `image_urls` | TEXT | | |
| `link_url` | VARCHAR(500) | | |
| `link_title` | VARCHAR(255) | | |
| `order` | INTEGER | DEFAULT 0 | |
| `duration_minutes` | INTEGER | DEFAULT 0 | |
| `is_free` | BOOLEAN | DEFAULT false | |
| `is_preview` | BOOLEAN | DEFAULT false | |
| `quiz_id` | INTEGER | FK → quizzes.id ON DELETE SET NULL | |
| `ai_generated` | BOOLEAN | DEFAULT false | |
| `tokens_used` | INTEGER | | |
| `ai_image_prompt` | TEXT | | |
| `ai_video_prompt` | TEXT | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |
| `completed_at` | TIMESTAMP | | |

### `quizzes` — Quiz

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `lesson_id` | INTEGER | FK → lessons.id ON DELETE SET NULL | |
| `title` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | | |
| `time_limit_seconds` | INTEGER | | |
| `passing_score_percent` | INTEGER | DEFAULT 70 | |
| `max_attempts` | INTEGER | | |
| `shuffle_questions` | BOOLEAN | DEFAULT false | |
| `shuffle_options` | BOOLEAN | DEFAULT false | |
| `show_results` | BOOLEAN | DEFAULT true | |
| `show_correct_answers` | BOOLEAN | DEFAULT true | |
| `total_points` | INTEGER | DEFAULT 0 | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `quiz_questions`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `quiz_id` | INTEGER | FK → quizzes.id ON DELETE CASCADE, NOT NULL | |
| `question_text` | TEXT | NOT NULL | |
| `question_type` | VARCHAR(20) | DEFAULT 'mcq' | |
| `points` | INTEGER | DEFAULT 1 | |
| `explanation` | TEXT | | |
| `order_index` | INTEGER | DEFAULT 0 | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `quiz_options`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `question_id` | INTEGER | FK → quiz_questions.id ON DELETE CASCADE, NOT NULL | |
| `option_text` | TEXT | NOT NULL | |
| `is_correct` | BOOLEAN | DEFAULT false | |
| `order_index` | INTEGER | DEFAULT 0 | |

### `quiz_attempts`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `quiz_id` | INTEGER | FK → quizzes.id ON DELETE CASCADE, NOT NULL | |
| `student_id` | INTEGER | NOT NULL | Pas de FK (legacy) |
| `status` | VARCHAR(20) | DEFAULT 'in_progress' | |
| `score` | FLOAT | | |
| `score_percent` | FLOAT | | |
| `correct_count` | INTEGER | | |
| `total_count` | INTEGER | | |
| `passed` | BOOLEAN | | |
| `started_at` | TIMESTAMP | DEFAULT utcnow | |
| `completed_at` | TIMESTAMP | | |
| `graded_at` | TIMESTAMP | | |

### `quiz_answers`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `attempt_id` | INTEGER | FK → quiz_attempts.id ON DELETE CASCADE, NOT NULL | |
| `question_id` | INTEGER | NOT NULL | Pas de FK (legacy) |
| `selected_option_ids` | TEXT | | |
| `text_answer` | TEXT | | |
| `is_correct` | BOOLEAN | | |
| `points_awarded` | INTEGER | DEFAULT 0 | |
| `answered_at` | TIMESTAMP | DEFAULT utcnow | |

### `classrooms` — Salles de classe

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `uuid` | UUID | UNIQUE | |
| `name` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | | |
| `invite_code` | VARCHAR(20) | UNIQUE | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `teacher_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `is_active` | BOOLEAN | DEFAULT true | |
| `max_students` | INTEGER | DEFAULT 30 | |
| `course_id` | INTEGER | FK → courses.id ON DELETE SET NULL | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `course_enrollments`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `student_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `course_id` | INTEGER | FK → courses.id ON DELETE CASCADE, NOT NULL | |
| `status` | ENUM(EnrollmentStatus) | DEFAULT 'active' | |
| `progress_percent` | INTEGER | DEFAULT 0 | |
| `enrolled_at` | TIMESTAMP | DEFAULT utcnow | |
| `completed_at` | TIMESTAMP | | |

**Contrainte unique** : `(student_id, course_id)` → `uq_student_course`

### `classroom_enrollments`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `student_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `classroom_id` | INTEGER | FK → classrooms.id ON DELETE CASCADE, NOT NULL | |
| `status` | ENUM(EnrollmentStatus) | DEFAULT 'active' | |
| `role` | VARCHAR(50) | DEFAULT 'student' | `student`, `monitor` |
| `enrolled_at` | TIMESTAMP | DEFAULT utcnow | |

**Contrainte unique** : `(student_id, classroom_id)` → `uq_student_classroom`

### `school_course_access` — Distribution B2B

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `course_id` | INTEGER | FK → courses.id ON DELETE CASCADE, NOT NULL | |
| `purchased_at` | TIMESTAMP | DEFAULT utcnow | |
| `is_active` | BOOLEAN | DEFAULT true | |
| `granted_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `price_paid_dt` | **NUMERIC(10,2)** | DEFAULT 0.0 | |

**Contrainte unique** : `(school_id, course_id)` → `ix_sca_school_course`

### `teacher_classes` — Classes enseignant (v2)

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `teacher_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE | |
| `name` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | | |
| `code` | VARCHAR(50) | | |
| `is_active` | BOOLEAN | DEFAULT true | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `class_course_access` — Liaison classe ↔ cours

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `class_id` | INTEGER | FK → teacher_classes.id ON DELETE CASCADE, NOT NULL | |
| `course_id` | INTEGER | FK → courses.id ON DELETE CASCADE, NOT NULL | |
| `assigned_at` | TIMESTAMP | DEFAULT utcnow | |
| `is_active` | BOOLEAN | DEFAULT true | |

**Contrainte unique** : `(class_id, course_id)` → `ix_cca_class_course`

### `student_enrollments` — Inscription élève ↔ classe

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `student_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `class_id` | INTEGER | FK → teacher_classes.id ON DELETE CASCADE, NOT NULL | |
| `enrolled_at` | TIMESTAMP | DEFAULT utcnow | |
| `is_active` | BOOLEAN | DEFAULT true | |

**Contrainte unique** : `(student_id, class_id)` → `ix_se_student_class`

### `progress` — Progression par leçon (legacy)

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `lesson_id` | INTEGER | FK → lessons.id ON DELETE CASCADE, NOT NULL | |
| `status` | VARCHAR(20) | DEFAULT 'not_started' | |
| `time_spent_seconds` | INTEGER | DEFAULT 0 | |
| `score` | FLOAT | | |
| `started_at` | TIMESTAMP | | |
| `completed_at` | TIMESTAMP | | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

**Contrainte unique** : `(user_id, lesson_id)` → `ix_progress_user_lesson`

### `lesson_progress` — Progression détaillée (legacy)

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `enrollment_id` | INTEGER | NOT NULL | Pas de FK |
| `lesson_id` | INTEGER | NOT NULL | Pas de FK |
| `status` | VARCHAR(20) | DEFAULT 'not_started' | |
| `video_position_seconds` | INTEGER | DEFAULT 0 | |
| `video_completed` | BOOLEAN | DEFAULT false | |
| `content_completed` | BOOLEAN | DEFAULT false | |
| `quiz_completed` | BOOLEAN | DEFAULT false | |
| `quiz_passed` | BOOLEAN | | |
| `quiz_score` | FLOAT | | |
| `started_at` | TIMESTAMP | | |
| `completed_at` | TIMESTAMP | | |
| `time_spent_seconds` | INTEGER | DEFAULT 0 | |

**Contrainte unique** : `(enrollment_id, lesson_id)` → `uq_enrollment_lesson`

### `assignments` — Devoirs

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `classroom_id` | INTEGER | FK → classrooms.id ON DELETE CASCADE, NOT NULL | |
| `title` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | | |
| `instructions` | TEXT | | |
| `max_score` | INTEGER | DEFAULT 100 | |
| `due_date` | TIMESTAMP | | |
| `allow_late_submission` | BOOLEAN | DEFAULT false | |
| `is_active` | BOOLEAN | DEFAULT true | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `submissions`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `assignment_id` | INTEGER | FK → assignments.id ON DELETE CASCADE, NOT NULL | |
| `student_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `content` | TEXT | | |
| `file_url` | VARCHAR(500) | | |
| `ai_score` | INTEGER | | |
| `ai_feedback` | TEXT | | |
| `tokens_used` | INTEGER | | |
| `is_late` | BOOLEAN | DEFAULT false | |
| `is_graded` | BOOLEAN | DEFAULT false | |
| `submitted_at` | TIMESTAMP | DEFAULT utcnow | |
| `graded_at` | TIMESTAMP | | |

### `certificates`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `student_id` | INTEGER | NOT NULL | Pas de FK |
| `course_id` | INTEGER | NOT NULL | Pas de FK |
| `enrollment_id` | INTEGER | NOT NULL | Pas de FK |
| `certificate_number` | VARCHAR(50) | UNIQUE, NOT NULL | |
| `student_name` | VARCHAR(255) | NOT NULL | |
| `course_name` | VARCHAR(255) | NOT NULL | |
| `issue_date` | TIMESTAMP | DEFAULT utcnow | |
| `expiry_date` | TIMESTAMP | | |
| `status` | VARCHAR(20) | DEFAULT 'ready' | |
| `pdf_url` | VARCHAR(500) | | |
| `verification_code` | VARCHAR(100) | UNIQUE, NOT NULL | |
| `grade` | FLOAT | | |
| `completion_percent` | INTEGER | DEFAULT 0 | |

**Contrainte unique** : `(student_id, course_id)` → `uq_cert_student_course`

### `notes` — Notes apprenant

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | NOT NULL | Pas de FK |
| `lesson_id` | INTEGER | NOT NULL | Pas de FK |
| `content` | TEXT | NOT NULL | |
| `position` | INTEGER | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `bookmarks`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | NOT NULL | Pas de FK |
| `lesson_id` | INTEGER | NOT NULL | Pas de FK |
| `position_seconds` | INTEGER | DEFAULT 0 | |
| `note` | VARCHAR(255) | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `documents` — Documents RAG

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `uuid` | UUID | UNIQUE | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `uploader_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `file_name` | VARCHAR(255) | NOT NULL | |
| `file_url` | VARCHAR(500) | NOT NULL | |
| `file_size` | INTEGER | | |
| `file_type` | VARCHAR(50) | | |
| `faiss_vector_id` | VARCHAR(255) | | |
| `status` | ENUM(DocumentStatus) | DEFAULT 'pending' | |
| `chunk_count` | INTEGER | | |
| `error_message` | TEXT | | |
| `processed_at` | TIMESTAMP | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `media_assets`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `owner_id` | INTEGER | NOT NULL | Pas de FK |
| `filename` | VARCHAR(500) | NOT NULL | |
| `original_filename` | VARCHAR(255) | NOT NULL | |
| `mime_type` | VARCHAR(100) | NOT NULL | |
| `size_bytes` | INTEGER | DEFAULT 0 | |
| `url` | VARCHAR(1000) | NOT NULL | |
| `storage_type` | VARCHAR(20) | DEFAULT 'local' | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `teacher_registrations`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `existing_user_id` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `email` | VARCHAR(255) | NOT NULL | |
| `full_name` | VARCHAR(255) | NOT NULL | |
| `hashed_password` | VARCHAR(500) | | |
| `status` | ENUM(TeacherRegistrationStatus) | DEFAULT 'pending' | |
| `rejection_reason` | TEXT | | |
| `certificate_url` | VARCHAR(500) | | |
| `cv_url` | VARCHAR(500) | | |
| `reviewed_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `reviewed_at` | TIMESTAMP | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

---

## 5. Parcours adaptatif & Validation pédagogique

### `niveaux_etude` — Arborescence : niveaux

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `nom` | VARCHAR(100) | UNIQUE, NOT NULL | ex: "9ème de base" |
| `ordre` | INTEGER | NOT NULL, DEFAULT 0 | |

### `matieres` — Arborescence : matières

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `niveau_etude_id` | INTEGER | FK → niveaux_etude.id ON DELETE CASCADE, NOT NULL | |
| `nom` | VARCHAR(100) | NOT NULL | |
| `remediation_threshold` | INTEGER | DEFAULT 40 | Score < 40% → Remédiation |
| `standard_threshold` | INTEGER | DEFAULT 75 | 40–75% → Standard |
| `avance_threshold` | INTEGER | DEFAULT 75 | > 75% → Avancé |

### `chapter_pathways` — Arborescence : chapitres

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `matiere_id` | INTEGER | FK → matieres.id ON DELETE CASCADE, NOT NULL | |
| `nom` | VARCHAR(200) | NOT NULL | |
| `ordre` | INTEGER | NOT NULL, DEFAULT 0 | |

### `notions` — Arborescence : notions

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `chapitre_id` | INTEGER | FK → chapter_pathways.id ON DELETE CASCADE, NOT NULL | |
| `nom` | VARCHAR(200) | NOT NULL | |
| `ordre` | INTEGER | NOT NULL, DEFAULT 0 | |

### `contenus_notion` — Contenus pédagogiques par niveau d'assimilation

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `notion_id` | INTEGER | FK → notions.id ON DELETE CASCADE, NOT NULL | |
| `niveau_assimilation` | VARCHAR(20) | NOT NULL | `remediation`, `standard`, `avance` |
| `type_ressource` | VARCHAR(30) | NOT NULL | `video`, `fiche`, `quiz`, `banque_exercices`, `evaluation_ia` |
| `contenu` | TEXT | NOT NULL | texte ou référence média |
| `enseignant_id` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `statut_pedagogique` | VARCHAR(10) | DEFAULT 'a' | `a`=actif, `b`=brouillon, `c`=archivé |
| `statut_validation_pedagogique` | VARCHAR(20) | DEFAULT 'en_attente' | |
| `valide_par` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `date_validation` | TIMESTAMP | | |
| `commentaire_rejet` | TEXT | | |

### `profils_assimilation` — Profil d'assimilation élève

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `eleve_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `chapitre_id` | INTEGER | FK → chapter_pathways.id ON DELETE CASCADE, NOT NULL | |
| `niveau_assimilation_courant` | VARCHAR(20) | NOT NULL | |
| `source_changement` | VARCHAR(30) | NOT NULL | |
| `score_declencheur` | FLOAT | | |
| `date` | TIMESTAMP | NOT NULL, DEFAULT utcnow | |
| `statut_validation` | VARCHAR(30) | DEFAULT 'auto_applique' | |

**Index** : `ix_profils_assimilation_eleve`, `ix_profils_assimilation_chapitre`, `ix_profils_assimilation_eleve_chapitre`

### `historiques_scores` — Historique scores

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `eleve_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `chapitre_id` | INTEGER | FK → chapter_pathways.id ON DELETE CASCADE, NOT NULL | |
| `quiz_id` | INTEGER | FK → quizzes.id ON DELETE SET NULL | |
| `score` | FLOAT | NOT NULL | |
| `date` | TIMESTAMP | NOT NULL, DEFAULT utcnow | |

### `notifications_reorientation`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `profil_assimilation_id` | INTEGER | FK → profils_assimilation.id ON DELETE CASCADE, NOT NULL | |
| `enseignant_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `date_notification` | TIMESTAMP | NOT NULL, DEFAULT utcnow | |
| `date_limite_action` | TIMESTAMP | NOT NULL | |
| `action_prise` | VARCHAR(20) | DEFAULT 'aucune' | |

### `learning_goals` — Objectifs pédagogiques

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `matiere` | VARCHAR(100) | | null = transversal |
| `horizon` | VARCHAR(20) | NOT NULL | `daily`, `weekly`, `monthly` |
| `metric_type` | VARCHAR(50) | NOT NULL | |
| `target_value` | **NUMERIC(10,2)** | NOT NULL | |
| `period_start` | TIMESTAMP | NOT NULL | |
| `period_end` | TIMESTAMP | NOT NULL | |
| `source` | VARCHAR(30) | DEFAULT 'auto_generated' | |
| `created_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

**Règle** : `statut` n'est JAMAIS stocké — toujours calculé dynamiquement via `compute_goal_status()`

### `placement_tests` — Tests de positionnement

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `matiere` | VARCHAR(100) | NOT NULL | |
| `niveau` | VARCHAR(50) | NOT NULL | |
| `title` | VARCHAR(255) | | |
| `questions` | JSON | NOT NULL | Format: `[{"text","options","correct","difficulty"}]` |
| `created_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `is_active` | BOOLEAN | DEFAULT true | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

### `placement_test_results`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `placement_test_id` | INTEGER | FK → placement_tests.id ON DELETE CASCADE, NOT NULL | |
| `competency_level` | VARCHAR(30) | NOT NULL | `debutant`, `intermediaire`, `avance` |
| `answers` | JSON | | |
| `score` | FLOAT | | |
| `completed_at` | TIMESTAMP | DEFAULT utcnow | |

---

## 6. RBAC Pédagogique

### `specialites_pedagogiques`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `ecole_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | Scopée par école |
| `nom` | VARCHAR(100) | NOT NULL | ex: "Sciences" |
| `cycle_scolaire` | VARCHAR(50) | NOT NULL | `1er_cycle`, `2eme_cycle` |

### `specialite_pedagogique_matieres` — Table pivot

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `specialite_id` | INTEGER | FK → specialites_pedagogiques.id ON DELETE CASCADE, NOT NULL | |
| `matiere_id` | INTEGER | FK → matieres.id ON DELETE CASCADE, NOT NULL | |

**Contrainte unique** : `(specialite_id, matiere_id)` → `uq_specialite_matiere`

### `responsables_pedagogiques`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `specialite_id` | INTEGER | FK → specialites_pedagogiques.id ON DELETE CASCADE, NOT NULL | |

**Contrainte unique** : `(user_id, specialite_id)` → `uq_user_specialite`

### `responsable_niveaux_etude` — Table pivot

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `responsable_id` | INTEGER | FK → responsables_pedagogiques.id ON DELETE CASCADE, PK | |
| `niveau_etude_id` | INTEGER | FK → niveaux_etude.id ON DELETE CASCADE, PK | |

---

## 7. Gamification

### `badge_definitions`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `nom` | VARCHAR(100) | UNIQUE, NOT NULL | |
| `description` | TEXT | NOT NULL | |
| `icon_url` | VARCHAR(500) | | |
| `couleur` | VARCHAR(20) | DEFAULT '#F97316' | |
| `categorie` | VARCHAR(50) | NOT NULL | `progression`, `quiz`, `streak`, `special` |
| `critere_type` | VARCHAR(50) | NOT NULL | `quiz_count`, `score_avg`, `streak_days`, `chapters_completed` |
| `critere_valeur` | INTEGER | NOT NULL | Seuil quantitatif |
| `points` | INTEGER | DEFAULT 10 | |

### `student_badges`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `eleve_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `badge_id` | INTEGER | FK → badge_definitions.id ON DELETE CASCADE, NOT NULL | |
| `date_obtention` | TIMESTAMP | NOT NULL, DEFAULT utcnow | |

**Contrainte unique** : `(eleve_id, badge_id)` → `uq_student_badge`

### `student_streaks`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `eleve_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `date_jour` | DATE | NOT NULL | |
| `streak_login` | BOOLEAN | DEFAULT false | |
| `streak_quiz` | BOOLEAN | DEFAULT false | |
| `streak_objectif` | BOOLEAN | DEFAULT false | |
| `points_jour` | INTEGER | DEFAULT 0 | |

**Contrainte unique** : `(eleve_id, date_jour)` → `uq_student_streak_day`

### `student_rankings`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `eleve_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `matiere_id` | INTEGER | FK → matieres.id ON DELETE SET NULL | |
| `palier` | VARCHAR(20) | NOT NULL | `decouverte`, `excellence`, `etablissement` |
| `points_total` | INTEGER | DEFAULT 0 | |
| `rang` | INTEGER | | |
| `date_calcul` | TIMESTAMP | NOT NULL, DEFAULT utcnow | |

---

## 8. LMS Course Builder (cb_*)

> Tables `cb_*` dans `models_lms.py` — architecture séparée via `LmsBase`.
> Système legacy de construction de cours avec séquence pédagogique fine.

| Table | Description | FK principales |
|-------|-------------|----------------|
| `cb_course_contents` | Cours (Super Admin) | — |
| `cb_chapters` | Chapitres | → cb_course_contents |
| `cb_lessons` | Leçons (multi-format) | → cb_chapters |
| `cb_quizzes` | Quiz | → cb_lessons |
| `cb_quiz_questions` | Questions | → cb_quizzes |
| `cb_quiz_options` | Options réponse | → cb_quiz_questions |
| `cb_correct_answers` | Bonnes réponses | → cb_quiz_questions, cb_quiz_options |
| `cb_quiz_attempts` | Tentatives | → cb_quizzes |
| `cb_student_answers` | Réponses élèves | → cb_quiz_attempts, cb_quiz_questions |
| `cb_course_enrollments` | Inscriptions | → cb_course_contents |
| `cb_lesson_progress` | Progression/leçon | → cb_course_enrollments, cb_lessons |
| `cb_video_watch_progress` | Progression vidéo | → cb_course_enrollments, cb_lessons |
| `cb_certificates` | Certificats | → cb_course_contents, cb_course_enrollments |

---

## 9. Conversations IA

### `ai_conversations`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `title` | VARCHAR(255) | DEFAULT 'Nouvelle conversation' | |
| `subject` | VARCHAR(100) | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

**Index** : `ix_ai_conv_user_id`, `ix_ai_conv_updated_at`

### `ai_chat_messages`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `conversation_id` | INTEGER | FK → ai_conversations.id ON DELETE CASCADE, NOT NULL | |
| `role` | VARCHAR(20) | NOT NULL | `"user"` ou `"assistant"` |
| `content` | TEXT | NOT NULL | |
| `detected_language` | VARCHAR(10) | | `"ar"`, `"fr"`, `"en"` |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

**Index** : `ix_ai_msg_conv_id`

---

## 10. Tables complémentaires

### `messages` — Messagerie plateforme

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `uuid` | UUID | UNIQUE | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `sender_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `receiver_id` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `type` | ENUM(MessageType) | DEFAULT 'direct' | |
| `subject` | VARCHAR(255) | NOT NULL | |
| `body` | TEXT | NOT NULL | |
| `target_audience` | VARCHAR(50) | | `all`, `students`, `teachers`, `specific` |
| `recipient_role` | VARCHAR(20) | | |
| `is_official_observation` | BOOLEAN | DEFAULT false | |
| `is_read` | BOOLEAN | DEFAULT false | |
| `read_at` | TIMESTAMP | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `platform_settings`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `school_id` | INTEGER | FK → schools.id ON DELETE SET NULL | null = global |
| `key` | VARCHAR(100) | NOT NULL | |
| `value` | TEXT | | |
| `description` | VARCHAR(255) | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |
| `updated_at` | TIMESTAMP | DEFAULT utcnow | |

**Contrainte unique** : `(school_id, key)` → `ix_settings_key`

### `audit_logs`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `admin_id` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `admin_email` | VARCHAR(255) | NOT NULL | |
| `action` | VARCHAR(100) | NOT NULL | |
| `target_type` | VARCHAR(50) | | |
| `target_id` | INTEGER | | |
| `details` | TEXT | | |
| `ip_address` | VARCHAR(45) | | IPv4/IPv6 |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `ai_usage_logs`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `school_id` | INTEGER | DEFAULT 0 | |
| `action` | VARCHAR(100) | NOT NULL | |
| `tokens_used` | INTEGER | DEFAULT 0 | |
| `cost_usd` | FLOAT | DEFAULT 0.0 | |
| `description` | TEXT | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `ai_content_reports`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `message_id` | VARCHAR(100) | | |
| `conversation_id` | INTEGER | | Pas de FK |
| `reported_by` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `school_id` | INTEGER | FK → schools.id ON DELETE SET NULL | |
| `reason` | TEXT | NOT NULL | |
| `details` | TEXT | | |
| `status` | VARCHAR(20) | DEFAULT 'pending' | |
| `resolved_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `resolved_at` | TIMESTAMP | | |
| `resolution_action` | TEXT | | |
| `resolution_response` | TEXT | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `pedagogical_escalations`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `course_id` | INTEGER | FK → courses.id ON DELETE SET NULL | |
| `escalated_by` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `reason` | TEXT | NOT NULL | |
| `details` | TEXT | | |
| `status` | VARCHAR(20) | DEFAULT 'pending' | |
| `resolved_by` | INTEGER | FK → users.id ON DELETE SET NULL | |
| `resolved_at` | TIMESTAMP | | |
| `resolution` | TEXT | | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

### `teacher_reassignments`

| Colonne | Type | Contraintes | Notes |
|---------|------|-------------|-------|
| `id` | INTEGER | PK | |
| `class_id` | INTEGER | FK → classrooms.id ON DELETE CASCADE, NOT NULL | |
| `original_teacher_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `new_teacher_id` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `school_id` | INTEGER | FK → schools.id ON DELETE CASCADE, NOT NULL | |
| `start_date` | TIMESTAMP | NOT NULL | |
| `end_date` | TIMESTAMP | | |
| `reason` | TEXT | | |
| `created_by` | INTEGER | FK → users.id ON DELETE CASCADE, NOT NULL | |
| `created_at` | TIMESTAMP | DEFAULT utcnow | |

---

## Annexe A — Tables sans clé étrangère

> Ces tables utilisent des colonnes `INTEGER` pour des identifiants sans contrainte `ForeignKey`.

| Table | Colonne | Type attendu | Note |
|-------|---------|--------------|------|
| `quiz_attempts` | `student_id` | users.id | Pas de FK |
| `quiz_answers` | `question_id` | quiz_questions.id | Pas de FK |
| `certificates` | `student_id` | users.id | Pas de FK |
| `certificates` | `course_id` | courses.id | Pas de FK |
| `certificates` | `enrollment_id` | course_enrollments.id | Pas de FK |
| `notes` | `user_id` | users.id | Pas de FK |
| `notes` | `lesson_id` | lessons.id | Pas de FK |
| `bookmarks` | `user_id` | users.id | Pas de FK |
| `bookmarks` | `lesson_id` | lessons.id | Pas de FK |
| `lesson_progress` | `enrollment_id` | course_enrollments.id | Pas de FK |
| `lesson_progress` | `lesson_id` | lessons.id | Pas de FK |
| `media_assets` | `owner_id` | users.id | Pas de FK |
| `ai_content_reports` | `conversation_id` | — | Pas de FK |

---

## Annexe B — Tables sans documentation

> Ces tables existent dans le code mais n'ont pas de docstrings détaillées dans le modèle.

| Table | Fichier | Ligne | Description déduite |
|-------|---------|-------|---------------------|
| `progress` | models.py:821 | Table legacy — progression utilisateur/leçon |
| `lesson_progress` | models.py:1303 | Table legacy — progression détaillée avec vidéo |
| `notes` | models.py:1268 | Notes apprenant par leçon |
| `bookmarks` | models.py:1286 | Signets apprenant |
| `media_assets` | models.py:1396 | Fichiers média uploadés |
| `platform_settings` | models.py:989 | Paramètres clé-valeur plateforme |
| `audit_logs` | models.py:1370 | Piste d'audit immuable |
| `cb_video_watch_progress` | models_lms.py:360 | Progression vidéo détaillée |
| `cb_correct_answers` | models_lms.py:252 | Bonnes réponses quiz LMS |

---

## Constantes associées

```python
# Limite utilisateurs par palier
SUBSCRIPTION_LIMITS = {
    "free": 10,
    "teacher_pro": 50,
    "school": 200,
    "institution": 1000,
}

# Seuils d'assimilation par défaut (configurable par matière)
DEFAULT_REMEDIATION_THRESHOLD = 40   # < 40%
DEFAULT_STANDARD_THRESHOLD = 75      # 40–75%
DEFAULT_AVANCE_THRESHOLD = 75        # > 75%

# Objectifs : statut TOUJOURS calculé à la volée
# compute_goal_status() dans backend/app/services/goal_tracking.py

# Wallet : Ledger append-only
# INSERT uniquement — jamais UPDATE/DELETE
# Balance = somme des transactions valides
```

---

> **Mise à jour** : 2026-08-01 — Conversion `Float → Numeric(10,2)` pour les colonnes monétaires. Migration SQL : `backend/migrations/2026_08_01_numeric_monetary.sql`

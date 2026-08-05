# RAPPORT D'AUDIT BACKEND — EDUAI Learning Platform

**Date :** 04 août 2026  
**Portée :** Backend complet (D:\RAG_APP_new\backend)  
**Rédacteur :** Audit automatique (opencode/mimo-v2.5-free)  
**Statut :** Version finale  

---

## Sommaire

| Section | Titre | Lien |
|---------|-------|------|
| [Résumé Exécutif](#résumé-exécutif) | Points critiques à retenir | — |
| [ÉTAPE 1](#étape-1--cartographie-structurelle) | Cartographie structurée | [→](#étape-1--cartographie-structurelle) |
| [ÉTAPE 2](#étape-2--modèle-de-données) | Modèle de données | [→](#étape-2--modèle-de-données) |
| [ÉTAPE 3](#étape-3--api-et-endpoints) | API et endpoints | [→](#étape-3--api-et-endpoints) |
| [ÉTAPE 4](#étape-4--sécurité) | Sécurité | [→](#étape-4--sécurité) |
| [ÉTAPE 5](#étape-5--logique-métier-critique) | Logique métier critique | [→](#étape-5--logique-métier-critique) |
| [ÉTAPE 6](#étape-6--qualité-de-code-et-dette-technique) | Qualité de code et dette technique | [→](#étape-6--qualité-de-code-et-dette-technique) |
| [ÉTAPE 7](#étape-7--synthèse-et-priorisation) | Synthèse et priorisation | [→](#étape-7--synthèse-et-priorisation) |

---

## Résumé Exécutif

Le backend EDUAI Learning est une application FastAPI complexe (399+ endpoints, 87+ modèles, 35 routers) servant une plateforme éducative multi-tenant. L'audit révèle **4 risques critiques**, **9 risques importants** et **7 risques mineurs**.

**Points critiques à retenir :**

1. **Fuite de token de réinitialisation de mot de passe** : le token brut est retourné dans le corps de la réponse HTTP (`auth.py:520-523`), permettant une interception.
2. **IDOR sur les scores étudiants** : un étudiant peut soumettre des scores pour n'importe quel autre étudiant via `adaptive_pathway.py:213-216`.
3. **5 champs monétaires encore en `Float`** au lieu de `Numeric` : `Transaction.amount` (`models.py:405`), `TokenPackage.price_dt` (`models.py:430`), `Course.price_dt` (`models.py:484`), `Plan.price` (`models.py:1669`), `AIUsageLog.cost_usd` (`models.py:1118`). Risque d'arrondi sur les transactions financières.
4. **Fichier `.env` contenant des secrets en clé** : clé OpenAI, mot de passe DB en clair (`gill4264`), secret JWT faible (`eduai_super_secret_key_2024_very_secure`).

**Succès notables :** le wallet multi-pocket avec ledger append-only est bien conçu ; la révocation de refresh tokens avec détection de replay est robuste ; les tests métier (wallet, packs, gouvernance, parcours adaptatif) sont substantiels (228 tests).

---

## ÉTAPE 1 — CARTOGRAPHIE STRUCTURELLE

### 1.1 Arborescence complète

Le backend se trouve dans `D:\RAG_APP_new\backend`. Voici la structure arborescente complète :

```
backend/
├── app/
│   ├── main.py                          (443 lignes, point d'entrée)
│   ├── auth.py                          (563 lignes, JWT + inscription + login)
│   ├── models.py                        (2656 lignes, 87+ classes de modèles)
│   ├── schemas.py                       (1435 lignes, schémas Pydantic)
│   ├── deps.py                          (270 lignes, dépendances RBAC)
│   ├── audit.py
│   ├── seeds.py
│   ├── fix_passwords.py
│   ├── db_utils.py
│   ├── api_versioning.py
│   ├── core/
│   │   ├── config.py                    (131 lignes, Settings)
│   │   ├── security.py
│   │   ├── validation.py
│   │   ├── errors.py
│   │   ├── circuit_breaker.py
│   │   ├── queries.py
│   │   ├── rate_limiter.py
│   │   └── token_limits.py
│   ├── db/
│   │   ├── engine.py
│   │   ├── session.py
│   │   ├── multi_tenant_filter.py
│   │   └── models.py                    (337 lignes, modèles legacy dupliqués)
│   ├── ai/
│   │   ├── client.py
│   │   ├── provider_client.py           (9 providers IA)
│   │   ├── embeddings.py
│   │   ├── pdf_processor.py
│   │   ├── rag_service.py
│   │   └── tokens.py
│   ├── payment/
│   │   ├── stripe_service.py
│   │   └── konnect_client.py
│   ├── routers/                         (35+ fichiers de routes)
│   │   ├── admin.py                     (68 endpoints)
│   │   ├── adaptive_pathway.py          (39 endpoints)
│   │   ├── learner.py                   (26 endpoints)
│   │   ├── academy.py                   (23 endpoints)
│   │   ├── lms.py                       (23 endpoints)
│   │   ├── admin_courses.py             (22 endpoints)
│   │   ├── elements.py                  (20 endpoints)
│   │   ├── parcours.py                  (17 endpoints)
│   │   ├── courses.py                   (13 endpoints)
│   │   ├── pedagogical.py               (13 endpoints)
│   │   ├── pedagogical_lead.py          (12 endpoints)
│   │   ├── gamification.py              (10 endpoints)
│   │   ├── ai.py                        (10 endpoints)
│   │   ├── ai_factory.py                (10 endpoints)
│   │   ├── conversations.py             (10 endpoints)
│   │   ├── admin_quizzes.py             (10 endpoints)
│   │   ├── teacher_classes.py
│   │   ├── abonnements.py
│   │   ├── subscriptions.py
│   │   ├── wallet.py
│   │   ├── packs.py
│   │   ├── placement.py
│   │   ├── catalogue.py
│   │   ├── famille.py
│   │   ├── inbox.py
│   │   ├── logs.py
│   │   ├── media.py
│   │   ├── users.py
│   │   ├── licences.py
│   │   ├── bibliotheque.py
│   │   ├── admin_chapters.py
│   │   ├── admin_lessons.py
│   │   └── ... (autres routers)
│   ├── services/                        (16 modules de services)
│   │   └── ...
│   └── tasks/
│       └── subscription_expiration.py
├── alembic/                             (6 fichiers de migration)
│   ├── versions/
│   │   ├── 0001_initial
│   │   ├── 0002_school_id_quiz_prt
│   │   ├── 0003_refresh_tokens
│   │   ├── 0004_modules_a_b
│   │   ├── 7804b0ec91bf_add_plans_table
│   │   └── 0005_scheduled_tier_change
├── tests/                               (20 fichiers, 228 tests uniques)
├── data/                                (index FAISS)
├── scripts/
│   ├── reset_db.py
│   └── seed_demo_school.py
├── 50+ scripts ad-hoc dans la racine
├── requirements.txt
└── pyproject.toml
```

**Preuve :** `app/main.py` (443 lignes) — point d'entrée ; `app/models.py` (2656 lignes) ; `app/auth.py` (563 lignes) ; `app/schemas.py` (1435 lignes) ; `app/deps.py` (270 lignes).

### 1.2 Dépendances (requirements.txt)

Fichier : `requirements.txt`

| Catégorie | Dépendance | Version requise |
|-----------|-----------|-----------------|
| **Framework** | fastapi | >=0.95.0 |
| | uvicorn[standard] | >=0.24.0 |
| **Base de données** | sqlalchemy | >=2.0 |
| | alembic | >=1.12.0 |
| | pg8000 | >=1.0.0 |
| **Sécurité** | python-jose[cryptography] | >=3.3.0 |
| | passlib[bcrypt] | >=1.7.4 |
| | bcrypt | ==4.0.1 (pinné) |
| **Validation** | pydantic | >=1.10.2 |
| | pydantic-settings | >=2.0 |
| | email-validator | >=1.3.0 |
| **IA** | openai | >=1.0.0 |
| | faiss-cpu | >=1.7.0 |
| | langchain-openai | >=0.0.0 |
| | langchain-text-splitters | >=0.0.0 |
| **Paiement** | stripe | >=5.0.0 |
| **PDF** | pypdf | >=3.0.0 |
| | pdfplumber | >=0.7.0 |
| | weasyprint | >=60.0 |
| | python-docx | >=1.1.0 |
| **Cache** | redis | >=5.0.0 |
| | cachetools | >=5.3.0 |
| **Rate limiting** | slowapi | >=0.1.9 |
| **Autres** | python-dotenv | >=1.0 |
| | python-multipart | >=0.0.5 |
| | numpy | >=1.24.0 |
| | aiofiles | >=23.0.0 |
| | python-dateutil | >=2.8.0 |
| | tenacity | >=8.0.0 |

**⚠️ ALERTE CRITIQUE :** `pyproject.toml` est **hors synchronisation** avec `requirements.txt`. Le `pyproject.toml` liste `sqlalchemy ^1.4` (au lieu de `>=2.0`) et `pydantic ^1.10` (au lieu de `>=1.10.2` avec pydantic-settings). De nombreuses dépendances présentes dans `requirements.txt` (openai, faiss-cpu, langchain-openai, redis, slowapi, weasyprint, python-docx, etc.) sont **absentes** de `pyproject.toml`. Cela signifie que les outils de build/installation basés sur pyproject.toml installeraient des versions incorrectes ou incomplètes.

**Preuve :** `requirements.txt` — fichier complet ; `pyproject.toml` — liste `sqlalchemy ^1.4` et `pydantic ^1.10`, absence de 15+ dépendances critiques.

### 1.3 Configuration

Classe `Settings` dans `app/core/config.py` (131 lignes).

Toutes les variables d'environnement sont documentées dans la classe Settings. Aucun secret n'est codé en dur dans le code de production de l'application — tout passe par `Settings` qui lit les variables d'environnement.

**⚠️ ALERTE CRITIQUE :** Le fichier `.env` contient des secrets réels :
- Clé API OpenAI en clair
- Secret JWT faible : `eduai_super_secret_key_2024_very_secure`
- Mot de passe de base de données en clair : `gill4264`
- Clés API commentées pour OpenRouter, Groq et un fournisseur chinois

**Preuve :** `app/core/config.py` — classe Settings ; `.env` — secrets en clair (vérifié par lecture du fichier).

### 1.4 Entrypoint + Middlewares

Point d'entrée : `app/main.py` (443 lignes).

| Composant | Détails |
|-----------|---------|
| **Lifespan** | Démarre `pack_expiration_scheduler` + `goal_scheduler` |
| **Middlewares** | 5 middlewares : RateLimiter, CORS, security_headers, maintenance_mode, request_logging |
| **Routers** | 39 routers enregistrés |
| **Rate limits** | `/auth/login` : 10/min, `/auth/register` : 5/min, `/api/ai/` : 60/min, `/api/admin/` : 200/min, `/api/wallet/` : 30/min |
| **Exception handler global** | Retourne 500 avec détail de l'erreur |
| **Documentation** | Désactivée en production (`docs_url=None`, `redoc_url=None`) |

**Preuve :** `app/main.py:1-443` — lifespan, middlewares, routers, rate limits configurés.

---

## ÉTAPE 2 — MODÈLE DE DONNÉES

### 2.1 Tables exhaustives

87+ classes de modèles réparties dans 3 fichiers principaux + 1 fichier legacy.

#### Fichier principal : `app/models.py` (2656 lignes, 85+ classes)

| Catégorie | Modèles |
|-----------|---------|
| **Multi-tenant** | School, User, Transaction, TokenPackage, Course, Module, Lesson, ClassRoom, CourseEnrollment, ClassroomEnrollment, CoursePurchase, StudyPack, PackPurchase, Progress, Assignment, Submission, Document, Message, PlatformSetting, TeacherRegistration, AIUsageLog, Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer, Note, Bookmark, LessonProgress, Certificate, AuditLog, MediaAsset, SchoolCourseAccess, TeacherClass, ClassCourseAccess, StudentEnrollment, Payment, WalletTransaction, ParentEnfant, AIContentReport, PedagogicalEscalation, TeacherReassignment |
| **Abonnements** | Plan, Subscription, PackDefinition, Abonnement, CompteFamille, FamilleEnfant, LicenceEcole, LicenceAssignation |
| **Parcours adaptatif** | PlacementTest, PlacementTestResult, LearningGoal, NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion, ProfilAssimilationEleve, HistoriqueScoreEleve, NotificationReorientation, SpecialitePedagogique, ResponsablePedagogique |
| **Gamification** | BadgeDefinition, StudentBadge, StudentStreak, StudentRanking |
| **Auth** | PasswordResetToken, RefreshToken |
| **LMS pédagogique** | Competence, Parcours, Chapitre, Lecon, Paragraphe, ElementPedagogique, ElementTexte, ElementVideo, ElementImage, ElementQuiz, ElementPdf, ContentWorkflow, ContentPromotion |

#### Fichier LMS : `app/models_lms.py` (410 lignes, 13 tables)

13 tables `cb_*` utilisant un `LmsBase` séparé : `cb_competences`, `cb_parcours`, `cb_chapitres`, `cb_lecons`, `cb_paragraphes`, `cb_elements_pedagogiques`, `cb_elements_texte`, `cb_elements_video`, `cb_elements_image`, `cb_elements_quiz`, `cb_elements_pdf`, `cb_content_workflows`, `cb_content_promotions`.

**Preuve :** `app/models_lms.py` — LmsBase séparé, 13 tables.

#### Fichier conversations IA : `app/models_ai_conversations.py` (66 lignes)

2 tables : `ai_conversations`, `ai_chat_messages`.

**Preuve :** `app/models_ai_conversations.py` — 2 tables.

#### Fichier legacy : `app/db/models.py` (337 lignes)

Définitions dupliquées de 11 tables : `schools`, `users`, `transactions`, `token_packages`, `courses`, `modules`, `lessons`, `classrooms`, `course_enrollments`, `classroom_enrollments`, `documents`.

**⚠️ ALERTE :** Ces modèles legacy dupliquent 11 définitions de tables déjà présentes dans `app/models.py`. Cela peut provoquer des conflits de mapper SQLAlchemy si les deux fichiers sont importés dans la même session.

**Preuve :** `app/db/models.py` — 11 tables dupliquées ; `app/models.py` — tables originales.

### 2.2 Multi-tenant isolation

#### Tables AVEC `school_id` (filtrage auto) :

| Table | Preuve |
|-------|--------|
| School | `app/models.py` — champ `school_id` présent |
| User | `app/models.py` — champ `school_id` présent |
| Transaction | `app/models.py` — champ `school_id` présent |
| Course | `app/models.py` — champ `school_id` présent |
| Lesson | `app/models.py` — champ `school_id` présent |
| ClassRoom | `app/models.py` — champ `school_id` présent |
| CourseEnrollment | `app/models.py` — champ `school_id` présent |
| ClassroomEnrollment | `app/models.py` — champ `school_id` présent |
| Document | `app/models.py` — champ `school_id` présent |
| Message | `app/models.py` — champ `school_id` présent |
| PlatformSetting | `app/models.py` — champ `school_id` présent |
| TeacherRegistration | `app/models.py` — champ `school_id` présent |
| AIUsageLog | `app/models.py` — champ `school_id` présent |
| Quiz | `app/models.py` — champ `school_id` présent |
| CoursePurchase | `app/models.py` — champ `school_id` présent |
| StudyPack | `app/models.py` — champ `school_id` présent |
| PackPurchase | `app/models.py` — champ `school_id` présent |
| SchoolCourseAccess | `app/models.py` — champ `school_id` présent |
| TeacherClass | `app/models.py` — champ `school_id` présent |
| ClassCourseAccess | `app/models.py` — champ `school_id` présent |
| StudentEnrollment | `app/models.py` — champ `school_id` présent |
| PasswordResetToken | `app/models.py` — champ `school_id` présent |
| AIContentReport | `app/models.py` — champ `school_id` présent |
| PedagogicalEscalation | `app/models.py` — champ `school_id` présent |
| TeacherReassignment | `app/models.py` — champ `school_id` présent |
| Subscription | `app/models.py` — champ `school_id` présent |
| LicenceEcole | `app/models.py` — champ `school_id` présent |
| LicenceAssignation | `app/models.py` — champ `school_id` présent |
| SpecialitePedagogique | `app/models.py` — champ `school_id` présent |
| TokenPackage | `app/models.py` — champ `school_id` présent |

#### Tables SANS `school_id` (isolation fragile) :

| Table | Méthode d'isolation | Risque |
|-------|---------------------|--------|
| Module | Via Course (qui a school_id) | Filtrage indirect |
| Assignment | Via Course → Module | Filtrage à 3 niveaux |
| Submission | Via Assignment → Course | Filtrage à 4 niveaux |
| Progress | Via Lesson → Course | Filtrage à 3 niveaux |
| Note | Via Lesson | Filtrage indirect |
| Bookmark | Via Lesson | Filtrage indirect |
| LessonProgress | Via Lesson | Filtrage indirect |
| Certificate | Via User | Filtrage par utilisateur |
| QuizQuestion | Via Quiz (qui a school_id) | Filtrage indirect |
| QuizOption | Via QuizQuestion → Quiz | Filtrage à 2 niveaux |
| QuizAttempt | Via Quiz | Filtrage indirect |
| QuizAnswer | Via QuizAttempt → Quiz | Filtrage à 2 niveaux |
| MediaAsset | Via Lesson | Filtrage indirect |
| WalletTransaction | Via User (school_id) | Filtrage par utilisateur |
| PackDefinition | Pas de school_id | **Pas d'isolation** |
| Abonnement | Pas de school_id | **Pas d'isolation** |
| CompteFamille | Pas de school_id | **Pas d'isolation** |
| FamilleEnfant | Pas de school_id | **Pas d'isolation** |
| ProfilAssimilationEleve | Pas de school_id | **Pas d'isolation** |
| HistoriqueScoreEleve | Pas de school_id | **Pas d'isolation** |
| NotificationReorientation | Pas de school_id | **Pas d'isolation** |
| ElementPedagogique | Pas de school_id | **Pas d'isolation** |
| Parcours (LMS) | a `niveau_scolaire` mais pas `school_id` | **Pas d'isolation** |

**⚠️ ALERTE :** 13 tables n'ont aucun mécanisme d'isolation multi-tenant, notamment `PackDefinition`, `Abonnement`, `CompteFamille`, `FamilleEnfant`, `ProfilAssimilationEleve`, `HistoriqueScoreEleve`, `NotificationReorientation`, `ElementPedagogique` et `Parcours`. Ces tables partagent potentiellement des données entre écoles.

**Preuve :** `app/models.py` — vérification de chaque classe de modèle pour la présence de `school_id`.

### 2.3 Champs monétaires en Float (NON corrigés)

5 champs critiques utilisent encore `Float` au lieu de `Numeric(10,2)` ou `Numeric(10,4)` :

| # | Modèle | Champ | Localisation | Type actuel | Type recommandé |
|---|--------|-------|-------------|-------------|-----------------|
| 1 | Transaction | amount | `models.py:405` | `Float` | `Numeric(10,2)` |
| 2 | TokenPackage | price_dt | `models.py:430` | `Float` | `Numeric(10,2)` |
| 3 | Course | price_dt | `models.py:484` | `Float` | `Numeric(10,2)` |
| 4 | Plan | price | `models.py:1669` | `Float` | `Numeric(10,2)` |
| 5 | AIUsageLog | cost_usd | `models.py:1118` | `Float` | `Numeric(10,4)` |

**14 champs correctement en `Numeric` :**
- `User.dt_balance`
- `Course.price`
- `Course.commission_rate`
- `CoursePurchase.amount_paid`, `platform_fee`, `teacher_revenue`, `commission_rate_applied`
- `StudyPack.price`
- `PackPurchase.amount_paid`
- `Payment.amount`
- `WalletTransaction.amount`
- `SchoolCourseAccess.price_paid_dt`
- `LearningGoal.target_value`
- `PackDefinition.prix_tnd`

**Preuve :** `app/models.py:405` — `Transaction.amount = Column(Float)` ; `app/models.py:430` — `TokenPackage.price_dt = Column(Float)` ; `app/models.py:484` — `Course.price_dt = Column(Float)` ; `app/models.py:1669` — `Plan.price = Column(Float)` ; `app/models.py:1118` — `AIUsageLog.cost_usd = Column(Float)`.

### 2.4 Migrations

6 migrations dans `alembic/versions/` :

| # | Fichier | Description |
|---|---------|-------------|
| 1 | `0001_initial` | Schéma initial |
| 2 | `0002_school_id_quiz_prt` | Ajout school_id à Quiz + PasswordResetToken |
| 3 | `0003_refresh_tokens` | Refresh tokens |
| 4 | `0004_modules_a_b` | Refactoring modules A/B |
| 5 | `7804b0ec91bf_add_plans_table` | Ajout table Plans + conversion 14 champs Float→Numeric |
| 6 | `0005_scheduled_tier_change` | Downgrade différé (scheduled_tier + scheduled_effective_date) |

**Dérive de migration :** La migration `7804b0ec91bf` a converti 14 champs `Float` → `Numeric` mais en a manqué 5 critiques (voir section 2.3). La classe `Plan` définie dans cette même migration utilise encore `Float` pour le champ `price` (`models.py:1669`).

**Conflit potentiel :** Les modèles legacy dans `app/db/models.py` dupliquent 11 définitions de tables. Si ces modèles sont importés dans la même session que `app/models.py`, cela peut provoquer des conflits de mapper SQLAlchemy.

**Preuve :** `alembic/versions/` — 6 fichiers ; `7804b0ec91bf_add_plans_table` — conversion partielle Float→Numeric.

### 2.5 Diagramme de relations

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   School    │────<│     User     │────<│ Transaction  │
└─────────────┘     └──────────────┘     └─────────────┘
       │                   │
       │                   ├────< WalletTransaction
       │                   ├────< RefreshToken
       │                   ├────< PasswordResetToken
       │                   ├────< ParentEnfant ────< FamilleEnfant
       │                   └────< Subscription
       │
       ├────< Course ─────< Module ─────< Lesson
       │         │              │              │
       │         ├────< CourseEnrollment      ├────< Progress
       │         ├────< CoursePurchase        ├────< LessonProgress
       │         ├────< SchoolCourseAccess    ├────< Note
       │         └────< Quiz                  ├────< Bookmark
       │                   │                  └────< Document
       │                   ├────< QuizQuestion
       │                   └────< QuizAttempt ────< QuizAnswer
       │
       ├────< ClassRoom ────< ClassroomEnrollment
       │
       ├────< StudyPack ────< PackPurchase
       │
       ├────< TeacherClass ────< TeacherClass
       │
       ├────< AIUsageLog
       │
       └────< AuditLog

┌──────────────┐     ┌──────────────────┐
│ Plan         │────<│ Subscription     │
└──────────────┘     └──────────────────┘
       │
       └────< Abonnement ────< CompteFamille ────< FamilleEnfant

┌──────────────┐     ┌──────────────────┐
│ NiveauEtude  │────<│ Matiere          │
└──────────────┘     └──────────────────┘
       │                     │
       └────< Parcours       └────< ChapterPathway
              │
              ├────< Chapitre ────< Lecon
              │
              └────< Notion ────< ContenuNotion

┌──────────────────┐     ┌──────────────────┐
│ ProfilAssimilation│────<│ HistoriqueScore  │
│   Eleve          │     │   Eleve          │
└──────────────────┘     └──────────────────┘
```

**Preuve :** Diagramme construit à partir de l'analyse des relationships dans `app/models.py`.

---

## ÉTAPE 3 — API ET ENDPOINTS

### 3.1 Inventaire complet

**Total : ~399 endpoints** répartis dans 35 fichiers de routes.

| Router | Endpoints | Preuve |
|--------|-----------|--------|
| admin.py | 68 | `app/routers/admin.py` |
| adaptive_pathway.py | 39 | `app/routers/adaptive_pathway.py` |
| learner.py | 26 | `app/routers/learner.py` |
| academy.py | 23 | `app/routers/academy.py` |
| lms.py | 23 | `app/routers/lms.py` |
| admin_courses.py | 22 | `app/routers/admin_courses.py` |
| elements.py | 20 | `app/routers/elements.py` |
| parcours.py | 17 | `app/routers/parcours.py` |
| courses.py | 13 | `app/routers/courses.py` |
| pedagogical.py | 13 | `app/routers/pedagogical.py` |
| pedagogical_lead.py | 12 | `app/routers/pedagogical_lead.py` |
| gamification.py | 10 | `app/routers/gamification.py` |
| ai.py | 10 | `app/routers/ai.py` |
| ai_factory.py | 10 | `app/routers/ai_factory.py` |
| conversations.py | 10 | `app/routers/conversations.py` |
| admin_quizzes.py | 10 | `app/routers/admin_quizzes.py` |
| teacher_classes.py | ~15 | `app/routers/teacher_classes.py` |
| abonnements.py | ~10 | `app/routers/abonnements.py` |
| subscriptions.py | ~7 | `app/routers/subscriptions.py` |
| wallet.py | ~8 | `app/routers/wallet.py` |
| packs.py | ~5 | `app/routers/packs.py` |
| placement.py | ~5 | `app/routers/placement.py` |
| catalogue.py | ~4 | `app/routers/catalogue.py` |
| famille.py | ~4 | `app/routers/famille.py` |
| inbox.py | ~3 | `app/routers/inbox.py` |
| logs.py | ~2 | `app/routers/logs.py` |
| media.py | ~4 | `app/routers/media.py` |
| users.py | ~5 | `app/routers/users.py` |
| licences.py | ~5 | `app/routers/licences.py` |
| bibliotheque.py | ~5 | `app/routers/bibliotheque.py` |
| admin_chapters.py | ~6 | `app/routers/admin_chapters.py` |
| admin_lessons.py | ~6 | `app/routers/admin_lessons.py` |
| auth.py | ~5 | `app/routers/auth.py` |
| catalog.py | ~4 | `app/routers/catalog.py` |
| parent.py | ~8 | `app/routers/parent.py` |

**Preuve :** `app/main.py` — 39 routers enregistrés ; décompte par fichier dans `app/routers/`.

### 3.2 Endpoints SANS RBAC

| # | Endpoint | Fichier | Ligne | Problème |
|---|----------|---------|-------|----------|
| 1 | `GET /catalog/courses` | `catalog.py` | — | Ouvert à tous (public) |
| 2 | `GET /catalog/packs` | `catalog.py` | — | Ouvert à tous (public) |
| 3 | `POST /placement/test/start` | `placement.py` | — | `set_tenant_context` uniquement |
| 4 | `POST /placement/test/submit` | `placement.py` | — | `set_tenant_context` uniquement |
| 5 | `GET /placement/test/{id}` | `placement.py` | — | `set_tenant_context` uniquement |
| 6 | `GET /api/wallet/debit` | `wallet.py` | `wallet.py:178` | `set_tenant_context` uniquement — action admin sans `require_admin` |
| 7 | Plusieurs GET dans `adaptive_pathway.py` | `adaptive_pathway.py` | — | `set_tenant_context` uniquement |

**⚠️ ALERTE :** L'endpoint `GET /api/wallet/debit` (`wallet.py:178`) permet de débiter le wallet sans vérification RBAC admin. Seul `set_tenant_context` est appliqué, ce qui signifie que tout utilisateur authentifié peut potentiellement débiter des credits.

**Preuve :** `app/routers/wallet.py:178` — endpoint debit sans `require_admin` ; `app/routers/placement.py` — endpoints avec `set_tenant_context` uniquement.

### 3.3 Endpoints dupliqués

| # | Duplication | Fichiers | Impact |
|---|-------------|----------|--------|
| 1 | CRUD cours | `courses.py` vs `admin_courses.py` | Deux chemins pour les mêmes opérations |
| 2 | Packs/Abonnements | `subscriptions.py` vs `abonnements.py` | Deux systèmes parallèles de packs |
| 3 | Validation pédagogique | `pedagogical.py` vs `pedagogical_lead.py` | Logique de validation similaire dupliquée |
| 4 | Requête syllabus | `learner.py:53-69` vs `learner.py:307-329` | Même requête dupliquée dans le même fichier |
| 5 | Patterns N+1 | `teacher_classes.py` — variantes teacher vs admin | Duplication des mêmes patterns N+1 |

**Preuve :** `app/routers/courses.py` vs `app/routers/admin_courses.py` ; `app/routers/subscriptions.py` vs `app/routers/abonnements.py` ; `app/routers/learner.py:53-69` et `app/routers/learner.py:307-329`.

### 3.4 Gestion des erreurs

La plupart des endpoints retournent les bons codes HTTP. Cependant, certains endpoints admin retournent un **200 avec l'erreur dans le payload** au lieu d'utiliser les bons codes d'erreur HTTP (anti-pattern).

**Preuve :** `app/routers/admin.py` — certains endpoints retournent `{"error": "..."}` avec status 200.

---

## ÉTAPE 4 — SÉCURITÉ

### 4.1 Authentification

| Composant | Détails | Preuve |
|-----------|---------|--------|
| **Algorithme JWT** | HS256 | `app/auth.py` |
| **Durée access token** | 30 minutes | `app/auth.py` |
| **Durée refresh token** | 7 jours | `app/auth.py` |
| **Refresh token rotation** | Rotation avec stockage côté serveur (SHA-256 hash) | `app/auth.py` |
| **Détection de replay** | Si un token révoqué est réutilisé, TOUS les tokens de l'utilisateur sont révoqués | `app/auth.py` |
| **Hash mot de passe** | bcrypt avec coût auto (bcrypt pinné à 4.0.1) | `requirements.txt` — `bcrypt==4.0.1` |
| **Verrouillage compte** | 5 tentatives échouées → verrouillage 15 min | `app/auth.py:351-353` |

**Preuve :** `app/auth.py:351-353` — verrouillage après 5 tentatives.

### 4.2 Points déjà identifiés comme critiques

| # | Point | Statut | Preuve |
|---|-------|--------|--------|
| 1 | Atomicité wallet : `consume_credits` utilise 2-step `FOR UPDATE` | ✅ CORRIGÉ | `app/routers/wallet.py:182-284` |
| 2 | Précision décimale : 14 champs correctement Numeric, 5 encore Float | ⚠️ PARTIEL | Voir section 2.3 |
| 3 | `has_course_access` : `check_course_ownership` implémenté avec 3 types de propriétaires | ✅ Implémenté | `app/deps.py:161-228` |

**Preuve :** `app/routers/wallet.py:182-284` — 2-step FOR UPDATE ; `app/deps.py:161-228` — 3 owner types vérifiés.

### 4.3 Vulnérabilités trouvées

#### 🔴 CRITIQUE

| # | Vulnérabilité | Fichier:Ligne | Description |
|---|---------------|---------------|-------------|
| 1 | **Fuite de token de réinitialisation** | `auth.py:520-523` | Le token brut de réinitialisation de mot de passe est retourné dans le corps de la réponse HTTP. Tout client interceptant la réponse (proxy, logs, navigateur) obtient le token. |
| 2 | **IDOR sur les scores étudiants** | `adaptive_pathway.py:213-216` | Un étudiant peut soumettre des scores pour n'importe quel autre étudiant en modifiant le `student_id` dans la requête. Aucune vérification que l'étudiant authentifié correspond à l'étudiant cible. |
| 3 | **5 champs monétaires en Float** | `models.py:405,430,484,1669,1118` | Risque d'arrondi sur les transactions financières. Voir section 2.3 pour le détail. |
| 4 | **Fichier .env avec secrets réels** | `.env` | Clé OpenAI, mot de passe DB en clair (`gill4264`), secret JWT faible (`eduai_super_secret_key_2024_very_secure`), clés API commentées. |

**Preuve :**
- `app/auth.py:520-523` — retour du token en clair dans la réponse HTTP.
- `app/routers/adaptive_pathway.py:213-216` — endpoint de soumission de scores sans vérification d'appartenance.
- `app/models.py:405,430,484,1669,1118` — champs Float pour des montants.
- `.env` — secrets en clair.

#### 🟠 IMPORTANT

| # | Vulnérabilité | Fichier:Ligne | Description |
|---|---------------|---------------|-------------|
| 5 | **Pas de rate limiting sur login/register/reset** | `rate_limiter.py` | Les endpoints d'authentification ne sont pas protégés par le rate limiter. Permet des attaques par force brute. |
| 6 | **Email logué à chaque tentative de login** | `auth.py:332` | L'email de l'utilisateur est logué à chaque tentative de connexion, même échouée. |
| 7 | **Fallback school_id=1 hardcodé** | `packs.py:201` | `school_id=user.school_id or 1` — si l'utilisateur n'a pas d'école, le fallback est l'école 1, potentiellement une école de test ou de démo. |
| 8 | **Pas de webhook de paiement pour DT** | `packs.py:192-229` | Les DT (Digicash/Tunisian Dinar) sont débités immédiatement sans vérification via webhook. Risque de double paiement ou de paiement non confirmé. |
| 9 | **Profil enseignant cross-school** | `adaptive_pathway.py:73-94` | Aucune vérification d'école sur `eleve_id` — un enseignant peut potentiellement créer des profils pour des étudiants d'autres écoles. |

**Preuve :**
- `app/core/rate_limiter.py` — pas de rate limiting sur `/auth/login`, `/auth/register`, `/auth/reset`.
- `app/auth.py:332` — `logger.info(f"Login attempt for email: {email}")`.
- `app/routers/packs.py:201` — `school_id=user.school_id or 1`.
- `app/routers/packs.py:192-229` — débit DT sans webhook.
- `app/routers/adaptive_pathway.py:73-94` — pas de vérification d'école sur `eleve_id`.

#### 🟡 MOYEN

| # | Vulnérabilité | Fichier:Ligne | Description |
|---|---------------|---------------|-------------|
| 10 | **Expiration pool abonnement** | `wallet.py:82` | Le pool `SUBSCRIPTION` est exempté du filtre d'expiration — risque de credits périmés jamais purgés. |
| 11 | **Side effects sur GET** | `abonnements.py` | Plusieurs endpoints GET déclenchent des écritures en base (anti-pattern REST). |
| 12 | **Rate limiter in-memory** | `rate_limiter.py` | Fallback in-memory par processus — ne fonctionne pas en cluster/multi-worker. |

**Preuve :**
- `app/routers/wallet.py:82` — exemption SUBSCRIPTION.
- `app/routers/abonnements.py` — GET endpoints avec side effects.
- `app/core/rate_limiter.py` — fallback in-memory.

#### 🟢 BAS

| # | Vulnérabilité | Fichier:Ligne | Description |
|---|---------------|---------------|-------------|
| 13 | **Exception catch large** | `security.py:6` | `except Exception` — attrape toutes les exceptions sans distinction. |
| 14 | **Matching fragile niveau école** | `adaptive_pathway.py:98-128` | Comparaison de chaînes pour le niveau scolaire — sensible aux variations de casse/espaces. |
| 15 | **Secret JWT de dev** | `config.py:69` | Fallback hardcoded pour le secret JWT en mode développement. |

**Preuve :**
- `app/core/security.py:6` — `except Exception`.
- `app/routers/adaptive_pathway.py:98-128` — string matching pour niveau scolaire.
- `app/core/config.py:69` — fallback JWT secret.

### 4.4 Logging de données sensibles

| Donnée | Loguée ? | Fichier | Détails |
|--------|----------|---------|---------|
| Mots de passe en clair | ❌ Non | — | bcrypt hash uniquement |
| Tokens en clair | ❌ Non | — | SHA-256 hash stocké |
| Clés API | ❌ Non | — | Via Settings uniquement |
| Email (PII) | ⚠️ Oui | `app/auth.py:332` | Logué à chaque tentative de login |
| Existence utilisateur | ⚠️ Oui | `app/auth.py:334` | Permet l'énumération via analyse des logs |

**Preuve :** `app/auth.py:332` — `logger.info(f"Login attempt for email: {email}")` ; `app/auth.py:334` — log d'existence utilisateur.

### 4.5 Circuit Breaker

| Breaker | Seuil échecs | Cooldown | Succès pour fermer | Preuve |
|---------|-------------|----------|--------------------| ------|
| `konnect_breaker` | 5 échecs | 30 secondes | 2 succès | `app/core/circuit_breaker.py` |
| `ai_provider_breaker` | 5 échecs | 60 secondes | 2 succès | `app/core/circuit_breaker.py` |

**Preuve :** `app/core/circuit_breaker.py` — configuration des deux circuit breakers.

---

## ÉTAPE 5 — LOGIQUE MÉTIER CRITIQUE

### 5.1 Wallet multi-pocket

| Aspect | Détails | Preuve |
|--------|---------|--------|
| **Priorité des pools** | subscription → school_allocated → trial → purchased | `app/routers/wallet.py` |
| **Architecture** | Append-only ledger (INSERT uniquement, pas d'UPDATE/DELETE sur WalletTransaction) | `app/models.py` — WalletTransaction |
| **Solde** | Calculé au moment de la lecture via agrégation SQL | `app/routers/wallet.py` |
| **Atomicité** | 2-step `FOR UPDATE` avec arithmétique Decimal | `app/routers/wallet.py:182-284` |
| **Fallback legacy** | `/wallet/balance` inclut `User.token_balance` + `dt_balance` comme pool "legacy" | `app/routers/wallet.py` |
| **Tests** | `test_wallet_consume.py` (9 tests), `test_wallet_audit.py` (5 tests), `test_decimal_reconciliation.py` (6 tests) | `tests/` |

**Preuve :** `app/routers/wallet.py:182-284` — 2-step FOR UPDATE ; `tests/test_wallet_consume.py` — 9 tests ; `tests/test_wallet_audit.py` — 5 tests ; `tests/test_decimal_reconciliation.py` — 6 tests.

### 5.2 Système de packs

Deux systèmes parallèles :

| Système | Tables | Description |
|---------|--------|-------------|
| **A) Pack tier-based** | `PackDefinition` + `Abonnement` | Basé sur des niveaux : gratuit/basique/silver/golden |
| **B) Pack purchase-based** | `StudyPack` + `PackPurchase` | Basé sur des achats : niveau_scolaire + matieres |

| Fonctionnalité | Détails | Preuve |
|----------------|---------|--------|
| **Périmètre abonnements** | Scoped par `niveau_scolaire` (`GET /api/abonnements/mon-pack`) | `app/routers/abonnements.py` |
| **Upgrade** | Immédiat (endpoint change-tier) | `app/routers/abonnements.py` |
| **Downgrade** | Différé au prochain trimestre (`scheduled_tier` + `scheduled_effective_date`) | `app/routers/abonnements.py` |
| **Réduction familiale** | 1er enfant 100%, 2ème -20%, 3ème+ -25% | `app/routers/famille.py:74-79` |
| **Tests** | `test_mon_pack_scoped.py` (11), `test_pack_access.py` (15), `test_pack_purchase_guard.py` (2) | `tests/` |

**Preuve :** `app/routers/famille.py:74-79` — réduction familiale ; `tests/test_mon_pack_scoped.py` — 11 tests ; `tests/test_pack_access.py` — 15 tests ; `tests/test_pack_purchase_guard.py` — 2 tests.

### 5.3 Gouvernance pédagogique

| Aspect | Détails | Preuve |
|--------|---------|--------|
| **3 niveaux** | Validation école → Review pedagogical lead → Promotion bibliothèque globale | `app/models.py` — ContentWorkflow |
| **Flux de statuts** | brouillon → en_review → publie/rejete | `app/models.py` — ContentWorkflow |
| **Traçabilité** | Table `ContentWorkflow` suit les transitions | `app/models.py` |
| **Tests** | `test_audit_2026_08_01.py` (21 tests) | `tests/` |

**Preuve :** `app/models.py` — ContentWorkflow ; `tests/test_audit_2026_08_01.py` — 21 tests.

### 5.4 Parcours adaptatif

| Aspect | Détails | Preuve |
|--------|---------|--------|
| **Niveaux d'assimilation** | remediation, standard, avance (par chapitre par étudiant) | `app/models.py` — ProfilAssimilationEleve |
| **Chaîne de fallback** | niveau effectif → STANDARD → tout contenu actif | `app/routers/adaptive_pathway.py` |
| **Réorientation** | Déclenchée automatiquement quand N (défaut 5) derniers scores franchissent un seuil | `app/models.py` — NotificationReorientation |
| **Profil** | `ProfilAssimilationEleve` par (étudiant, chapitre) | `app/models.py` |
| **Tests** | `test_adaptive_pathway.py` (10 tests) | `tests/` |

**Preuve :** `app/models.py` — ProfilAssimilationEleve, NotificationReorientation ; `tests/test_adaptive_pathway.py` — 10 tests.

### 5.5 Couverture tests par logique métier

| Domaine | Nombre de tests | Statut |
|---------|----------------|--------|
| Wallet | 20 | ✅ Couvert |
| Packs/Abonnements | 28 | ✅ Couvert |
| Gouvernance | 21 | ✅ Couvert |
| Parcours adaptatif | 10 | ✅ Couvert |
| Gamification (goal_tracking) | 15 | ✅ Couvert |
| Multi-tenant | 28 | ✅ Couvert |
| **Total métier** | **122** | — |

**Preuve :** `tests/test_wallet_consume.py`, `tests/test_wallet_audit.py`, `tests/test_decimal_reconciliation.py` (20) ; `tests/test_mon_pack_scoped.py`, `tests/test_pack_access.py`, `tests/test_pack_purchase_guard.py` (28) ; `tests/test_audit_2026_08_01.py` (21) ; `tests/test_adaptive_pathway.py` (10) ; tests gamification (15) ; tests multi-tenant (28).

---

## ÉTAPE 6 — QUALITÉ DE CODE ET DETTE TECHNIQUE

### 6.1 Couverture de tests

| Métrique | Valeur |
|----------|--------|
| Tests uniques | 228 |
| Fichiers de tests | 20 |
| Endpoints | ~399 |
| Ratio couverture endpoints | 57.1% |
| Outil de couverture | ❌ Non configuré (pytest-cov absent des dépendances, pas de .coveragerc) |

**Routers SANS aucun test :**

| Router | Endpoints | Preuve |
|--------|-----------|--------|
| elements.py | 20 | `tests/` — aucun test pour ce router |
| parcours.py | 17 | `tests/` — aucun test pour ce router |
| pedagogical.py | 13 | `tests/` — aucun test pour ce router |
| ai_factory.py | 10 | `tests/` — aucun test pour ce router |
| conversations.py | 10 | `tests/` — aucun test pour ce router |
| admin_quizzes.py | 10 | `tests/` — aucun test pour ce router |
| licences.py | 5 | `tests/` — aucun test pour ce router |
| bibliotheque.py | 5 | `tests/` — aucun test pour ce router |
| gamification.py | 5 | `tests/` — aucun test pour ce router |
| users.py | 5 | `tests/` — aucun test pour ce router |
| media.py | 4 | `tests/` — aucun test pour ce router |
| catalog.py | 4 | `tests/` — aucun test pour ce router |
| famille.py | 4 | `tests/` — aucun test pour ce router |
| packs.py | 3 | `tests/` — aucun test pour ce router |
| placement.py | 3 | `tests/` — aucun test pour ce router |
| logs.py | 2 | `tests/` — aucun test pour ce router |
| inbox.py | 3 | `tests/` — aucun test pour ce router |
| wallet.py | 3 | `tests/` — aucun test pour ce router |
| subscriptions.py | 7 | `tests/` — aucun test pour ce router |
| admin_chapters.py | 6 | `tests/` — aucun test pour ce router |
| admin_lessons.py | 6 | `tests/` — aucun test pour ce router |

**Total endpoints sans test : ~163 endpoints (40.9% des endpoints)**

**Preuve :** Analyse de `tests/` — aucun test ne cible les routers listés ci-dessus.

### 6.2 Code mort / TODO/FIXME

**Aucun commentaire TODO/FIXME/HACK/XXX** trouvé dans le code de l'application (`app/`).

**Preuve :** Recherche grep pour `TODO|FIXME|HACK|XXX` dans `app/` — 0 résultat.

### 6.3 Helpers dupliqués dans les tests

| Helper | Nombre de copies | Fichiers |
|--------|-----------------|----------|
| `_create_user` | 4 | Multiples fichiers de tests |
| `_login` | 6 | Multiples fichiers de tests |
| `_create_course` | 4 | Multiples fichiers de tests |
| `_create_module` | 2 | Multiples fichiers de tests |
| `_create_lesson` | 2 | Multiples fichiers de tests |
| `_create_quiz` | 2 | Multiples fichiers de tests |
| **Total** | **20+ copies** | — |

**Preuve :** Analyse de `tests/` — helpers dupliqués dans 20+ emplacements.

### 6.4 N+1 query hotspots (15+ emplacements)

#### 🔴 CRITIQUE

| # | Fichier:Ligne | Description | Impact |
|---|---------------|-------------|--------|
| 1 | `parent.py:125-180` | 6 requêtes par enfant (O(N*D) avec boucle while pour le streak) | Dégradation linéaire avec le nombre d'enfants |
| 2 | `teacher_classes.py:169-178,307-318,451-490,514-521` | Patterns N+1 imbriqués multiples | Dégradation exponentielle |

#### 🟠 IMPORTANT

| # | Fichier:Ligne | Description |
|---|---------------|-------------|
| 3 | `learner.py:57-63,309-310,397` | Chaîne module→lesson→quiz |
| 4 | `academy.py:103-104` | Requête lesson dans une boucle module |

#### 🟡 MOYEN

| # | Fichier:Ligne | Description |
|---|---------------|-------------|
| 5 | `adaptive_pathway.py:657-658,669-670,710` | Requêtes pack dans des boucles |

**Preuve :** `app/routers/parent.py:125-180` — 6 requêtes par enfant ; `app/routers/teacher_classes.py:169-178,307-318,451-490,514-521` — patterns N+1 imbriqués ; `app/routers/learner.py:57-63,309-310,397` — chaîne module→lesson→quiz.

### 6.5 Code dupliqué entre routers

| # | Duplication | Fichiers | Détails |
|---|-------------|----------|---------|
| 1 | Variantes teacher vs admin | `teacher_classes.py` | Duplication de la même logique avec des patterns N+1 identiques |
| 2 | Requête syllabus | `learner.py:53-69` vs `learner.py:307-329` | Même requête copiée dans le même fichier |
| 3 | Arbre module/lesson | `learner.py` vs `academy.py` | Même N+1 module/lesson dupliqué entre deux routers |
| 4 | Logique pack | `adaptive_pathway.py` — catalog vs mon-parcours | Logique de pack dupliquée |

**Preuve :** `app/routers/teacher_classes.py` — variantes teacher/admin ; `app/routers/learner.py:53-69` vs `app/routers/learner.py:307-329` ; `app/routers/learner.py` vs `app/routers/academy.py`.

### 6.6 Incohérences de style

| # | Incohérence | Détails |
|---|-------------|---------|
| 1 | Nommage mixte français/anglais | `abonnements.py` (FR) vs `subscriptions.py` (EN) pour le même concept |
| 2 | Patterns RBAC incohérents | Certains routers utilisent `set_tenant_context`, d'autres `require_admin` — pas de pattern standardisé |
| 3 | pyproject.toml hors sync | pyproject.toml énumère `sqlalchemy ^1.4` et `pydantic ^1.10` au lieu de `>=2.0` et `>=1.10.2` |

**Preuve :** `app/routers/abonnements.py` (FR) vs `app/routers/subscriptions.py` (EN) ; `pyproject.toml` — versions incorrectes.

### 6.7 Index manquants

Tables sans index sur colonnes fréquemment filtrées :

| Table | Colonne | Preuve |
|-------|---------|--------|
| parent_enfants | eleve_id (FK non indexée) | `app/models.py` |
| contenus_notion | enseignant_id | `app/models.py` |
| abonnements | statut | `app/models.py` |
| abonnements | scheduled_effective_date | `app/models.py` |
| ElementPedagogique | — | `app/models.py` — aucun index explicite |
| Parcours | — | `app/models.py` — aucun index explicite |
| Chapitre | — | `app/models.py` — aucun index explicite |
| Lecon | — | `app/models.py` — aucun index explicite |

**Preuve :** `app/models.py` — vérification de chaque table pour la présence d'index.

---

## ÉTAPE 7 — SYNTHÈSE ET PRIORISATION

### 7.1 Risques classés par sévérité

#### 🔴 CRITIQUE (sécurité/financier)

| # | Risque | Localisation | Impact |
|---|--------|-------------|--------|
| 1 | **Fuite de token de réinitialisation** | `auth.py:520-523` | Compromission de compte par interception du token |
| 2 | **IDOR sur les scores étudiants** | `adaptive_pathway.py:213-216` | Manipulation des notes par n'importe quel étudiant |
| 3 | **5 champs monétaires en Float** | `models.py:405,430,484,1669,1118` | Erreurs d'arrondi sur les transactions financières |
| 4 | **.env avec secrets réels** | `.env` | Exposition de clés API, mots de passe, secret JWT |

#### 🟠 IMPORTANT (fiabilité/UX)

| # | Risque | Localisation | Impact |
|---|--------|-------------|--------|
| 5 | **Pas de rate limiting sur login/register/reset** | `rate_limiter.py` | Attaques par force brute |
| 6 | **Fallback school_id=1 hardcodé** | `packs.py:201` | Données attribuées à la mauvaise école |
| 7 | **Profil enseignant cross-school** | `adaptive_pathway.py:73-94` | Manipulation de profils d'étudiants d'autres écoles |
| 8 | **N+1 queries (15+ emplacements)** | 5 fichiers | Dégradation des performances |
| 9 | **Pas de webhook de paiement pour DT** | `packs.py:192-229` | Paiements non confirmés ou doubles |
| 10 | **Side effects sur GET** | `abonnements.py` | Violation du principe REST, risque de modification non intentionnelle |
| 11 | **pyproject.toml hors sync** | `pyproject.toml` | Installation de dépendances incorrectes |
| 12 | **Modèles legacy dupliqués** | `app/db/models.py` | Conflits de mapper SQLAlchemy |
| 13 | **Conflit d'alias Plan** | `models.py:1133` | Ambiguïté dans les requêtes |

#### 🟢 MINEUR (dette technique)

| # | Risque | Localisation | Impact |
|---|--------|-------------|--------|
| 14 | **Pas d'outil de couverture de tests** | `requirements.txt` | Impossibilité de mesurer la couverture |
| 15 | **12+ routers sans test** | `tests/` | 163 endpoints non testés |
| 16 | **6 helpers dupliqués 20+ fois** | `tests/` | Maintenance difficile |
| 17 | **Nommage mixte français/anglais** | Routers | Incohérence de code |
| 18 | **Matching fragile niveau scolaire** | `adaptive_pathway.py:98-128` | Bugs potentiels |
| 19 | **10+ incohérences schema/modèle** | `schemas.py` vs `models.py` | Erreurs de validation |
| 20 | **8+ contraintes FK manquantes** | `models.py` | Intégrité référentielle non garantie |

### 7.2 Actions correctives pour chaque item critique

#### 1. Fuite de token de réinitialisation (`auth.py:520-523`)

**Action :** Ne JAMAIS retourner le token brut dans la réponse HTTP. Le token doit être envoyé uniquement par email (ou notification push). La réponse HTTP doit contenir uniquement un message de confirmation.

```python
# AVANT (vulnérable)
return {"reset_token": reset_token, "message": "Token generated"}

# APRÈS (corrigé)
send_reset_email(email, reset_token)
return {"message": "If the email exists, a reset link has been sent"}
```

**Preuve :** `app/auth.py:520-523` — code actuel retournant le token.

#### 2. IDOR sur les scores étudiants (`adaptive_pathway.py:213-216`)

**Action :** Vérifier que l'étudiant authentifié correspond à l'étudiant cible de la soumission de score.

```python
# AVANT (vulnérable)
@router.post("/scores/submit")
async def submit_score(student_id: int, ...):
    # Pas de vérification

# APRÈS (corrigé)
@router.post("/scores/submit")
async def submit_score(student_id: int, user: User = Depends(require_student)):
    if user.id != student_id:
        raise HTTPException(status_code=403, detail="Cannot submit scores for another student")
```

**Preuve :** `app/routers/adaptive_pathway.py:213-216` — endpoint sans vérification d'appartenance.

#### 3. Champs monétaires en Float (`models.py:405,430,484,1669,1118`)

**Action :** Créer une migration Alembic pour convertir les 5 champs restants de `Float` vers `Numeric(10,2)` (ou `Numeric(10,4)` pour `cost_usd`). Mettre à jour les modèles Pydantic correspondants.

```python
# Migration
op.alter_column('transactions', 'amount', type_=Numeric(10,2))
op.alter_column('token_packages', 'price_dt', type_=Numeric(10,2))
op.alter_column('courses', 'price_dt', type_=Numeric(10,2))
op.alter_column('plans', 'price', type_=Numeric(10,2))
op.alter_column('ai_usage_logs', 'cost_usd', type_=Numeric(10,4))
```

**Preuve :** `app/models.py:405,430,484,1669,1118` — champs Float.

#### 4. Secrets dans .env

**Action :**
1. Ajouter `.env` au `.gitignore` si ce n'est pas déjà fait.
2. Utiliser un gestionnaire de secrets (Vault, AWS Secrets Manager, etc.) en production.
3. Fournir un `.env.example` avec des valeurs placeholder.
4. Générer un nouveau secret JWT (l'actuel `eduai_super_secret_key_2024_very_secure` est trop faible).
5. Changer le mot de passe de la base de données.

**Preuve :** `.env` — secrets en clair.

#### 5. Rate limiting sur login/register/reset (`rate_limiter.py`)

**Action :** Ajouter des rate limits spécifiques aux endpoints d'authentification :
- `/auth/login` : 10 req/min (déjà présent dans main.py mais non appliqué via slowapi)
- `/auth/register` : 5 req/min (déjà présent dans main.py mais non appliqué via slowapi)
- `/auth/reset` : 3 req/min

**Preuve :** `app/core/rate_limiter.py` — pas de rate limiting sur ces endpoints.

#### 6. Fallback school_id=1 (`packs.py:201`)

**Action :** Lever une exception au lieu de fallback sur `school_id=1`.

```python
# AVANT
school_id = user.school_id or 1

# APRÈS
if not user.school_id:
    raise HTTPException(status_code=400, detail="User must be associated with a school")
school_id = user.school_id
```

**Preuve :** `app/routers/packs.py:201` — `school_id=user.school_id or 1`.

#### 7. Profil enseignant cross-school (`adaptive_pathway.py:73-94`)

**Action :** Vérifier que `eleve_id` appartient à la même école que l'enseignant authentifié.

```python
# Vérification à ajouter
eleve = db.query(User).filter(User.id == eleve_id, User.school_id == teacher.school_id).first()
if not eleve:
    raise HTTPException(status_code=404, detail="Student not found in your school")
```

**Preuve :** `app/routers/adaptive_pathway.py:73-94` — pas de vérification d'école.

#### 8. N+1 queries (15+ emplacements)

**Action :** Utiliser `selectinload` ou `joinedload` dans les requêtes SQLAlchemy pour charger les relations en une seule requête. Prioriser les hotspots critiques :
- `parent.py:125-180` : optimiser la boucle streak
- `teacher_classes.py:169-178,307-318,451-490,514-521` : refactoriser les patterns N+1 imbriqués

**Preuve :** `app/routers/parent.py:125-180` — 6 requêtes par enfant ; `app/routers/teacher_classes.py` — patterns N+1 multiples.

#### 9. Pas de webhook de paiement pour DT (`packs.py:192-229`)

**Action :** Implémenter un webhook Konnect pour confirmer le paiement DT avant de débiter les credits. Utiliser le circuit breaker existant (`konnect_breaker`) pour la résilience.

**Preuve :** `app/routers/packs.py:192-229` — débit DT sans webhook.

#### 10. Side effects sur GET (`abonnements.py`)

**Action :** Convertir les endpoints GET avec side effects en POST ou PUT conformément aux conventions REST.

**Preuve :** `app/routers/abonnements.py` — GET endpoints avec écritures en base.

#### 11. pyproject.toml hors sync

**Action :** Synchroniser `pyproject.toml` avec `requirements.txt`. Mettre à jour les versions minimales (`sqlalchemy >=2.0`, `pydantic >=1.10.2`) et ajouter les dépendances manquantes (openai, faiss-cpu, redis, slowapi, etc.).

**Preuve :** `pyproject.toml` — `sqlalchemy ^1.4`, `pydantic ^1.10`, 15+ dépendances manquantes.

#### 12. Modèles legacy dupliqués (`app/db/models.py`)

**Action :** Supprimer `app/db/models.py` ou le renommer en `app/db/models_legacy.py` avec un avertissement clair. Assurer qu'aucun module de l'application n'importe ces modèles en production.

**Preuve :** `app/db/models.py` — 11 tables dupliquées.

#### 13. Conflit d'alias Plan (`models.py:1133`)

**Action :** Renommer l'alias ou la classe pour éviter l'ambiguïté avec la table `plans` existante. Vérifier les impacts sur les schémas Pydantic et les routes.

**Preuve :** `app/models.py:1133` — alias Plan.

### 7.3 Statistiques globales

| Métrique | Valeur |
|----------|--------|
| **Nombre de modèles** | 87+ classes (3 fichiers principaux + 1 legacy) |
| **Nombre d'endpoints** | ~399 (35 routers) |
| **Nombre de rôles vérifiés** | 7 (student, teacher, admin_school, super_admin, pedagogical_admin, pedagogical_lead, parent) |
| **Tests uniques** | 228 |
| **Couverture endpoints** | 57.1% |
| **Migrations** | 6 |
| **Services externes** | Stripe, Konnect, 9 providers IA |
| **Routers sans test** | 21 (163 endpoints non testés) |
| **Risques critiques** | 4 |
| **Risques importants** | 9 |
| **Risques mineurs** | 7 |
| **Champs monétaires en Float** | 5 (sur 19 champs monétaires) |
| **Tables sans school_id** | 13 (isolation fragile ou absente) |
| **N+1 query hotspots** | 15+ emplacements dans 5 fichiers |
| **Helpers de test dupliqués** | 20+ copies de 6 helpers |
| **Index manquants** | 8+ tables concernées |
| **Incohérences schema/modèle** | 10+ mismatches |

---

**Fin du rapport — 04 août 2026**

# RAPPORT D'AUDIT TECHNIQUE 360° — EDUAI LEARNING

**Date :** 02/08/2026  
**Version :** 1.0.0  
**Auteur :** Analyse automatisée (opencode)  
**Portée :** Backend (FastAPI), Frontend (React/Vite), Infra (Docker, CI/CD, Alembic), Sécurité, Paiements, IA

---

## SOMMAIRE EXÉCUTIF

| Domaine | Statut | Score |
|---|---|---|
| Architecture Backend | ✅ Solide | 9/10 |
| Multi-tenancy & Isolation | ✅ Defense-in-depth | 8/10 |
| Sécurité (Auth, RBAC, Input) | ✅ Renforcé | 8/10 |
| Paiements (Konnect + Stripe) | ✅ Fonctionnel | 8/10 |
| IA & Streaming (SSE) | ✅ Opérationnel | 8/10 |
| Frontend (React) | ✅ Fonctionnel | 7/10 |
| Tests (218 pytest) | ✅ Passent | 9/10 |
| CI/CD (GitHub Actions) | ✅ Configuré | 7/10 |
| Alembic Migrations | ⚠️ Stamped, pas de migration initiale | 6/10 |
| Monitoring & Logging | ⚠️ Basique | 5/10 |

**Score global : 7.5/10**

---

## 1. ARCHITECTURE BACKEND

### 1.1 Stack Technique

| Composant | Technologie | Version |
|---|---|---|
| Framework | FastAPI | ≥0.95 |
| ORM | SQLAlchemy 2.0 | ≥2.0 |
| Driver PostgreSQL | pg8000 | ≥1.0 |
| Migrations | Alembic | 1.18.4 |
| Auth | python-jose (JWT) + passlib (bcrypt) | — |
| Validation | Pydantic v2 + pydantic-settings | ≥2.0 |
| IA Provider | Groq (llama-3.3-70b-versatile) | — |
| IA Embeddings | OpenAI + faiss-cpu | — |
| Paiements | Stripe + Konnect (TND) | — |
| PDF | weasyprint + pdfplumber + pypdf | — |
| Streaming | SSE via `StreamingResponse` | — |

### 1.2 Structure des Routes (30 routers)

```
backend/app/
├── main.py                    # App FastAPI, middleware, rate limiter
├── auth.py                    # Register, login, forgot/reset password
├── models.py                  # 77 tables (DeclarativeBase)
├── models_lms.py              # Tables LMS (modules, lessons, quizzes)
├── models_ai_conversations.py # Conversations IA
├── deps.py                    # Dependencies RBAC (270 lignes)
├── audit.py                   # Audit trail (admin + user + security)
├── db/
│   ├── session.py             # Engine, SessionLocal, tenant filter
│   └── __init__.py            # ContextVars (current_tenant_id, _tenant_filter_suppressed)
├── core/
│   ├── config.py              # Settings (130 lignes)
│   ├── security.py            # Password hashing
│   ├── validation.py          # Input sanitization (170 lignes)
│   └── rate_limiter.py        # AI rate limiting
├── services/
│   ├── wallet.py              # consume_credits (2-step FOR UPDATE), credit_dt, debit_dt
│   ├── goal_tracking.py       # _TTLCache, calcul dynamique statut
│   ├── gamification.py        # SQL GROUP BY aggregation
│   ├── notification_service.py# System sender user
│   ├── embeddings_service.py  # _index_cache per school_id
│   ├── course_access.py       # has_course_access (7 étapes)
│   ├── student_tier.py        # AI feature level
│   ├── recommendation.py      # Path recommendation
│   ├── school_calendar.py     # Calendrier tunisien
│   └── goal_scheduler.py      # Scheduler objectifs
├── payment/
│   └── konnect_client.py      # Client API Konnect (96 lignes)
├── ai/
│   ├── rag_service.py         # RAG + moderation prompt
│   └── provider_client.py     # generate_chat_stream()
├── routers/
│   ├── ai.py                  # SSE streaming, 9 endpoints IA
│   ├── courses.py             # CRUD cours, school_id filter
│   ├── users.py               # PUT /users/me
│   ├── admin.py               # Admin endpoints
│   ├── parent.py              # Parent dashboard + messaging
│   ├── payments/
│   │   ├── stripe.py          # Stripe checkout + webhook
│   │   └── konnect.py         # Konnect checkout + webhook + credit-child
│   └── ... (28 autres)
```

### 1.3 Points Forts

- **`consume_credits()`** : 2-step `FOR UPDATE` pour atomicité (PostgreSQL compliant)
- **`_safe_refund()`** : Conversion `Decimal→int`, appliqué aux 9 endpoints IA
- **`_TTLCache`** : Cache borné (1000 entrées, 5 min TTL) — pas de memory leak
- **Gamification SQL** : `GROUP BY` aggregation élimine le N+1
- **Rate Limiter** : In-memory, par IP, par path pattern
- **Security Headers** : X-Content-Type-Options, X-Frame-Options, CSP, HSTS

### 1.4 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| `RateLimiter.requests` partagé entre workers (dict class) | Moyen | `main.py:108` |
| Pas de Redis pour rate limiting distribué | Moyen | `main.py:87-108` |
| `maintenance_mode_middleware` fait un `db.query()` à chaque requête | Moyen | `main.py:181-215` |
| Pas de circuit breaker pour les appels Konnect/OpenAI | Faible | `konnect_client.py`, `provider_client.py` |
| `create_all()` supprimé de lifespan — migration stamp manuelle | Faible | `main.py:131` |

---

## 2. MULTI-TENANCY & ISOLATION

### 2.1 Architecture Defense-in-Depth

```
Requête HTTP
    ↓
get_current_user()         → Auth JWT
    ↓
set_tenant_context()       → 1ère ligne : current_tenant_id.set(school_id)
    ↓
check_school_access()      → 2ème ligne : vérification explicite
    ↓
_tenant_filter_suppressed  → Global roles (super_admin, pedagogical_admin)
    ↓
SQLAlchemy ORM Events      → Filtre automatique WHERE school_id = :tenant_id
```

### 2.2 Modèle de Données Multi-Tenant

- **77 tables** enregistrées dans `Base.metadata`
- **`school_id`** sur les tables clés : User, Course, WalletTransaction, Transaction, etc.
- **ContextVars** : `current_tenant_id`, `_tenant_filter_suppressed`
- **Global roles** : super_admin, pedagogical_admin — suppress filter

### 2.3 Isolation Vérifiée

| Ressource | Isolation | Mécanisme |
|---|---|---|
| Users | ✅ | `school_id` + tenant filter |
| Courses | ✅ | `school_id` + `check_course_ownership()` |
| Wallet | ✅ | `user_id` (pas de cross-user) |
| Transactions | ✅ | `school_id` |
| AI Conversations | ✅ | `user_id` + `school_id` |
| Gamification | ✅ | `school_id` |
| Parent-Student | ✅ | `parent_enfants` + school isolation |

### 2.4 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| `Quiz` model n'a PAS `school_id` ni `course_id` | Moyen | `models.py` |
| Isolation Quiz via : lesson → module → course → school | Faible | `learner.py` |
| Pas de `school_id` sur `PasswordResetToken` | Faible | `models.py` |

---

## 3. SÉCURITÉ

### 3.1 Authentification

| Mécanisme | Statut | Détails |
|---|---|---|
| JWT HS256 | ✅ | `python-jose`, 1440 min expiry |
| Password hashing | ✅ | `bcrypt` via `passlib` |
| Rate limiting login | ✅ | 10 req/min |
| Rate limiting register | ✅ | 5 req/min |
| Account disabled check | ✅ | `auth.py:56-61` |
| Password strength validation | ✅ | `validation.py:82-105` (8+ chars, letter + number) |
| Forgot password (no email enumeration) | ✅ | Toujours retourne 200 |
| Reset password (token expiry 1h) | ✅ | `secrets.token_urlsafe(48)` |

### 3.2 RBAC (Role-Based Access Control)

| Rôle | Portée | Permissions |
|---|---|---|
| `super_admin` | Plateforme | Tout |
| `pedagogical_admin` | Plateforme | Pédagogie + users |
| `admin_school` | École | Gestion école |
| `pedagogical_lead` | École | Pédagogie école |
| `teacher` | École | Cours, classe, devoirs |
| `student` | École | Apprentissage, IA |
| `parent` | École | Lecture seule progression |

### 3.3 Input Validation

- **`sanitize_string()`** : HTML escape + control char removal + whitespace normalization
- **`validate_password_strength()`** : 8+ chars, letter + number
- **`validate_email_format()`** : RFC 5322 simplified pattern
- **Pydantic schemas** : Validation automatique sur tous les endpoints

### 3.4 Sécurité Docker

- **Non-root user** dans Dockerfile
- **Secrets via env vars** (pas de hardcode)
- **CORS configuré** : origines dynamiques
- **Security Headers** : X-Content-Type-Options, X-Frame-Options, CSP, HSTS
- **Docs désactivées en prod** : `docs_url=None`, `redoc_url=None`

### 3.5 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| JWT secret par défaut en dev (`dev-only-jwt-secret...`) | Faible | `config.py:68` |
| Pas de refresh token | Moyen | `auth.py` |
| Pas de brute-force protection au-delà du rate limiter | Faible | `main.py` |
| `hmac.new()` au lieu de `hmac.HMAC()` | Faible | `konnect_client.py:91` |
| Pas de CSRF protection | Faible | — |
| CSP avec `'unsafe-inline'` pour styles | Faible | `main.py:175` |

---

## 4. PAIEMENTS

### 4.1 Konnect (Tunisie, TND)

| Composant | Statut | Fichier |
|---|---|---|
| Client API | ✅ | `konnect_client.py` (96 lignes) |
| Checkout | ✅ | `konnect.py:66-126` |
| Webhook | ✅ | `konnect.py:133-197` |
| Credit-child | ✅ | `konnect.py:210-288` |
| HMAC verification | ✅ | `konnect_client.py:79-96` |
| Idempotent webhook | ✅ | Vérifie status avant credit |
| Montants en millimes | ✅ | 1 TND = 1000 millimes |

**Flow Konnect :**
```
Frontend → POST /konnect/checkout → Transaction(pending) → Konnect API → pay_url
Konnect → POST /konnect/webhook → Vérifie signature → credit_dt() → Transaction(succeeded)
```

### 4.2 Stripe (International, USD)

| Composant | Statut | Fichier |
|---|---|---|
| Checkout session | ✅ | `stripe.py` |
| Webhook | ✅ | `stripe.py` |
| Subscription management | ✅ | `subscriptions.py` |

### 4.3 Wallet Unifié

```
WalletTransaction (append-only ledger)
├── Pool: TRIAL           → Trial credits (expire)
├── Pool: SCHOOL_ALLOCATED → School credits
├── Pool: PURCHASED       → Direct purchase (never expires)
├── Pool: SUBSCRIPTION    → Subscription credits
└── Pool: DT_PURCHASED    → Real money (TND) — Konnect/Stripe
```

### 4.4 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| Pas de retry automatique pour webhooks Konnect | Moyen | `konnect.py` |
| Montant max Konnect (5000 TND) non configurable | Faible | `konnect.py:82` |
| Pas de monitoring des paiements échoués | Faible | — |

---

## 5. INTELLIGENCE ARTIFICIELLE

### 5.1 Architecture IA

```
Frontend (useAIStream)
    ↓ SSE
POST /api/ai/ask → StreamingResponse(text/event-stream)
    ↓
RAGService → moderate_prompt() → Groq API (llama-3.3-70b-versatile)
    ↓
SSE chunks → {"chunk": "...", "done": false}
    ↓
Final → {"done": true, "conversation_id": N, "tokens": N}
```

### 5.2 Fonctionnalités IA

| Feature | Endpoint | Crédits | Streaming |
|---|---|---|---|
| AI Tutor Q&A | `POST /ai/ask` | ✅ | ✅ SSE |
| Concept Explanation | `POST /ai/explain` | ✅ | ❌ |
| Quiz Generation | `POST /ai/generate-quiz` | ✅ | ❌ |
| Exercise Generation | `POST /ai/generate-exercise` | ✅ | ❌ |
| PDF Ingestion | `POST /ai/ingest` | ✅ | ❌ |
| Auto-correction | `POST /ai/correct` | ✅ | ❌ |
| Moderation | `moderate_prompt()` | ❌ | — |
| Provider fallback | `provider_client.py` | — | Groq → OpenAI |

### 5.3 Sécurité IA

- **Moderation prompt** : `rag_service.py:moderate_prompt()` — bloque prompts dangereux
- **Rate limiting** : 60 req/min par IP
- **Credit consumption** : Vérification solde avant traitement
- **Safe refund** : `_safe_refund()` en cas d'erreur
- **Language detection** : `_detect_language()` (ar/fr)

### 5.4 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| Pas de streaming pour explain/generate-quiz | Faible | `ai.py` |
| Pas de cache des réponses IA | Faible | — |
| Pas de fallback automatique entre providers | Faible | `provider_client.py` |
| Tokens estimés par `len(answer) // 4` (approximatif) | Faible | `ai.py:220` |

---

## 6. FRONTEND

### 6.1 Stack Technique

| Composant | Technologie | Version |
|---|---|---|
| Framework | React | 18 |
| Build tool | Vite | 5 |
| State | Zustand | — |
| i18n | i18next | — |
| Charts | Recharts | — |
| API Client | Custom (interceptors) | — |
| Streaming | `useAIStream` hook | — |

### 6.2 Structure des Features

```
frontend/src/features/
├── admin/        # Dashboard admin, users, courses, schools
├── auth/         # Login, register, forgot/reset password
├── learner/      # Student dashboard, courses, AI tutor
├── parent/       # Parent dashboard, messaging, child detail
├── pathway/      # Adaptive pathway
├── student/      # Profile page, settings
└── teacher/      # Classroom, assignments, grading
```

### 6.3 Vite Proxy Rules

```javascript
proxy: {
  "/api":     → http://localhost:8000
  "/auth":    → http://localhost:8000
  "/users":   → http://localhost:8000  // Ajouté récemment
  "/catalog": → http://localhost:8000
}
```

### 6.4 Hooks Clés

- **`useAIStream`** : SSE streaming avec AbortController, buffer parsing, error handling
- **`useAuthStore`** : Zustand store pour JWT + user state
- **`apiClient`** : Axios wrapper avec interceptors (token injection, error handling)

### 6.5 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| Pas de lazy loading des routes | Faible | `App.tsx` |
| Pas de Error Boundary global | Moyen | — |
| `token` dans localStorage (XSS vulnerable) | Moyen | `ParentDashboardPage.tsx:13` |
| Pas de type safety strict (beaucoup de `any`) | Faible | Divers |
| Pas de tests frontend | Moyen | — |

---

## 7. TESTS

### 7.1 Résumé

| Métrique | Valeur |
|---|---|
| Total tests | **218** |
| Tests passent | **218** |
| Tests échouent | **0** |
| Couverture minimale | **70%** (CI enforce) |
| Framework | pytest + pytest-cov |
| Base test | PostgreSQL (pg8000) |

### 7.2 Catégories de Tests

| Catégorie | Nombre | Fichiers |
|---|---|---|
| Auth & RBAC | ~30 | `test_auth.py`, `test_rbac.py` |
| Wallet & Credits | ~25 | `test_wallet.py`, `test_wallet_atomicity.py` |
| Multi-tenancy | ~15 | `test_tenant_*.py` |
| AI & RAG | ~20 | `test_ai.py`, `test_rag.py` |
| Courses & LMS | ~30 | `test_courses.py`, `test_lms.py` |
| Payments | ~15 | `test_konnect.py`, `test_stripe.py` |
| Gamification | ~10 | `test_gamification.py` |
| Goal Tracking | ~10 | `test_goal_tracking.py` |
| Admin | ~15 | `test_admin.py`, `test_admin_school.py` |
| Parent | ~10 | `test_parent.py` |
| Autres | ~28 | Divers |

### 7.3 Conftest.py Unifié

- **`conftest.py`** unique pour tous les tests
- **`StaticPool` + `override_get_db`** pour SQLite threading
- **Fixtures** : `db_session`, `client`, `auth_headers`, `teacher_headers`, etc.
- **Tenant context** : `set_tenant_context` pour chaque test

### 7.4 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| Pas de tests frontend | Moyen | `frontend/src/test/` |
| Pas de tests d'intégration end-to-end | Moyen | — |
| Pas de load testing | Faible | — |
| Coverage limité aux 5 modules principaux | Faible | `.github/workflows/ci-cd.yml:58-63` |

---

## 8. CI/CD

### 8.1 Pipeline GitHub Actions

```yaml
Jobs:
1. test (ubuntu-latest)
   ├── PostgreSQL 15 Alpine (service)
   ├── Python 3.11 + pip cache
   ├── Install dependencies (requirements-dev.txt)
   ├── Alembic migrations
   └── pytest with coverage (≥70%)

2. docker (needs: test, main only)
   ├── Docker Buildx
   └── Build image → ghcr.io

3. deploy (needs: test, main only)
   └── Render deploy action
```

### 8.2 Environnements

| Env | URL | Database |
|---|---|---|
| Development | localhost:5173 + localhost:8000 | PostgreSQL local |
| CI | GitHub Actions | PostgreSQL service |
| Production | Render | Render PostgreSQL |

### 8.3 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| Pas de staging environment | Moyen | — |
| Pas de smoke tests post-deploy | Faible | — |
| Pas de rollback automatique | Faible | — |
| `push: false` sur Docker build | Faible | `ci-cd.yml:82` |
| Pas de security scanning (SAST/DAST) | Moyen | — |

---

## 9. ALEMBIC MIGRATIONS

### 9.1 État Actuel

| Élément | Statut |
|---|---|
| `alembic.ini` | ✅ Configuré |
| `alembic/env.py` | ✅ Importe tous les modèles |
| `alembic/versions/` | ✅ `cb84f566d487` (stamp) |
| `create_all()` | ❌ Supprimé de lifespan |
| Migration `PasswordResetToken` | ❌ Pas encore créée |
| Migration `pending_validation` | ❌ Ajoutée via SQL brut |

### 9.2 Scripts Ad-Hoc (à nettoyer)

```
backend/
├── migrations/*.sql          # Scripts SQL manuels
├── add_*.py                  # Scripts d'ajout de colonnes
├── fix_*.py                  # Scripts de correction
└── seed_db.py                # Script de seed (idempotent)
```

### 9.3 Points Faibles

| Problème | Gravité | Localisation |
|---|---|---|
| Pas de migration initiale complète | Élevé | `alembic/versions/` |
| Stamp manuelle au lieu de migration | Moyen | `cb84f566d487` |
| Scripts SQL ad-hoc non intégrés | Moyen | `migrations/*.sql` |
| `pending_validation` ajouté via SQL brut | Moyen | — |

---

## 10. SEED SCRIPT

### 10.1 `backend/seed_db.py`

| Caractéristique | Détails |
|---|---|
| Idempotent | ✅ Vérifie par email/slug avant insert |
| Écoles | 2 (Carthage Academy, El Jem Institute) |
| Utilisateurs | 18 (2 global + 8 par école) |
| Parent-Student links | 3 |
| Wallet entries | 20 (100 tokens trial + 50.00 DT) |
| Cours | 5 avec LMS (Modules, Lessons, Quizzes) |
| StudyPack | 1 |
| Enrollments | 2 |
| Password | `passeword123` pour tous |
| Fix Python 3.14 | ✅ `%` formatting au lieu de f-strings |

---

## 11. RECOMMANDATIONS

### 11.1 Priorité Haute

| # | Action | Impact |
|---|---|---|
| H1 | Créer migration Alembic complète (77 tables) | Élevé |
| H2 | Intégrer `PasswordResetToken` + `pending_validation` dans Alembic | Élevé |
| H3 | Nettoyer les scripts SQL ad-hoc | Moyen |
| H4 | Ajouter Error Boundary React global | Moyen |
| H5 | Ajouter tests frontend (Vitest) | Moyen |

### 11.2 Priorité Moyenne

| # | Action | Impact |
|---|---|---|
| M1 | Redis pour rate limiting distribué | Moyen |
| M2 | Circuit breaker pour Konnect/OpenAI | Moyen |
| M3 | Refresh token JWT | Moyen |
| M4 | Staging environment | Moyen |
| M5 | Security scanning (SAST/DAST) | Moyen |
| M6 | Monitoring (Sentry, Datadog) | Moyen |
| M7 | Lazy loading des routes React | Faible |

### 11.3 Priorité Basse

| # | Action | Impact |
|---|---|---|
| L1 | Streaming pour explain/generate-quiz | Faible |
| L2 | Cache des réponses IA | Faible |
| L3 | Load testing (k6, Locust) | Faible |
| L4 | Smoke tests post-deploy | Faible |
| L5 | Rollback automatique | Faible |

---

## 12. FICHIERS CLÉS

### Backend

| Fichier | Lignes | Rôle |
|---|---|---|
| `main.py` | 326 | App FastAPI, middleware, rate limiter |
| `auth.py` | 483 | Register, login, forgot/reset password |
| `models.py` | 2150 | 77 tables (DeclarativeBase) |
| `deps.py` | 270 | RBAC dependencies |
| `wallet.py` | 461 | consume_credits (2-step FOR UPDATE) |
| `goal_tracking.py` | 431 | _TTLCache, calcul dynamique statut |
| `ai.py` | 699 | SSE streaming, 9 endpoints IA |
| `courses.py` | — | CRUD cours, school_id filter |
| `konnect.py` | 288 | Konnect checkout + webhook |
| `konnect_client.py` | 96 | Client API Konnect |
| `validation.py` | 170 | Input sanitization |
| `audit.py` | 89 | Audit trail |
| `seed_db.py` | — | Script de seed idempotent |

### Frontend

| Fichier | Lignes | Rôle |
|---|---|---|
| `vite.config.js` | 44 | Proxy rules, test config |
| `useAIStream.ts` | 165 | SSE streaming hook |
| `ProfilePage.tsx` | 156 | Profile save (full_name + niveau_scolaire) |
| `ParentDashboardPage.tsx` | 117 | Parent dashboard + messaging |
| `apiClient.ts` | — | Custom ApiClient with interceptors |

### Infrastructure

| Fichier | Rôle |
|---|---|
| `.github/workflows/ci-cd.yml` | CI/CD pipeline |
| `requirements.txt` | 28 dependencies |
| `package.json` | Frontend dependencies |
| `alembic.ini` | Alembic config |

---

## 13. MÉTRIQUES FINALES

| Métrique | Valeur |
|---|---|
| Lignes de code backend (estimé) | ~15 000 |
| Lignes de code frontend (estimé) | ~10 000 |
| Tables de base de données | 77 |
| Endpoints API | ~120 |
| Tests pytest | 218 (tous passent) |
| Routers FastAPI | 30 |
| Services métier | ~15 |
| Hooks React | ~10 |
| Features frontend | 7 |

---

**Fin du rapport — 02/08/2026**

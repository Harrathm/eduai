# TECHNICAL SPECIFICATION — EDUAI Learning

> Document d'architecture technique — le "comment on le construit"
> Ce document couvre les choix d'ingénierie, pas les règles métier ni l'installation.
> Mis à jour : 2026-08-01

---

# PARTIE 1 — المواصفات التقنية (العربية)

---

## 1. نظرة عامة على البنية المعمارية

### 1.1 مكونات النظام

يتكون نظام EDUAI Learning من خمسة مكونات رئيسية:

```
┌─────────────────────────────────────────────────────┐
│                    المتصفح/التطبيق                    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  واجهة الويب  │  │  تطبيق Flutter │  │  API REST  │ │
│  │  React/Vite   │  │  Mobile       │  │  FastAPI   │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
└─────────┼──────────────────┼────────────────┼────────┘
          │                  │                │
          ▼                  ▼                ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.11+)          │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐ │
│  │ Routers  │ │ Services │ │ AI Engine │ │ Models │ │
│  │ (27 ملف)│ │          │ │ (RAG)     │ │ (50+)  │ │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘ └───┬────┘ │
└───────┼───────────┼─────────────┼───────────┼──────┘
        │           │             │           │
        ▼           ▼             ▼           ▼
┌─────────────────────────────────────────────────────┐
│              PostgreSQL 15 (القاعدة البيانات)        │
│  ┌──────────────────────────────────────────────┐   │
│  │  50+ جدول — multi-tenant via school_id       │   │
│  │  Numeric(10,2) للحقول المالية                  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 1.2 الاتصال بين المكونات

- **Frontend ↔ Backend**: REST API عبر HTTP/HTTPS. لا يوجد WebSocket. streaming عبر Server-Sent Events (SSE) للـ AI.
- **Backend ↔ DB**: SQLAlchemy ORM مع pg8000 driver.
- **Backend ↔ AI**: API calls مباشرة (OpenAI-compatible clients) مع retry logic.
- **Backend ↔ AI/RAG**: TF-IDF (scikit-learn) للاسترجاع — FAISS غير مستخدم فعلياً رغم وجوده في requirements.txt.

### 1.3 المبررات المعمارية

- **为什么不 fine-tuning بدلاً من RAG؟**: السبب غير موثق في المستودع. RAG يوفر تكلفة أقل ويسمح بتحديث المحتوى دون إعادة تدريب.
- **لماذا PostgreSQL؟**: السبب غير موثق في المستودع. PostgreSQL يوفر row-level security و JSON support و Numeric precision.

---

## 2. المكدس التقني التفصيلي

### 2.1 الخادم (Backend)

| المكوّن | التفاصيل |
|---------|---------|
| Framework | FastAPI ≥ 0.95.0 |
| ORM | SQLAlchemy ≥ 2.0 (لكن يُستخدم مع Base.metadata.create_all — لا Alembic) |
| Driver قاعدة البيانات | pg8000 ≥ 1.0.0 |
| التشفير | python-jose ≥ 3.3.0 (HS256 JWT) |
| تشفير كلمات المرور | bcrypt 4.0.1 عبر passlib ≥ 1.7.4 |
| التحقق من الإدخال | pydantic ≥ 1.10.2, pydantic-settings ≥ 2.0 |
| Rate Limiting | slowapi ≥ 0.1.9 + Redis اختياري |
| الجدولة | APScheduler (BackgroundScheduler) — غير موجود في requirements.txt |
| الملفات | aiofiles ≥ 23.0.0 |
| التقارير | weasyprint ≥ 60.0, python-docx ≥ 1.1.0 |

**ملاحظة مهمة**: `bcrypt==4.0.1` مثبت بدقة. `apscheduler` و `scikit-learn` مستوردة في الوقت الفعلي لكنها غير موجودة في requirements.txt.

### 2.2 واجهة المستخدم (Frontend)

| المكوّن | التفاصيل |
|---------|---------|
| Framework | React 18.2.0 + Vite 5.1.0 |
| TypeScript | ^6.0.3 |
| State Management | Zustand ^4.5.0 (لا Redux, لا Context API) |
| CSS | TailwindCSS 3.4.1 |
| HTTP Client | fetch API الأصلي (axios مثبت لكن غير مستخدم) |
| i18n | i18next ^26.3.6 + react-i18next ^17.0.11 |
| الرسوم البيانية | recharts ^3.8.1 |
| الاختبارات | Vitest ^4.1.6 + jsdom + @testing-library/react |

**ملاحظة مهمة**: لا يوجد React Query أو SWR — جميع جلب البيانات يدوياً عبر useEffect + useState.

### 2.3 تطبيق الهاتف (Mobile)

| المكوّن | التفاصيل |
|---------|---------|
| Framework | Flutter (SDK ≥3.0.0 <4.0.0) |
| State Management | flutter_bloc ^8.1.3 |
| Navigation | go_router ^13.0.0 |
| التخزين | flutter_secure_storage, shared_preferences |
| HTTP | http package |

**حالة التطوير**: مبكر — 6 شاشات فقط، 3 مسارات مربوطة.

### 2.4 قاعدة البيانات

| المكوّن | التفاصيل |
|---------|---------|
| DBMS | PostgreSQL 15 (Alpine) |
| ORM | SQLAlchemy ≥ 2.0 |
| Driver | pg8000 ≥ 1.0.0 |
| Multi-tenancy | عمود `school_id` في جميع الجداول ذات الصلة |
| تشفير مالي | `Numeric(10,2)` لجميع الحقول المالية |

### 2.5 محرك الذكاء الاصطناعي / RAG

**خط الاسترجاع الفعلي (ليس RAG معماري عام)**:

1. **استخراج النص**: `pdfplumber` يُخرج النص من PDF
2. **تقسيم النص**: `RecursiveCharacterTextSplitter` — حجم 500 حرف، تراكب 100 حرف
3. **إنشاء التضمينات**: TF-IDF عبر `scikit-learn` (`TfidfVectorizer` — char_wb analyzer, ngram_range=(2,4), max_features=10000)
4. **التخزين**: ملفات JSON في `data/faiss_indexes/school_{school_id}.json`
5. **الاسترجاع**: cosine_similarity → فلترة score > 0.01 → إرجاع k نتائج
6. **التجميع**: sctx10 نتائج × 12,000 حرف كحد أقصى

**ملاحظة مهمة**: FAISS م listed في requirements.txt لكنه غير مستخدم. النظام بالكامل يعتمد على TF-IDF.

---

## 3. نموذج البيانات

### 3.1 الجداول الرئيسية (~50 جدول)

**الجداول الأساسية**:
- `schools` — الكيان الجامع (multi-tenant root)
- `users` — المستخدمون مع `school_id` FK و `role` enum

**الجداول المالية**:
- `wallet_transactions` — دفتر مالي append-only مع `amount Numeric(10,2)` و `pool WalletPool`
- `course_purchases` — مشتريات الدورات مع `amount_paid`, `platform_fee`, `teacher_revenue`
- `pack_purchases` — مشتريات الحزم
- `payments` — مدفوعات Stripe

**جداول LMS**:
- `courses`, `modules`, `lessons`, `quizzes`, `quiz_questions`, `quiz_options`, `quiz_attempts`
- `course_enrollments`, `progress`, `assignments`, `submissions`

**جداول الحزم الدراسية**:
- `study_packs` — حزم الدورات مع `niveau_scolaire` و `matieres` (JSON)
- `pack_purchases` — مشتريات الحزم مع `valid_from`, `valid_until`

**جداول المسار التكيفي**:
- `niveaux_etude`, `matieres`, `chapter_pathways`, `notions`, `contenus_notion`
- `profils_assimilation` — بروفايل امتصاص كل طالب لكل فصل
- `notifications_reorientation` — إشعارات إعادة التوجيه

**جداول التقييم**:
- `badge_definitions`, `student_badges`, `student_streaks`, `student_rankings`

### 3.2 استراتيجية Multi-tenancy

**النموذج الفعلي**: عمود `school_id` في جميع الجداول ذات الصلة.

**آلية التنفيذ** (`app/db/session.py`):
```python
# ContextVar لتخزين معرف المدرسة الحالي
current_tenant_id: ContextVar[int | None] = ContextVar("current_tenant_id", default=None)
_tenant_filter_suppressed: ContextVar[bool] = ContextVar("_tenant_filter_suppressed", default=False)

# Event listener على Session.do_orm_execute
# يُحقن WHERE school_id = current_tenant_id في جميع SELECTs
```

**استثناءات**:
- `super_admin` و `pedagogical_admin` → يتجاوزون الفلتر
- `tenant_unaware()` context manager → يُكتم الفلتر للدورات العامة
- `has_course_access()` خطوة 6/7 → `_tenant_filter_suppressed` للحزم الفردية

---

## 4. الأمان والمصادقة

### 4.1 آلية المصادقة

**JWT Token**:
- الخوارزمية: HS256
- مدة الصلاحية: 1440 دقيقة (24 ساعة) — بدون refresh token
- المحتوى: `{"sub": user_id, "school_id": school_id, "exp": timestamp}`
- الإنشاء: `app/auth.py:create_access_token()`

**تشفير كلمات المرور**: bcrypt 4.0.1 عبر passlib.

**حماية من Brute-force**: 5 محاولات فاشلة → قفل لمدة 15 دقيقة (`locked_until`).

### 4.2 تطبيق RBAC

**النمط**: FastAPI Dependencies.

**جميع الدوال** (`app/deps.py`):

| الدالة | الأدوار المسموح بها |
|--------|-------------------|
| `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| `require_platform_admin` | super_admin, pedagogical_admin |
| `require_school_admin_strict` | admin_school فقط |
| `require_teacher_or_admin` | super_admin, admin_school, teacher |
| `require_pedagogical_admin` | pedagogical_admin فقط |
| `require_pedagogical_lead` | pedagogical_lead فقط (يجب أن يكون له school_id) |
| `require_parent` | parent فقط |

**مثال على الاستخدام** (`app/routers/admin.py`):
```python
@router.get("/users")
def list_users(current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    ...
```

### 4.3 إدارة الأسرار

- **المتغيرات البيئية**: `.env` (غير مصدّق في Git)
- **القائمة**: `JWT_SECRET`, `DATABASE_URL`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `MINIMAX_API_KEY`, `STRIPE_SECRET_KEY`, إلخ
- **لا يوجد vault أو إدارة أسرار متقدمة**
- **ملف `API_Keys.txt` موجود في جذر المشروع** — ⚠️ خطر أمني محتمل

---

## 5. التكاملات الخارجية

### 5.1 MiniMax API (وغيره من مزودي الذكاء الاصطناعي)

**9 مزودين مدعومين** (`app/ai/provider_client.py`):
```python
SUPPORTED_PROVIDERS = {
    "openai", "groq", "openrouter", "minimax", "anthropic",
    "azure", "google", "freetokenfaucet", "nvidia"
}
```

**اختيار المزود**: الأولوية `freetokenfaucet → nvidia → openai → groq → openrouter → minimax → anthropic → azure → google`. الأول مع `enabled=True` و مفتاح موجود.

**تنسيق الاستدعاء**: OpenAI-compatible client مع `base_url` اختياري.

**معالجة الأخطاء**:
- timeout: 180s (OpenAI-compatible), 60s (Anthropic)
- retry: max 3 محاولات، exponential backoff
- فلترة نماذج التضمين من استدعاءات الدردشة

### 5.2 الدفع (Paymee/Konnect)

**حالة التكامل**: Stripe مدمج في الكود (`payments/stripe.py`) لكن Paymee/Konnect غير موجود.

**التدفق الفعلي**:
- `POST /api/payments/checkout` → إنشاء جلسة Stripe
- `POST /api/payments/webhook` → معالجة أحداث Stripe
- `Payment` model يخزن `stripe_session_id`

### 5.3 تكاملات أخرى

- **weasyprint**: لتوليد تقارير PDF
- **python-docx**: لتوليد مستندات Word
- **pdfplumber**: لاستخراج النص من PDF
- **langchain-text-splitters**: لتقسيم النصوص

---

## 6. القيود التقنية والمخاطر المعروفة

### 6.1 قيود قابلية التوسع

- **لا يوجد cache**: لا Redis، لا memcached (Redis اختياري فقط لـ rate limiting)
- **لا يوجد queue غير متزامن**: لا Celery، لا RQ — المهام في الخلفية عبر APScheduler فقط
- **لا يوجد WebSocket**: جميع الاتصالات REST
- **TF-IDF يُعاد بناؤه عند كل استعلام**: لا persistent index

### 6.2 الديون التقنية الحالية

- **المالي Float vs Numeric**: تم تحويل جميع الحقول المالية إلى `Numeric(10,2)` (11 colonne) — wallet_transactions.amount, courses.price, courses.commission_rate, course_purchases (amount_paid/platform_fee/teacher_revenue/commission_rate_applied), study_packs.price, pack_purchases.amount_paid, payments.amount, school_course_accesses.price_paid_dt, users.dt_balance. Migration SQL: `migrations/2026_08_01_numeric_monetary.sql`
- **المigration**: لا يوجد Alembic — يتم استخدام SQL مباشر و `Base.metadata.create_all()`
- **12 سكريبت seed**: تكرار كبير في بيانات التجربة
- **axios مثبت لكن غير مستخدم** في الواجهة الأمامية
- **Student sidebar en 5 sections rétractables** (DashboardLayout.tsx : Accueil/Parcours/IA/Objectifs/Profil). AdminLayout et SchoolAdminLayout conservent leur sidebar plate. Les 3 layouts partagent un même pattern mais le student est maintenant unifié
- **لا tsconfig.json** في الواجهة الأمامية

### 6.3 قيود البنية التحتية

- **Docker**: docker-compose.yml للتطوير + docker-compose.prod.yml للإنتاج
- **النشر**: GitHub Actions → Render (deploy فقط على main)
- **لا يوجد staging environment**

---

## 7. البيئات والنشر

### 7.1 البيئات

| البيئة | التفاصيل |
|--------|---------|
| Development | SQLite (اختبارات) أو PostgreSQL محلي |
| Production | PostgreSQL 15 على Render |
| CI | GitHub Actions مع postgres:15 service |

### 7.2 Pipeline CI/CD

**الملف**: `backend/.github/workflows/ci-cd.yml`

```
push to main/develop → test → docker build → deploy to Render (main فقط)
PR to main → test → docker build (push=false)
```

### 7.3 استراتيجية Migration DB

**لا يوجد Alembic** رغم أن Dockerfile يُشغّل `python -m alembic upgrade head || true`.

**الإدارة الحالية**:
- `Base.metadata.create_all()` في startup
- ملفات SQL مباشرة في `backend/migrations/`
- لا يوجد versioning للـ schema

---

# PARTIE 2 — SPÉCIFICATION TECHNIQUE (Français)

---

## 1. VUE D'ENSEMBLE DE L'ARCHITECTURE

### 1.1 Composants du système

EDUAI Learning se compose de cinq composants principaux :

```
┌─────────────────────────────────────────────────────┐
│               Client (Navigateur/App)               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Frontend Web │  │  App Flutter  │  │  API REST  │ │
│  │  React/Vite   │  │  Mobile       │  │  FastAPI   │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
└─────────┼──────────────────┼────────────────┼────────┘
          │                  │                │
          ▼                  ▼                ▼
┌─────────────────────────────────────────────────────┐
│           FastAPI Backend (Python 3.11+)            │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐ │
│  │ Routers  │ │ Services │ │ Moteur IA │ │Models  │ │
│  │ (27)     │ │          │ │ (RAG)     │ │ (50+)  │ │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘ └───┬────┘ │
└───────┼───────────┼─────────────┼───────────┼──────┘
        │           │             │           │
        ▼           ▼             ▼           ▼
┌─────────────────────────────────────────────────────┐
│           PostgreSQL 15 (Base de données)           │
│  ┌──────────────────────────────────────────────┐   │
│  │  50+ tables — multi-tenant via school_id      │   │
│  │  Numeric(10,2) pour champs monétaires         │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 1.2 Communication entre composants

- **Frontend ↔ Backend** : REST API via HTTP/HTTPS. Aucun WebSocket. Le streaming IA utilise Server-Sent Events (SSE) via `fetch` avec `generateContentStream` (`features/admin/api/index.ts`).
- **Backend ↔ DB** : SQLAlchemy ORM avec driver pg8000.
- **Backend ↔ IA** : Appels API directs (clients OpenAI-compatible) avec retry logic (`app/ai/rag_service.py`).
- **Backend ↔ RAG** : TF-IDF (scikit-learn) pour le retrieval — FAISS n'est PAS utilisé malgré sa présence dans `requirements.txt`.

### 1.3 Justifications architecturales

- **Pourquoi RAG plutôt que fine-tuning ?** : Raison non documentée dans le repo. Le RAG permet de mettre à jour le contenu sans ré-entraînement et à moindre coût.
- **Pourquoi PostgreSQL ?** : Raison non documentée dans le repo. PostgreSQL offre row-level security, support JSON, et précision Numeric pour les calculs financiers.

---

## 2. STACK TECHNIQUE DÉTAILLÉ

### 2.1 Backend

| Composant | Détails |
|-----------|---------|
| Framework | FastAPI ≥ 0.95.0 |
| ORM | SQLAlchemy ≥ 2.0 (utilisé avec `Base.metadata.create_all` — pas d'Alembic) |
| Driver DB | pg8000 ≥ 1.0.0 |
| Auth JWT | python-jose ≥ 3.3.0 (HS256) |
| Hashing mots de passe | bcrypt 4.0.1 via passlib ≥ 1.7.4 |
| Validation | pydantic ≥ 1.10.2, pydantic-settings ≥ 2.0 |
| Rate Limiting | slowapi ≥ 0.1.9 + Redis optionnel |
| Scheduler | APScheduler (BackgroundScheduler) — absent de requirements.txt |
| Fichiers | aiofiles ≥ 23.0.0 |
| PDF/Docx | weasyprint ≥ 60.0, python-docx ≥ 1.1.0 |

**Note** : `bcrypt==4.0.1` est piné exactement. `apscheduler` et `scikit-learn` sont importés runtime mais absents de `requirements.txt`.

### 2.2 Frontend

| Composant | Détails |
|-----------|---------|
| Framework | React 18.2.0 + Vite 5.1.0 |
| TypeScript | ^6.0.3 |
| State Management | Zustand ^4.5.0 (pas Redux, pas Context API) |
| CSS | TailwindCSS 3.4.1 |
| HTTP Client | `fetch` natif (axios installé mais inutilisé) |
| i18n | i18next ^26.3.6 + react-i18next ^17.0.11 |
| Charts | recharts ^3.8.1 |
| Tests | Vitest ^4.1.6 + jsdom + @testing-library/react |

**Note** : Aucun React Query ni SWR — tout le data fetching est manuel via `useEffect` + `useState`.

### 2.3 Mobile

| Composant | Détails |
|-----------|---------|
| Framework | Flutter (SDK ≥3.0.0 <4.0.0) |
| State Management | flutter_bloc ^8.1.3 |
| Navigation | go_router ^13.0.0 |
| Stockage | flutter_secure_storage, shared_preferences |
| HTTP | http package |

**État** : Précoce — 6 écrans, 3 routes câblées uniquement.

### 2.4 Base de données

| Composant | Détails |
|-----------|---------|
| DBMS | PostgreSQL 15 (Alpine) |
| ORM | SQLAlchemy ≥ 2.0 |
| Driver | pg8000 ≥ 1.0.0 |
| Multi-tenancy | Colonne `school_id` partout |
| Précision monétaire | `Numeric(10,2)` pour tous les champs financiers |

### 2.5 Moteur IA / RAG

**Pipeline de retrieval réel** (pas un RAG générique) :

1. **Extraction texte** : `pdfplumber` — extraction depuis PDF
2. **Découpage** : `RecursiveCharacterTextSplitter` — chunk_size=500, overlap=100
3. **Embeddings** : TF-IDF via `scikit-learn` (`TfidfVectorizer` — analyzer='char_wb', ngram_range=(2,4), max_features=10000)
4. **Stockage** : Fichiers JSON dans `data/faiss_indexes/school_{school_id}.json`
5. **Retrieval** : cosine_similarity → filtrage score > 0.01 → k résultats
6. **Assemblage** : k=10 résultats, 12000 caractères max

**Note** : FAISS est listé dans `requirements.txt` mais n'est PAS utilisé. Le système est entièrement basé sur TF-IDF.

---

## 3. MODÈLE DE DONNÉES

### 3.1 Tables principales (~50 tables)

**Tables fondamentales** :
- `schools` — entité racine multi-tenant
- `users` — utilisateurs avec `school_id` FK et enum `role`

**Tables financières** :
- `wallet_transactions` — ledger append-only, `amount Numeric(10,2)`, `pool WalletPool`
- `course_purchases` — achats de cours avec `amount_paid`, `platform_fee`, `teacher_revenue`
- `pack_purchases` — achats de packs avec `valid_from`, `valid_until`
- `payments` — paiements Stripe

**Tables LMS** :
- `courses`, `modules`, `lessons`, `quizzes`, `quiz_questions`, `quiz_options`, `quiz_attempts`
- `course_enrollments`, `progress`, `assignments`, `submissions`

**Tables Packs d'études** :
- `study_packs` — packs avec `niveau_scolaire` et `matieres` (JSON)
- `pack_purchases` — achats avec durée de validité

**Tables Parcours adaptatif** :
- `niveaux_etude`, `matieres`, `chapter_pathways`, `notions`, `contenus_notion`
- `profils_assimilation` — profil d'assimilation par élève par chapitre
- `notifications_reorientation` — notifications de réorientation

**Tables Gamification** :
- `badge_definitions`, `student_badges`, `student_streaks`, `student_rankings`

### 3.2 Stratégie de Multi-tenancy

**Modèle implémenté** : Colonne `school_id` dans toutes les tables pertinentes.

**Mécanisme** (`app/db/session.py`) :
```python
# ContextVar pour stocker l'ID école courant
current_tenant_id: ContextVar[int | None] = ContextVar("current_tenant_id", default=None)
_tenant_filter_suppressed: ContextVar[bool] = ContextVar("_tenant_filter_suppressed", default=False)

# Event listener sur Session.do_orm_execute
# Injecte WHERE school_id = current_tenant_id dans tous les SELECTs
```

**Exceptions** :
- `super_admin` et `pedagogical_admin` → contournent le filtre
- `tenant_unaware()` context manager → supprime le filtre pour les rôles globaux
- `has_course_access()` étape 6/7 → `_tenant_filter_suppressed` pour les packs individuels

---

## 4. SÉCURITÉ ET AUTHENTIFICATION

### 4.1 Mécanisme d'authentification

**JWT Token** :
- Algorithme : HS256
- Durée de vie : 1440 minutes (24 heures) — aucun refresh token
- Contenu : `{"sub": user_id, "school_id": school_id, "exp": timestamp}`
- Création : `app/auth.py:create_access_token()`

**Hashing mots de passe** : bcrypt 4.0.1 via passlib.

**Protection brute-force** : 5 tentatives échouées → verrouillage 15 minutes (`locked_until`).

### 4.2 Application du RBAC

**Pattern** : FastAPI Dependencies.

**Toutes les fonctions** (`app/deps.py`) :

| Fonction | Rôles autorisés |
|----------|----------------|
| `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| `require_platform_admin` | super_admin, pedagogical_admin |
| `require_school_admin_strict` | admin_school uniquement |
| `require_teacher_or_admin` | super_admin, admin_school, teacher |
| `require_pedagogical_admin` | pedagogical_admin uniquement |
| `require_pedagogical_lead` | pedagogical_lead uniquement (doit avoir school_id) |
| `require_parent` | parent uniquement |

**Exemple d'usage** (`app/routers/admin.py`) :
```python
@router.get("/users")
def list_users(current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    ...
```

### 4.3 Gestion des secrets

- **Variables d'environnement** : `.env` (non commité en Git)
- **Liste** : `JWT_SECRET`, `DATABASE_URL`, `OPENAI_API_KEY`, `GROQ_API_KEY`, etc.
- **Aucun vault ni gestion avancée des secrets**
- **Fichier `API_Keys.txt` présent à la racine** — ⚠️ risque de sécurité potentiel

---

## 5. INTÉGRATIONS EXTERNES

### 5.1 MiniMax API (et autres fournisseurs IA)

**9 fournisseurs supportés** (`app/ai/provider_client.py`) :
```python
SUPPORTED_PROVIDERS = {
    "openai", "groq", "openrouter", "minimax", "anthropic",
    "azure", "google", "freetokenfaucet", "nvidia"
}
```

**Sélection du fournisseur** : Par priorité `freetokenfaucet → nvidia → openai → groq → openrouter → minimax → anthropic → azure → google`. Premier avec `enabled=True` et clé configurée.

**Format d'appel** : Client OpenAI-compatible avec `base_url` optionnel.

**Gestion des erreurs** :
- Timeout : 180s (OpenAI-compatible), 60s (Anthropic)
- Retry : max 3 tentatives, backoff exponentiel
- Filtrage des modèles d'embedding des appels chat

### 5.2 Paiement (Stripe)

**Intégration actuelle** : Stripe (`payments/stripe.py`). Paymee/Konnect absent du code.

**Flux** :
- `POST /api/payments/checkout` → création session Stripe
- `POST /api/payments/webhook` → traitement événements Stripe
- Modèle `Payment` stocke `stripe_session_id`

### 5.3 Autres intégrations

- **weasyprint** : génération de rapports PDF
- **python-docx** : génération de documents Word
- **pdfplumber** : extraction de texte depuis PDF
- **langchain-text-splitters** : découpage de textes

---

## 6. CONTRAINTES TECHNIQUES ET LIMITES CONNUES

### 6.1 Limites de scalabilité

- **Aucun cache** : pas de Redis, pas de memcached (Redis optionnel uniquement pour rate limiting)
- **Aucune queue asynchrone** : pas de Celery, pas de RQ — tâches de fond via APScheduler uniquement
- **Aucun WebSocket** : toutes les communications sont REST
- **TF-IDF reconstruit à chaque requête** : pas de persistent index

### 6.2 Dette technique identifiée

- **Champs monétaires Float vs Numeric** : la plupart convertis en `Numeric(10,2)` mais `Transaction.amount`, `TokenPackage.price_dt`, `Course.price_dt` restent en Float
- **Migrations** : pas d'Alembic — SQL brut + `Base.metadata.create_all()`
- **12 scripts seed** : redondance significative
- **axios installé mais inutilisé** côté frontend
- **Student sidebar en 5 sections rétractables** (DashboardLayout.tsx : Accueil/Parcours/IA/Objectifs/Profil). AdminLayout et SchoolAdminLayout conservent leur sidebar plate. Les 3 layouts partagent un même pattern mais le student est maintenant unifié
- **Pas de tsconfig.json** côté frontend

### 6.3 Limites d'infrastructure

- **Docker** : docker-compose.yml (dev) + docker-compose.prod.yml (prod)
- **Déploiement** : GitHub Actions → Render (déploiement sur main uniquement)
- **Pas de staging environment**

---

## 7. ENVIRONNEMENTS ET DÉPLOIEMENT

### 7.1 Environnements

| Environnement | Détails |
|---------------|---------|
| Development | SQLite (tests) ou PostgreSQL local |
| Production | PostgreSQL 15 sur Render |
| CI | GitHub Actions avec service postgres:15 |

### 7.2 Pipeline CI/CD

**Fichier** : `backend/.github/workflows/ci-cd.yml`

```
push to main/develop → test → docker build → deploy to Render (main uniquement)
PR to main → test → docker build (push=false)
```

### 7.3 Stratégie de migration DB

**Pas d'Alembic** malgré que le Dockerfile exécute `python -m alembic upgrade head || true`.

**Gestion actuelle** :
- `Base.metadata.create_all()` au startup
- Fichiers SQL bruts dans `backend/migrations/`
- Aucun versioning du schema

---

# PARTIE 3 — TECHNICAL SPECIFICATION (English)

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 System Components

EDUAI Learning consists of five main components:

```
┌─────────────────────────────────────────────────────┐
│               Client (Browser/App)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Web Frontend │  │  Flutter App  │  │  REST API  │ │
│  │  React/Vite   │  │  Mobile       │  │  FastAPI   │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
└─────────┼──────────────────┼────────────────┼────────┘
          │                  │                │
          ▼                  ▼                ▼
┌─────────────────────────────────────────────────────┐
│           FastAPI Backend (Python 3.11+)            │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐ │
│  │ Routers  │ │ Services │ │ AI Engine │ │ Models │ │
│  │ (27)     │ │          │ │ (RAG)     │ │ (50+)  │ │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘ └───┬────┘ │
└───────┼───────────┼─────────────┼───────────┼──────┘
        │           │             │           │
        ▼           ▼             ▼           ▼
┌─────────────────────────────────────────────────────┐
│           PostgreSQL 15 (Database)                  │
│  ┌──────────────────────────────────────────────┐   │
│  │  50+ tables — multi-tenant via school_id      │   │
│  │  Numeric(10,2) for monetary fields            │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 1.2 Inter-component Communication

- **Frontend ↔ Backend**: REST API over HTTP/HTTPS. No WebSocket. AI streaming uses Server-Sent Events (SSE) via `fetch` with `generateContentStream` (`features/admin/api/index.ts`).
- **Backend ↔ DB**: SQLAlchemy ORM with pg8000 driver.
- **Backend ↔ AI**: Direct API calls (OpenAI-compatible clients) with retry logic (`app/ai/rag_service.py`).
- **Backend ↔ RAG**: TF-IDF (scikit-learn) for retrieval — FAISS is NOT used despite being in `requirements.txt`.

### 1.3 Architectural Justifications

- **Why RAG instead of fine-tuning?**: Reason not documented in the repo. RAG allows content updates without retraining and at lower cost.
- **Why PostgreSQL?**: Reason not documented in the repo. PostgreSQL provides row-level security, JSON support, and Numeric precision for financial calculations.

---

## 2. DETAILED TECH STACK

### 2.1 Backend

| Component | Details |
|-----------|---------|
| Framework | FastAPI ≥ 0.95.0 |
| ORM | SQLAlchemy ≥ 2.0 (used with `Base.metadata.create_all` — no Alembic) |
| DB Driver | pg8000 ≥ 1.0.0 |
| JWT Auth | python-jose ≥ 3.3.0 (HS256) |
| Password Hashing | bcrypt 4.0.1 via passlib ≥ 1.7.4 |
| Validation | pydantic ≥ 1.10.2, pydantic-settings ≥ 2.0 |
| Rate Limiting | slowapi ≥ 0.1.9 + Redis optional |
| Scheduler | APScheduler (BackgroundScheduler) — absent from requirements.txt |
| Files | aiofiles ≥ 23.0.0 |
| PDF/Docx | weasyprint ≥ 60.0, python-docx ≥ 1.1.0 |

**Important note**: `bcrypt==4.0.1` is pinned exactly. `apscheduler` and `scikit-learn` are imported at runtime but absent from `requirements.txt`.

### 2.2 Frontend

| Component | Details |
|-----------|---------|
| Framework | React 18.2.0 + Vite 5.1.0 |
| TypeScript | ^6.0.3 |
| State Management | Zustand ^4.5.0 (no Redux, no Context API) |
| CSS | TailwindCSS 3.4.1 |
| HTTP Client | Native `fetch` (axios installed but unused) |
| i18n | i18next ^26.3.6 + react-i18next ^17.0.11 |
| Charts | recharts ^3.8.1 |
| Testing | Vitest ^4.1.6 + jsdom + @testing-library/react |

**Important note**: No React Query or SWR — all data fetching is manual via `useEffect` + `useState`.

### 2.3 Mobile

| Component | Details |
|-----------|---------|
| Framework | Flutter (SDK ≥3.0.0 <4.0.0) |
| State Management | flutter_bloc ^8.1.3 |
| Navigation | go_router ^13.0.0 |
| Storage | flutter_secure_storage, shared_preferences |
| HTTP | http package |

**Status**: Early-stage — 6 screens, 3 routes wired.

### 2.4 Database

| Component | Details |
|-----------|---------|
| DBMS | PostgreSQL 15 (Alpine) |
| ORM | SQLAlchemy ≥ 2.0 |
| Driver | pg8000 ≥ 1.0.0 |
| Multi-tenancy | `school_id` column everywhere |
| Monetary Precision | `Numeric(10,2)` for all financial fields |

### 2.5 AI/RAG Engine

**Actual retrieval pipeline** (not a generic RAG architecture):

1. **Text extraction**: `pdfplumber` — extracts from PDF
2. **Chunking**: `RecursiveCharacterTextSplitter` — chunk_size=500, overlap=100
3. **Embeddings**: TF-IDF via `scikit-learn` (`TfidfVectorizer` — analyzer='char_wb', ngram_range=(2,4), max_features=10000)
4. **Storage**: JSON files in `data/faiss_indexes/school_{school_id}.json`
5. **Retrieval**: cosine_similarity → filter score > 0.01 → return k results
6. **Assembly**: k=10 results, 12000 chars max

**Important note**: FAISS is listed in `requirements.txt` but is NOT used. The system is entirely TF-IDF based.

---

## 3. DATA MODEL

### 3.1 Main Tables (~50 tables)

**Core tables**:
- `schools` — multi-tenant root entity
- `users` — users with `school_id` FK and `role` enum

**Financial tables**:
- `wallet_transactions` — append-only ledger, `amount Numeric(10,2)`, `pool WalletPool`
- `course_purchases` — course purchases with `amount_paid`, `platform_fee`, `teacher_revenue`
- `pack_purchases` — pack purchases with `valid_from`, `valid_until`
- `payments` — Stripe payments

**LMS tables**:
- `courses`, `modules`, `lessons`, `quizzes`, `quiz_questions`, `quiz_options`, `quiz_attempts`
- `course_enrollments`, `progress`, `assignments`, `submissions`

**Study Pack tables**:
- `study_packs` — packs with `niveau_scolaire` and `matieres` (JSON)
- `pack_purchases` — purchases with validity duration

**Adaptive Pathway tables**:
- `niveaux_etude`, `matieres`, `chapter_pathways`, `notions`, `contenus_notion`
- `profils_assimilation` — per-student per-chapter assimilation profile
- `notifications_reorientation` — reorientation notifications

**Gamification tables**:
- `badge_definitions`, `student_badges`, `student_streaks`, `student_rankings`

### 3.2 Multi-tenancy Strategy

**Implemented model**: `school_id` column in all relevant tables.

**Mechanism** (`app/db/session.py`):
```python
# ContextVar to store current school ID
current_tenant_id: ContextVar[int | None] = ContextVar("current_tenant_id", default=None)
_tenant_filter_suppressed: ContextVar[bool] = ContextVar("_tenant_filter_suppressed", default=False)

# Event listener on Session.do_orm_execute
# Injects WHERE school_id = current_tenant_id in all SELECTs
```

**Exceptions**:
- `super_admin` and `pedagogical_admin` → bypass the filter
- `tenant_unaware()` context manager → suppresses filter for global roles
- `has_course_access()` step 6/7 → `_tenant_filter_suppressed` for individual packs

---

## 4. SECURITY & AUTHENTICATION

### 4.1 Authentication Mechanism

**JWT Token**:
- Algorithm: HS256
- Lifetime: 1440 minutes (24 hours) — no refresh token
- Payload: `{"sub": user_id, "school_id": school_id, "exp": timestamp}`
- Creation: `app/auth.py:create_access_token()`

**Password Hashing**: bcrypt 4.0.1 via passlib.

**Brute-force Protection**: 5 failed attempts → 15-minute lockout (`locked_until`).

### 4.2 RBAC Enforcement

**Pattern**: FastAPI Dependencies.

**All functions** (`app/deps.py`):

| Function | Allowed Roles |
|----------|---------------|
| `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| `require_platform_admin` | super_admin, pedagogical_admin |
| `require_school_admin_strict` | admin_school only |
| `require_teacher_or_admin` | super_admin, admin_school, teacher |
| `require_pedagogical_admin` | pedagogical_admin only |
| `require_pedagogical_lead` | pedagogical_lead only (must have school_id) |
| `require_parent` | parent only |

**Usage example** (`app/routers/admin.py`):
```python
@router.get("/users")
def list_users(current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    ...
```

### 4.3 Secrets Management

- **Environment variables**: `.env` (not committed to Git)
- **List**: `JWT_SECRET`, `DATABASE_URL`, `OPENAI_API_KEY`, `GROQ_API_KEY`, etc.
- **No vault or advanced secrets management**
- **`API_Keys.txt` file at project root** — ⚠️ potential security risk

---

## 5. EXTERNAL INTEGRATIONS

### 5.1 MiniMax API (and other AI providers)

**9 supported providers** (`app/ai/provider_client.py`):
```python
SUPPORTED_PROVIDERS = {
    "openai", "groq", "openrouter", "minimax", "anthropic",
    "azure", "google", "freetokenfaucet", "nvidia"
}
```

**Provider selection**: By priority `freetokenfaucet → nvidia → openai → groq → openrouter → minimax → anthropic → azure → google`. First with `enabled=True` and configured key.

**Call format**: OpenAI-compatible client with optional `base_url`.

**Error handling**:
- Timeout: 180s (OpenAI-compatible), 60s (Anthropic)
- Retry: max 3 attempts, exponential backoff
- Embedding model filtering from chat calls

### 5.2 Payment (Stripe)

**Current integration**: Stripe (`payments/stripe.py`). Paymee/Konnect absent from code.

**Flow**:
- `POST /api/payments/checkout` → create Stripe session
- `POST /api/payments/webhook` → process Stripe events
- `Payment` model stores `stripe_session_id`

### 5.3 Other Integrations

- **weasyprint**: PDF report generation
- **python-docx**: Word document generation
- **pdfplumber**: PDF text extraction
- **langchain-text-splitters**: Text splitting

---

## 6. TECHNICAL CONSTRAINTS & KNOWN LIMITATIONS

### 6.1 Scalability Limits

- **No cache**: no Redis, no memcached (Redis optional for rate limiting only)
- **No async task queue**: no Celery, no RQ — background tasks via APScheduler only
- **No WebSocket**: all communication is REST
- **TF-IDF rebuilt on every query**: no persistent index

### 6.2 Identified Technical Debt

- **Monetary Float vs Numeric**: most fields converted to `Numeric(10,2)` but `Transaction.amount`, `TokenPackage.price_dt`, `Course.price_dt` remain Float
- **Migrations**: no Alembic — raw SQL + `Base.metadata.create_all()`
- **12 seed scripts**: significant redundancy
- **axios installed but unused** on frontend
- **3 separate layouts** for sidebar with duplicated patterns
- **No tsconfig.json** on frontend

### 6.3 Infrastructure Limitations

- **Docker**: docker-compose.yml (dev) + docker-compose.prod.yml (prod)
- **Deployment**: GitHub Actions → Render (deploy on main only)
- **No staging environment**

---

## 7. ENVIRONMENTS & DEPLOYMENT

### 7.1 Environments

| Environment | Details |
|-------------|---------|
| Development | SQLite (tests) or local PostgreSQL |
| Production | PostgreSQL 15 on Render |
| CI | GitHub Actions with postgres:15 service |

### 7.2 CI/CD Pipeline

**File**: `backend/.github/workflows/ci-cd.yml`

```
push to main/develop → test → docker build → deploy to Render (main only)
PR to main → test → docker build (push=false)
```

### 7.3 DB Migration Strategy

**No Alembic** despite Dockerfile running `python -m alembic upgrade head || true`.

**Current management**:
- `Base.metadata.create_all()` at startup
- Raw SQL files in `backend/migrations/`
- No schema versioning

---

# ANNEXE A — DETTE TECHNIQUE ET RISQUES ARCHITECTURAUX

| # | Problème | Sévérité | Impact |
|---|----------|----------|--------|
| 1 | **Pas de refresh token JWT** — token expire après 24h sans renouvellement possible | À planifier | Déconnexion imprévisible des utilisateurs actifs |
| 2 | **Migrations sans Alembic** — schema géré par `create_all()` + SQL brut | Bloquant lancement | Risque de perte de données en production lors de changements de schema |
| 3 | **TF-IDF sans index persistent** — matrice reconstruite à chaque requête retrieval | À planifier | Performance dégradée avec beaucoup de documents |
| 4 | **`Transaction.amount` et `TokenPackage.price_dt` encore en Float** | À planifier | Incohérence monétaire potentielle |
| 5 | **Pas de queue asynchrone** — appels IA synchrones | À planifier | Saturation du worker sous charge |
| 6 | **Aucun cache** — requêtes DB à chaque requête HTTP | À planifier | Charge sur PostgreSQL |
| 7 | **12 scripts seed redondants** | Mineur | Maintenance difficile |
| 8 | **`API_Keys.txt` à la racine** | Mineur | Risque de fuite de secrets |
| 9 | **Mobile très précoce** — 3 routes sur 6 écrans | Mineur | Fonctionnalités limitées |
| 10 | **Pas de tsconfig.json** — TypeScript fonctionne via defaults Vite | Mineur | Comportement imprévisible possible |
| 11 | **axios installé mais inutilisé** | Mineur | Bundle size inutile |
| 12 | **3 layouts sidebar séparés** avec patterns dupliqués | Mineur | Dette de maintenance |

---

# ANNEXE B — DÉCISIONS D'ARCHITECTURE NON DOCUMENTÉES

| # | Décision | Fichier concerné | Impact |
|---|----------|-----------------|--------|
| 1 | **Multi-tenancy par ContextVar** au lieu de RLS PostgreSQL | `app/db/session.py` | Le filtre est injecté au niveau ORM, pas au niveau DB — contournable si quelqu'un utilise raw SQL |
| 2 | **Wallet unifié** : tous les flux passent par `WalletTransaction` append-only | `app/services/wallet.py` | `dt_balance` sur User est une colonne dépréciée mais encore lue |
| 3 | **Pack Découverte** ne reçoit jamais d'objectif personnalisé | `app/services/goal_tracking.py` | Règle métier non tracée dans le code comme commentaire |
| 4 | **Règle de publication** : Standard + (Remédiation OU Avancé) minimum | `app/services/adaptive_pathway.py` | Logique dispersée, pas de fonction dédiée |
| 5 | **Statut toujours recalculé** : `LearningGoal.statut` n'est jamais stocké | `app/services/goal_tracking.py` | Différent du pattern classique de stockage de statut |
| 6 | **Tenant filter supprimé pour packs individuels** | `app/services/course_access.py` | `_tenant_filter_suppressed` dans `has_course_access()` étapes 6/7 |
| 7 | **Provider IA par priorité** : freetokenfaucet en premier | `app/ai/provider_client.py` | Ordre non documenté, impacte quel provider est utilisé |
| 8 | **Rate limiting custom** au lieu de slowapi pour l'IA | `app/core/rate_limiter.py` | Redis optionnel, fallback in-memory |
| 9 | **Pas de séparation wallet IA vs wallet cours** | `app/models.py` | `WalletPool` enum combine les deux usages dans la même table |
| 10 | **Enrollment automatique** lors de l'achat de pack | `app/routers/packs.py` | Crée `CourseEnrollment` + vérifie level_up |
| 11 | **Notifications = in-app uniquement** | `app/services/notification_service.py` | Utilise le modèle `Message` existant, pas de push/email |
| 12 | **`_role_str` bug corrigé** en `get_user_role` | `app/routers/academy.py:90` | ancien code cassé avec NameError |

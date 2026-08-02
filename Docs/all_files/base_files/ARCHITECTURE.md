# ARCHITECTURE — EDUAI Learning

> Document de référence visuelle et structurelle du système.
> Ce document couvre les composants, la circulation des données, la liste des API exposées, et l'historique des décisions de conception.
> Mis à jour : 2026-08-01

---

# PARTIE 1 — البنية المعمارية (العربية)

---

## 1. مخطط المكونات

```
┌──────────────────────────────────────────────────────────────────┐
│                       المتصفح / التطبيق                          │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────┐  │
│  │  واجهة الويب     │   │  تطبيق Flutter   │   │  Swagger UI  │  │
│  │  React + Vite    │   │  Mobile          │   │  /docs       │  │
│  └────────┬─────────┘   └────────┬─────────┘   └──────┬───────┘  │
└───────────┼──────────────────────┼─────────────────────┼──────────┘
            │  REST API            │  REST API            │  REST API
            ▼                      ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11+)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Auth     │  │ Routers  │  │ Services │  │ AI/RAG Engine    │  │
│  │ JWT      │  │ (30+)    │  │ (18)     │  │ TF-IDF + API    │  │
│  │ bcrypt   │  │          │  │          │  │ externes         │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│  ┌────┴─────────────┴─────────────┴──────────────────┴─────────┐  │
│  │                    SQLAlchemy ORM                            │  │
│  │  Multi-tenant: event listener + ContextVar                  │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────────┘
                              │  SQL
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PostgreSQL 15                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  50+ جدول — multi-tenant عبر school_id                   │    │
│  │  Numeric(10,2) للحقول المالية                             │    │
│  │  WalletTransaction (append-only ledger)                  │    │
│  └──────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  FAISS Indexes (ملفات JSON في filesystem)                │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### وصف المكونات

| المكون | الدور | يتواصل مع |
|--------|-------|-----------|
| **React/Vite Frontend** | واجهة المستخدم الرئيسية | Backend عبر REST API |
| **Flutter Mobile** | تطبيق الجوال (قيد التطوير) | Backend عبر REST API |
| **FastAPI Backend** | خادم API + منطق الأعمال + RBAC + AI Engine | PostgreSQL, FAISS, موفري AI الخارجي |
| **PostgreSQL 15** | قاعدة البيانات الرئيسية | Backend عبر SQLAlchemy |
| **FAISS Indexes** | فهرس البحث الدلالي (TF-IDF) | Backend عبر embeddings_service |
| **موفري AI الخارجي** | نموذج اللغة الكبيرة | Backend عبر provider_client.py |

### لا يوجد في البنية

- لا يوجد message queue (RabbitMQ, Redis pub/sub)
- لا يوجد cache Redis في الإنتاج
- لا يوجد خدمة مراقبة منفصلة
- لا يوجد CDN أو load balancer منفصل

---

## 2. تدفق البيانات

### 2.1 تدفق التسجيل وتسجيل الدخول

```
POST /auth/login (email + password)
  -> auth.py:234        login() يستقبل OAuth2PasswordRequestForm
  -> auth.py:240        استعلام عن المستخدم بالبريد الإلكتروني
  -> auth.py:248-254    فحص قفل الحساب (5 محاولات فاشلة = قفل 15 دقيقة)
  -> security.py:3-7    verify_password() — bcrypt.checkpw()
  -> auth.py:267-268    إعادة تعيين عداد المحاولات
  -> auth.py:272        تحديث last_login
  -> auth.py:23-30      create_access_token() — JWT بـ HS256
                         الحمولة: {sub: user_id, school_id, exp: +24h}
  -> auth.py:275        return {"access_token": "...", "token_type": "bearer"}
```

**تفعيل JWT**: `get_current_user()` في `auth.py:41-76` يفك تشفير JWT، يستخرج user_id، ويجلب المستخدم من DB. ContextVar `current_tenant_id` يُضبط تلقائياً.

### 2.2 تدفق شراء كورس

```
POST /api/courses/{course_id}/purchase
  -> courses.py:318     استعلام عن الكورس — التحقق من وجوده
  -> courses.py:322-323 التحقق من أن السعر > 0
  -> courses.py:326-331 التحقق من عدم الشراء المسبق
  -> courses.py:335     get_dt_balance() — مجموع ledger WalletTransaction
  -> courses.py:336-340 فحص الرصيد vs السعر → 402 إذا غير كافٍ
  -> courses.py:345     debit_dt(db, user_id, course.price, commit=False)
                         wallet.py:135-148: إنشاء سجل WalletTransaction بمبلغ سالب
  -> courses.py:350-360 إنشاء سجل Transaction (COURSE_PURCHASE)
  -> courses.py:363-365 حساب العمولة: platform_fee = price * (commission_rate / Decimal("100"))
  -> courses.py:367-377 إنشاء CoursePurchase
  -> courses.py:380-384 إنشاء CourseEnrollment (تسجيل تلقائي)
  -> courses.py:385     db.commit() — COMMIT ذري واحد (atomique)
  -> courses.py:389-395 إشعار مؤلف الكورس عبر notify_purchase()
  -> courses.py:397-404 return {purchase_id, amount_paid, remaining_balance}
```

**ملاحظة**: لا يوجد فحص level_up في تدفق الشراء.

### 2.3 تدفق سؤال AI Tutor

```
POST /api/ai/ask {question, conversation_id?}
  -> ai.py:122          check_ai_rate_limit(user_id, "ai_ask") — 30 طلب/دقيقة
  -> ai.py:125          _validate_school_id()
  -> wallet.py:38       estimate_cost(AI_ASK, len(question)) ≈ 2 credits
  -> wallet.py:96-99    get_total_balance() — مجموع جميع الـ pools
  -> ai.py:131-136      فحص الرصيد >= التكلفة → 402 إذا غير كافٍ
  -> wallet.py:182-247  consume_credits() — خصم من pools بالترتيب:
                         1. SUBSCRIPTION, 2. SCHOOL_ALLOCATED, 3. TRIAL, 4. PURCHASED
                         (مع row-level lock عبر with_for_update())
  -> ai.py:143          RAGService(db=db)
  -> ai.py:148-149      _get_or_create_conversation()
  -> ai.py:152          _load_conversation_history() — آخر 20 رسالة
  -> rag_service.py:362 ask_tutor() → generate(mode="tutor")
  -> rag_service.py:197 retrieve_context(school_id, prompt, k=5)
  -> embeddings_service.py:120-155 similarity_search()
                         - تحميل مستندات school من filesystem
                         - بناء TF-IDF vectorizer (char_wb, ngram 2-4)
                         - حساب cosine similarity
  -> rag_service.py:205 _build_messages() — بناء الـ prompt
  -> provider_client.py:100  get_enabled_provider() — أول مزود مفعّل من DB
  -> provider_client.py:282  client.chat.completions.create() — استدعاء API الخارجي
  -> ai.py:159-161      log_ai_usage()
  -> ai.py:164-165      _save_chat_message() x2 (user + assistant)
  -> ai.py:170-171      return AIResult(answer, sources=[], conversation_id)
  (عند الخطأ: ai.py:172-178 استرداد الرصيد — add_credits())
```

---

## 3. مرجع الـ APIs

> FastAPI يولّد تلقائياً Swagger UI على `/docs` و OpenAPI JSON على `/openapi.json`.

### 3.1 المصادقة

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| POST | `/auth/register` | عام | تسجيل مستخدم جديد + JWT |
| POST | `/auth/login` | عام | تسجيل الدخول + JWT |
| PUT | `/auth/me/language` |Authenticated | تغيير اللغة |
| PUT | `/auth/me/onboarding-complete` |Authenticated | إنهاء Onboarding |

### 3.2 المستخدمون

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| GET | `/api/users/me` |Authenticated | ملفي الشخصي |
| GET | `/api/users` |Authenticated | قائمة المستخدمين |
| GET | `/api/users/{user_id}` |Authenticated | تفاصيل مستخدم |
| PUT | `/api/users/{user_id}` |Authenticated | تعديل مستخدم |

### 3.3 الكورسات

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| GET | `/api/courses` |authenticated | قائمة الكورسات |
| GET | `/api/courses/my-courses` |authenticated | كورساتي (المؤلف) |
| GET | `/api/courses/{id}` |authenticated | تفاصيل كورس |
| POST | `/api/courses` |teacher/admin | إنشاء كورس |
| PUT | `/api/courses/{id}` |teacher/admin | تعديل كورس |
| POST | `/api/courses/{id}/enroll` |authenticated | تسجيل مجاني |
| GET | `/api/courses/{id}/enrollments` |teacher | قائمة المسجلين |
| POST | `/api/courses/{id}/modules` |teacher | إنشاء وحدة |
| POST | `/api/courses/modules/{id}/lessons` |teacher | إنشاء درس |
| PUT | `/api/courses/{id}/price` |teacher | تحديث السعر |
| POST | `/api/courses/{id}/purchase` |authenticated | شراء كورس بالـ DT |
| GET | `/api/courses/my-sales` |teacher | مبيعاتي |
| POST | `/api/courses/{id}/refund-request` |authenticated | طلب استرداد |

### 3.4 الكتالوج العام

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| GET | `/catalog/courses` | عام | بحث الكتالوج |
| GET | `/catalog/courses/{slug}` | عام | تفاصيل كورس عام |
| GET | `/catalog/stats` | عام | إحصائيات |
| GET | `/catalog/categories` | عام | التصنيفات |

### 3.5 الطالب (Learner)

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| GET | `/api/learner/courses/{id}/preview` |authenticated | معاينة كورس |
| GET | `/api/learner/courses` |authenticated | كورساتي المسجلة |
| GET | `/api/learner/catalog` |authenticated | كتالوج الطالب |
| GET | `/api/learner/courses/{id}` |authenticated | تفاصيل كورس مسجل |
| GET | `/api/learner/courses/{id}/syllabus` |authenticated | المنهج |
| POST | `/api/learner/courses/{id}/enroll` |authenticated | تسجيل في كورس |
| GET | `/api/learner/my-courses` |authenticated | كورساتي |
| GET | `/api/learner/lessons/{id}` |authenticated | محتوى درس |
| POST | `/api/learner/lessons/{id}/progress` |authenticated | تسجيل تقدم |
| POST | `/api/learner/quizzes/{id}/start` |authenticated | بدء اختبار |
| GET | `/api/learner/quizzes/{id}` |authenticated | عرض اختبار |
| POST | `/api/learner/quizzes/{id}/submit` |authenticated | تسليم اختبار |
| POST | `/api/learner/quiz-attempts/{id}/submit` |authenticated | تسليم محاولة |
| GET | `/api/learner/certificates` |authenticated | شهاداتي |
| GET | `/api/learner/certificates/{id}` |authenticated | تفاصيل شهادة |
| GET | `/api/learner/courses/{id}/certificate` |authenticated | شهادة كورس |
| POST | `/api/learner/lessons/{id}/notes` |authenticated | إضافة ملاحظة |
| GET | `/api/learner/lessons/{id}/notes` |authenticated | ملاحظاتي |
| POST | `/api/learner/lessons/{id}/bookmarks` |authenticated | إضافة إشارة مرجعية |
| GET | `/api/learner/lessons/{id}/bookmarks` |authenticated | إشاراتي المرجعية |
| POST | `/api/learner/verify-identity` |authenticated | التحقق من الهوية |
| GET | `/api/learner/verify-identity/status` |authenticated | حالة التحقق |
| GET | `/api/learner/subscription/status` |authenticated | حالة الاشتراك |
| GET | `/api/learner/dashboard` |authenticated | Dashboard الطالب |
| GET | `/api/learner/recommended-path` |authenticated | المسار المُوصى به |
| GET | `/api/learner/daily-objective` |authenticated | الهدف اليومي |

### 3.6 AI

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| POST | `/api/ai/ask` |authenticated | سؤال AI Tutor |
| POST | `/api/ai/explain` |authenticated | شرح مفهوم |
| POST | `/api/ai/correct` |authenticated | تصحيح إجابة |
| POST | `/api/ai/quiz` |authenticated | توليد اختبار |
| POST | `/api/ai/exercises` |authenticated | توليد تمارين |
| POST | `/api/ai/ingest/pdf` |authenticated | استيراد PDF إلى RAG |
| POST | `/api/ai/ingest/text` |authenticated | استيراد نص إلى RAG |
| POST | `/api/ai/ingest/lesson/{id}` |authenticated | استيراد درس إلى RAG |
| GET | `/api/ai/usage` |authenticated | سجل الاستخدام |
| GET | `/api/ai/stats` |authenticated | إحصائيات AI |
| POST | `/api/ai/generate` |authenticated | توليد محتوى عام |
| GET | `/api/ai/history` |authenticated | سجل المحادثات |

### 3.7 مُصنع AI (AI Factory)

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| POST | `/api/admin/ai-factory/generate-plan` | admin | توليد خطة كورس |
| POST | `/api/admin/ai-factory/generate-content-stream` | admin | توليد محتوى (SSE) |
| POST | `/api/admin/ai-factory/generate-quiz` | admin | توليد اختبار |
| POST | `/api/admin/ai-factory/generate-media-prompts` | admin | توليد وسائط |
| POST | `/api/admin/ai-factory/generate-image` | admin | توليد صورة |
| POST | `/api/admin/ai-factory/save-image-to-bundle` | admin | حفظ صورة |
| POST | `/api/admin/ai-factory/generate-bundle` | admin | توليد حزمة كاملة |
| POST | `/api/admin/ai-factory/publish` | admin | نشر الكورس |
| POST | `/api/admin/ai-factory/preview` | admin | معاينة |
| GET | `/api/admin/ai-factory/rag-debug` | admin | تشخيص RAG |

### 3.8 المحفظة والباقات والاشتراكات

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| GET | `/api/wallet/balance` |authenticated | رصيد المحفظة |
| GET | `/api/wallet/history` |authenticated | سجل المعاملات |
| POST | `/api/wallet/purchase` |authenticated | شراء DT |
| GET | `/api/packs` |authenticated | قائمة الباقات |
| GET | `/api/packs/{id}` |authenticated | تفاصيل باقة |
| POST | `/api/packs/{id}/purchase` |authenticated | شراء باقة |
| GET | `/api/subscriptions/plans` |authenticated | الخطط المتاحة |
| POST | `/api/subscriptions/checkout` |authenticated | إنشاء جلسة Stripe |
| GET | `/api/subscriptions/current` |authenticated | اشتراكي الحالي |
| POST | `/api/subscriptions/webhook` | عام (Stripe) | Webhook Stripe |

### 3.9 المدير العام (Admin)

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| GET | `/api/admin/dashboard` |admin | إحصائيات Dashboard |
| POST | `/api/admin/schools` |admin | إنشاء مدرسة |
| GET | `/api/admin/schools` |admin | قائمة المدارس |
| PUT | `/api/admin/schools/{id}` |admin | تعديل مدرسة |
| DELETE | `/api/admin/schools/{id}` |admin | حذف مدرسة |
| GET | `/api/admin/users` |admin | قائمة المستخدمين |
| POST | `/api/admin/users` |admin | إنشاء مستخدم |
| PUT | `/api/admin/users/{id}` |admin | تعديل مستخدم |
| DELETE | `/api/admin/users/{id}` |admin | حذف مستخدم |
| PUT | `/api/admin/users/{id}/toggle-active` |admin | تفعيل/تعطيل |
| PUT | `/api/admin/users/{id}/change-role` |admin | تغيير الدور |
| GET | `/api/admin/analytics/overview` |admin | نظرة عامة |
| GET | `/api/admin/analytics/revenue` |admin | تحليلات الإيرادات |
| GET | `/api/admin/audit-logs` |admin | سجل التدقيق |
| POST | `/api/admin/school/packs/purchase` |admin | شراء باقة مدرسية |
| GET | `/api/admin/school/packs/active` |admin | الباقات النشطة |
| POST | `/api/admin/import-students` |admin | استيراد طلاب |

### 3.10 المعلم والمسارات التكيفية والgamification

| الطريقة | المسار | الدور | الوصف |
|---------|--------|-------|-------|
| GET | `/api/teacher/classes` |teacher | فئاتي |
| POST | `/api/teacher/classes` |teacher | إنشاء فئة |
| PUT | `/api/teacher/classes/{id}` |teacher | تعديل فئة |
| DELETE | `/api/teacher/classes/{id}` |teacher | حذف فئة |
| POST | `/api/teacher/classes/{id}/enroll` |teacher | تسجيل طالب |
| GET | `/api/teacher/classes/{id}/students` |teacher | قائمة الطلاب |
| GET | `/api/pathway/mon-parcours` |authenticated | مساري الشخصي |
| POST | `/api/pathway/auto-enroll-from-test` |authenticated | تسجيل تلقائي من اختبار |
| POST | `/api/pathway/enroll-pathway` |authenticated | تسجيل في مسار |
| GET | `/api/gamification/badges` |authenticated | الشارات |
| POST | `/api/gamification/badges/check` |authenticated | فحص الشارات |
| GET | `/api/gamification/streak` |authenticated | السلسلة اليومية |
| GET | `/api/learner/goals` |authenticated | أهدافي |
| POST | `/api/learner/goals/monthly` |authenticated | إنشاء هدف شهري |
| GET | `/api/parents/me/enfants` |parent | أطفالي |
| GET | `/api/parents/me/dashboard` |parent | Dashboard ولي الأمر |
| POST | `/api/parents/me/enfants/lier` |parent | ربط طالب |
| GET | `/api/placement/tests` |authenticated | اختبارات التقييم |
| POST | `/api/placement/tests/{id}/submit` |authenticated | تسليم اختبار |
| GET | `/api/inbox/messages` |authenticated | الرسائل |
| GET | `/api/conversations` |authenticated | المحادثات |
| POST | `/api/conversations/{id}/messages` |authenticated | إرسال رسالة |

---

## 4. قرارات التصميم (ADR)

### ADR-001: Multi-tenancy عبر school_id
- **السياق**: المنصة تخدم عدة مدارس في نفس قاعدة البيانات
- **القرار**: `school_id` كعمود في كل جدول + event listener SQLAlchemy يُضيف فلتر تلقائي
- **البدائل**: schema منفصل لكل مدرسة (لم يُستخدم — تكلفة عالية)
- **القيود**: لا يوجد row-level security على مستوى DB

### ADR-002: Wallet Ledger Append-Only
- **السياق**: المحفظة تحتاج تتبعاً شاملاً لجميع المعاملات
- **القرار**: `WalletTransaction` append-only مع `Numeric(10,2)`. الأرصدة محسوبة دائماً من ledger
- **Alternatives**: جدول `Wallet` مع رصيد mutable (متاح كعمود deprecated)
- **القيود**: أداء أقل للحسابات الكبيرة

### ADR-003: JWT بدون Refresh Token
- **القرار**: JWT واحد مع صلاحية 24 ساعة فقط
- **البدائل**: نظام refresh token (لم يُستخدم)
- **القيود**: المستخدمون يُسجلون الدخول مرة كل 24 ساعة

### ADR-004: RAG عبر TF-IDF
- **القرار**: TF-IDF (scikit-learn) بدون خدمة خارجية
- **البدائل**: FAISS (غير مثبت)، embeddings API (quota مُنفد)
- **القيود**: لا يوجد persistent index

### ADR-005: 8 موفري AI
- **القرار**: دعم 8 موفريين مع fallback
- **البدائل**: مزود واحد فقط
- **القيود**: تعقيد الصيانة

### ADR-006: لا يوجد Alembic
- **القرار**: SQL مباشر في `backend/migrations/` + `Base.metadata.create_all()`
- **البدائل**: Alembic (موجود في Dockerfile لكن غير مستخدم)
- **القيود**: لا يوجد versioning للـ schema

### ADR-007: Debtor Atomic commit
- **القرار**: `debit_dt(commit=False)` + `db.commit()` واحد من Caller
- **البدائل**: commit منفصل لكل عملية
- **القيود**: لا يوجد distributed transaction

### ADR-008: Statut pédagogique = Always Recalculated
- **القرار**: `LearningGoal.statut` لا يُخزن — يُحسب دائماً من القيم الحالية
- **البدائل**: تخزين الحالة مع تحديث دوري

### ADR-009: Pack Découverte = No Auto-Generated Goals
- **القرار**: لا توجد أهداف مُولّدة تلقائياً لمستخدمي باقة Découverte

### ADR-010: Tenant Filter Suppression pour Packs Individuels
- **القرار**: `has_course_access()` يكبح فلتر Tenant للـ PackPurchase مع `school_id=None`

### ADR-011: Navigation 5 Sections pour Étudiant
- **القرار**: Sidebar مُقسّم إلى 5 أقسام (Accueil/Parcours/IA/Objectifs/Profil)

### ADR-012: Commission Rate = Decimal
- **القرار**: `commission_rate` يُقسم على `Decimal("100")` وليس `100` (float)

### ADR-013: pg8000 Enum = UPPERCASE
- **القرار**: قواعد DB تستخدم UPPERCASE values

### ADR-014: No Level-Up Check in Course Purchase
- **القرار**: لا يوجد فحص level_up في تدفق الشراء

---

# PARTIE 2 — ARCHITECTURE SYSTÈME (Français)

---

## 1. Diagramme des Composants

```
┌──────────────────────────────────────────────────────────────────┐
│                       Navigateur / App                           │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────┐  │
│  │  Interface Web   │   │  Application     │   │  Swagger UI  │  │
│  │  React + Vite    │   │  Flutter         │   │  /docs       │  │
│  └────────┬─────────┘   └────────┬─────────┘   └──────┬───────┘  │
└───────────┼──────────────────────┼─────────────────────┼──────────┘
            │  REST API            │  REST API            │  REST API
            ▼                      ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11+)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Auth     │  │ Routers  │  │ Services │  │ Moteur RAG       │  │
│  │ JWT      │  │ (30+)    │  │ (18)     │  │ TF-IDF + API    │  │
│  │ bcrypt   │  │          │  │          │  │ externes          │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│  ┌────┴─────────────┴─────────────┴──────────────────┴─────────┐  │
│  │                    SQLAlchemy ORM                            │  │
│  │  Multi-tenant : event listener + ContextVar                 │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────────┘
                              │  SQL
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PostgreSQL 15                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  50+ tables — multi-tenant via school_id                 │    │
│  │  Numeric(10,2) pour champs monétaires                    │    │
│  │  WalletTransaction (append-only ledger)                  │    │
│  └──────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Index FAISS (fichiers JSON dans filesystem)             │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Description des Composants

| Composant | Rôle | Communique avec |
|-----------|------|-----------------|
| **Frontend React/Vite** | Interface utilisateur principale | Backend via REST API |
| **App Flutter** | Application mobile (en développement) | Backend via REST API |
| **Backend FastAPI** | Serveur API + logique métier + RBAC + Moteur RAG | PostgreSQL, FAISS, fournisseurs AI externes |
| **PostgreSQL 15** | Base de données principale | Backend via SQLAlchemy |
| **Index FAISS** | Index de recherche sémantique (TF-IDF) | Backend via embeddings_service |
| **Fournisseurs AI externes** | Modèle de langage pour générer les réponses | Backend via provider_client.py |

### Ce qui N'EXISTE PAS

- Pas de message queue (RabbitMQ, Redis pub/sub)
- Pas de cache Redis en production
- Pas de service de monitoring séparé
- Pas de CDN ou load balancer séparé

---

## 2. Flux de Données

### 2.1 Flux d'Authentification

```
POST /auth/login (email + password)
  -> auth.py:234        login() reçoit OAuth2PasswordRequestForm
  -> auth.py:240        Requête DB par email
  -> auth.py:248-254    Vérification lockout (5 échecs = lock 15 min)
  -> security.py:3-7    verify_password() — bcrypt.checkpw()
  -> auth.py:267-268    Reset compteur échecs
  -> auth.py:272        Mise à jour last_login
  -> auth.py:23-30      create_access_token() — JWT HS256
                         Payload : {sub: user_id, school_id, exp: +24h}
  -> auth.py:275        return {"access_token": "...", "token_type": "bearer"}
```

**Validation JWT** : `get_current_user()` dans `auth.py:41-76` décode le JWT, extrait user_id, récupère l'utilisateur de DB. ContextVar `current_tenant_id` défini automatiquement.

### 2.2 Flux d'Achat de Cours

```
POST /api/cours/{course_id}/purchase
  -> courses.py:318     Requête cours en DB
  -> courses.py:322-323 Vérifie prix > 0
  -> courses.py:326-331 Vérifie pas déjà acheté
  -> courses.py:335     get_dt_balance() — somme du ledger
  -> courses.py:336-340 Vérifie solde vs prix → 402 si insuffisant
  -> courses.py:345     debit_dt(db, user_id, course.price, commit=False)
                         wallet.py:135-148: crée WalletTransaction négatif
  -> courses.py:350-360 Crée Transaction (COURSE_PURCHASE)
  -> courses.py:363-365 Calcule commission: price * (commission_rate / Decimal("100"))
  -> courses.py:367-377 Crée CoursePurchase
  -> courses.py:380-384 Crée CourseEnrollment (inscription auto)
  -> courses.py:385     db.commit() — COMMIT ATOMIQUE unique
  -> courses.py:389-395 Notification auteur via notify_purchase()
  -> courses.py:397-404 return {purchase_id, amount_paid, remaining_balance}
```

### 2.3 Flux de Question AI Tutor

```
POST /api/ai/ask {question, conversation_id?}
  -> ai.py:122          check_ai_rate_limit(user_id, "ai_ask") — 30 req/min
  -> ai.py:125          _validate_school_id()
  -> wallet.py:38       estimate_cost(AI_ASK, len(question)) ≈ 2 credits
  -> wallet.py:96-99    get_total_balance() — somme tous les pools
  -> ai.py:131-136      Solde >= coût ? Sinon 402
  -> wallet.py:182-247  consume_credits() — débit par pools par priorité
                         (SUBSCRIPTION → SCHOOL_ALLOCATED → TRIAL → PURCHASED)
  -> ai.py:143          RAGService(db=db)
  -> ai.py:148-149      _get_or_create_conversation()
  -> ai.py:152          _load_conversation_history() — 20 derniers messages
  -> rag_service.py:362 ask_tutor() → generate(mode="tutor")
  -> rag_service.py:197 retrieve_context(school_id, prompt, k=5)
  -> embeddings_service.py:120-155 similarity_search()
                         TF-IDF (char_wb, ngram 2-4) + cosine similarity
  -> rag_service.py:205 _build_messages() — system prompt + context + question
  -> provider_client.py:100  get_enabled_provider() — premier fournisseur activé
  -> provider_client.py:282  client.chat.completions.create() — appel API externe
  -> ai.py:159-161      log_ai_usage()
  -> ai.py:164-165      _save_chat_message() x2
  -> ai.py:170-171      return AIResult(answer, sources=[], conversation_id)
  (erreur: ai.py:172-178 remboursement via add_credits())
```

---

## 3. Référence des APIs

> FastAPI génère automatiquement Swagger UI sur `/docs` et OpenAPI JSON sur `/openapi.json`.

### 3.1 Authentification

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| POST | `/auth/register` | public | Inscription + JWT |
| POST | `/auth/login` | public | Connexion + JWT |
| PUT | `/auth/me/language` | Authentifié | Changer langue |
| PUT | `/auth/me/onboarding-complete` | Authentifié | Terminer Onboarding |

### 3.2 Utilisateurs

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/users/me` | Authentifié | Mon profil |
| GET | `/api/users` | Authentifié | Liste utilisateurs |
| GET | `/api/users/{id}` | Authentifié | Détail utilisateur |
| PUT | `/api/users/{id}` | Authentifié | Modifier utilisateur |

### 3.3 Cours

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/courses` | Authentifié | Liste cours |
| GET | `/api/courses/my-courses` | Authentifié | Mes cours (auteur) |
| GET | `/api/courses/{id}` | Authentifié | Détail cours |
| POST | `/api/courses` | teacher/admin | Créer cours |
| PUT | `/api/courses/{id}` | teacher/admin | Modifier cours |
| POST | `/api/courses/{id}/enroll` | Authentifié | Inscription gratuite |
| GET | `/api/courses/{id}/enrollments` | teacher | Liste inscrits |
| POST | `/api/courses/{id}/modules` | teacher | Créer module |
| POST | `/api/courses/modules/{id}/lessons` | teacher | Créer leçon |
| PUT | `/api/courses/{id}/price` | teacher | Mettre à jour prix |
| POST | `/api/courses/{id}/purchase` | Authentifié | Acheter cours (DT) |
| GET | `/api/courses/my-sales` | teacher | Mes ventes |
| POST | `/api/courses/{id}/refund-request` | Authentifié | Demande remboursement |

### 3.4 Catalogue Public

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/catalog/courses` | public | Recherche catalogue |
| GET | `/catalog/courses/{slug}` | public | Détail cours public |
| GET | `/catalog/stats` | public | Statistiques |
| GET | `/catalog/categories` | public | Catégories |

### 3.5 Étudiant (Learner)

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/learner/courses/{id}/preview` | Authentifié | Aperçu cours |
| GET | `/api/learner/courses` | Authentifié | Mes cours inscrits |
| GET | `/api/learner/catalog` | Authentifié | Catalogue étudiant |
| GET | `/api/learner/courses/{id}` | Authentifié | Détail cours inscrit |
| GET | `/api/learner/courses/{id}/syllabus` | Authentifié | Syllabus |
| POST | `/api/learner/courses/{id}/enroll` | Authentifié | S'inscrire |
| GET | `/api/learner/my-courses` | Authentifié | Mes cours |
| GET | `/api/learner/lessons/{id}` | Authentifié | Contenu leçon |
| POST | `/api/learner/lessons/{id}/progress` | Authentifié | Enregistrer progrès |
| POST | `/api/learner/quizzes/{id}/start` | Authentifié | Commencer quiz |
| GET | `/api/learner/quizzes/{id}` | Authentifié | Voir quiz |
| POST | `/api/learner/quizzes/{id}/submit` | Authentifié | Soumettre quiz |
| POST | `/api/learner/quiz-attempts/{id}/submit` | Authentifié | Soumettre tentative |
| GET | `/api/learner/certificates` | Authentifié | Mes certificats |
| GET | `/api/learner/certificates/{id}` | Authentifié | Détail certificat |
| GET | `/api/learner/courses/{id}/certificate` | Authentifié | Certificat cours |
| POST | `/api/learner/lessons/{id}/notes` | Authentifié | Ajouter note |
| GET | `/api/learner/lessons/{id}/notes` | Authentifié | Mes notes |
| POST | `/api/learner/lessons/{id}/bookmarks` | Authentifié | Ajouter signet |
| GET | `/api/learner/lessons/{id}/bookmarks` | Authentifié | Mes signets |
| POST | `/api/learner/verify-identity` | Authentifié | Vérifier identité |
| GET | `/api/learner/verify-identity/status` | Authentifié | Statut vérification |
| GET | `/api/learner/subscription/status` | Authentifié | Statut abonnement |
| GET | `/api/learner/dashboard` | Authentifié | Dashboard |
| GET | `/api/learner/recommended-path` | Authentifié | Parcours recommandé |
| GET | `/api/learner/daily-objective` | Authentifié | Objectif du jour |

### 3.6 AI

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| POST | `/api/ai/ask` | Authentifié | Question AI Tutor |
| POST | `/api/ai/explain` | Authentifié | Expliquer concept |
| POST | `/api/ai/correct` | Authentifié | Corriger réponse |
| POST | `/api/ai/quiz` | Authentifié | Générer quiz |
| POST | `/api/ai/exercises` | Authentifié | Générer exercices |
| POST | `/api/ai/ingest/pdf` | Authentifié | Importer PDF vers RAG |
| POST | `/api/ai/ingest/text` | Authentifié | Importer texte vers RAG |
| POST | `/api/ai/ingest/lesson/{id}` | Authentifié | Importer leçon vers RAG |
| GET | `/api/ai/usage` | Authentifié | Journal d'utilisation |
| GET | `/api/ai/stats` | Authentifié | Statistiques AI |
| POST | `/api/ai/generate` | Authentifié | Générer contenu |
| GET | `/api/ai/history` | Authentifié | Historique conversations |

### 3.7 AI Factory (Admin)

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| POST | `/api/admin/ai-factory/generate-plan` | admin | Générer plan cours |
| POST | `/api/admin/ai-factory/generate-content-stream` | admin | Générer contenu (SSE) |
| POST | `/api/admin/ai-factory/generate-quiz` | admin | Générer quiz |
| POST | `/api/admin/ai-factory/generate-media-prompts` | admin | Générer médias |
| POST | `/api/admin/ai-factory/generate-image` | admin | Générer image |
| POST | `/api/admin/ai-factory/save-image-to-bundle` | admin | Sauvegarder image |
| POST | `/api/admin/ai-factory/generate-bundle` | admin | Générer bundle complet |
| POST | `/api/admin/ai-factory/publish` | admin | Publier cours |
| POST | `/api/admin/ai-factory/preview` | admin | Aperçu cours |
| GET | `/api/admin/ai-factory/rag-debug` | admin | Diagnostic RAG |

### 3.8 Construction de Cours (Admin)

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/admin/courses` | Authentifié | Liste cours |
| POST | `/api/admin/courses` | Authentifié | Créer cours |
| PATCH | `/api/admin/courses/{id}` | Authentifié | Modifier cours |
| DELETE | `/api/admin/courses/{id}` | Authentifié | Supprimer cours |
| POST | `/api/admin/courses/{id}/publish` | Authentifié | Publier |
| POST | `/api/admin/courses/{id}/submit-for-review` | Authentifié | Soumettre à révision |
| POST | `/api/admin/courses/{id}/unpublish` | Authentifié | Dépublier |
| POST | `/api/admin/courses/{id}/archive` | Authentifié | Archiver |
| POST | `/api/admin/courses/{id}/duplicate` | Authentifié | Dupliquer |
| POST | `/api/admin/courses/{id}/reorder` | Authentifié | Réordonner |
| GET | `/api/admin/courses/{id}/preview` | Authentifié | Aperçu |
| GET | `/api/admin/courses/{id}/analytics` | Authentifié | Analytiques |
| GET | `/api/admin/courses/{id}/chapters` | Authentifié | Chapitres |
| POST | `/api/admin/courses/{id}/chapters` | Authentifié | Créer chapitre |
| GET | `/api/admin/chapters` | Authentifié | Liste chapitres |
| POST | `/api/admin/chapters` | Authentifié | Créer chapitre |
| PATCH | `/api/admin/chapters/{id}` | Authentifié | Modifier chapitre |
| DELETE | `/api/admin/chapters/{id}` | Authentifié | Supprimer chapitre |
| POST | `/api/admin/chapters/reorder` | Authentifié | Réordonner |
| GET | `/api/admin/lessons` | Authentifié | Liste leçons |
| POST | `/api/admin/lessons` | Authentifié | Créer leçon |
| PATCH | `/api/admin/lessons/{id}` | Authentifié | Modifier leçon |
| DELETE | `/api/admin/lessons/{id}` | Authentifié | Supprimer leçon |
| POST | `/api/admin/lessons/reorder` | Authentifié | Réordonner |
| GET | `/api/admin/quizzes/lesson/{id}` | Authentifié | Quiz de leçon |
| POST | `/api/admin/quizzes` | Authentifié | Créer quiz |
| PATCH | `/api/admin/quizzes/{id}` | Authentifié | Modifier quiz |
| DELETE | `/api/admin/quizzes/{id}` | Authentifié | Supprimer quiz |
| POST | `/api/admin/quizzes/{id}/questions` | Authentifié | Ajouter question |
| PATCH | `/api/admin/quizzes/{id}/questions/{id}` | Authentifié | Modifier question |
| DELETE | `/api/admin/quizzes/{id}/questions/{id}` | Authentifié | Supprimer question |
| POST | `/api/admin/quizzes/{id}/questions/{id}/options` | Authentifié | Ajouter option |
| DELETE | `/api/admin/quizzes/{id}/questions/{id}/options/{id}` | Authentifié | Supprimer option |

### 3.9 Academy (Scope École)

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| POST | `/api/academy/courses` | Authentifié | Créer cours école |
| GET | `/api/academy/courses` | Authentifié | Cours de l'école |
| GET | `/api/academy/courses/{id}/detail` | Authentifié | Détail + has_course_access |
| PUT | `/api/academy/courses/{id}` | Authentifié | Modifier cours |
| PUT | `/api/academy/courses/{id}/publish` | Authentifié | Publier |
| DELETE | `/api/academy/courses/{id}` | Authentifié | Supprimer |
| POST | `/api/academy/modules` | Authentifié | Créer module |
| PUT | `/api/academy/modules/{id}` | Authentifié | Modifier module |
| DELETE | `/api/academy/modules/{id}` | Authentifié | Supprimer module |
| GET | `/api/academy/courses/{id}/modules` | Authentifié | Modules du cours |
| POST | `/api/academy/lessons` | Authentifié | Créer leçon |
| PUT | `/api/academy/lessons/{id}` | Authentifié | Modifier leçon |
| DELETE | `/api/academy/lessons/{id}` | Authentifié | Supprimer leçon |
| GET | `/api/academy/lessons/{id}/quizzes` | Authentifié | Quiz de leçon |
| POST | `/api/academy/quizzes` | Authentifié | Créer quiz |
| GET | `/api/academy/quizzes/{id}` | Authentifié | Détail quiz |
| GET | `/api/academy/quizzes/{id}/questions` | Authentifié | Questions quiz |
| POST | `/api/academy/quizzes/{id}/attempt` | Authentifié | Commencer tentative |
| PUT | `/api/academy/quizzes/{id}/attempt/{id}` | Authentifié | Soumettre tentative |
| GET | `/api/academy/quizzes/{id}/attempts` | Authentifié | Tentatives |
| GET | `/api/academy/my-courses` | Authentifié | Mes cours |

### 3.10 Portefeuille, Packs, Abonnements

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/wallet/balance` | Authentifié | Solde portefeuille |
| GET | `/api/wallet/history` | Authentifié | Historique transactions |
| POST | `/api/wallet/purchase` | Authentifié | Acheter DT |
| GET | `/api/packs` | Authentifié | Liste packs |
| GET | `/api/packs/{id}` | Authentifié | Détail pack |
| POST | `/api/packs/{id}/purchase` | Authentifié | Acheter pack |
| GET | `/api/subscriptions/plans` | Authentifié | Plans disponibles |
| POST | `/api/subscriptions/checkout` | Authentifié | Créer session Stripe |
| GET | `/api/subscriptions/current` | Authentifié | Mon abonnement |
| POST | `/api/subscriptions/webhook` | public (Stripe) | Webhook Stripe |

### 3.11 Administration

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/admin/dashboard` | admin | Stats Dashboard |
| POST | `/api/admin/schools` | admin | Créer école |
| GET | `/api/admin/schools` | admin | Liste écoles |
| PUT | `/api/admin/schools/{id}` | admin | Modifier école |
| DELETE | `/api/admin/schools/{id}` | admin | Supprimer école |
| POST | `/api/admin/schools/{id}/regenerate-invite-code` | admin | Régénérer code invite |
| GET | `/api/admin/users` | admin | Liste utilisateurs |
| GET | `/api/admin/users/{id}` | admin | Détail utilisateur |
| POST | `/api/admin/user-update` | admin | Mettre à jour utilisateur |
| POST | `/api/admin/users/{id}/reset-password` | admin | Réinitialiser mot de passe |
| POST | `/api/admin/users` | admin | Créer utilisateur |
| PUT | `/api/admin/users/{id}` | admin | Modifier utilisateur |
| DELETE | `/api/admin/users/{id}` | admin | Supprimer utilisateur |
| PUT | `/api/admin/users/{id}/balance` | admin | Modifier solde |
| PUT | `/api/admin/users/{id}/toggle-active` | admin | Activer/Désactiver |
| PUT | `/api/admin/users/{id}/change-role` | admin | Changer rôle |
| PUT | `/api/admin/users/{id}/approve` | admin | Approuver utilisateur |
| GET | `/api/admin/users-all` | admin | Tous les utilisateurs |
| GET | `/api/admin/classes` | admin | Liste classes |
| POST | `/api/admin/classes` | admin | Créer classe |
| POST | `/api/admin/enrollments` | admin | Inscription |
| GET | `/api/admin/enrollments` | admin | Liste inscriptions |
| GET | `/api/admin/analytics/overview` | admin | Vue d'ensemble |
| GET | `/api/admin/analytics/users` | admin | Analytiques utilisateurs |
| GET | `/api/admin/analytics/revenue` | admin | Revenus |
| GET | `/api/admin/analytics/enrollments` | admin | Analytiques inscriptions |
| GET | `/api/admin/analytics/api-costs` | admin | Coûts API |
| POST | `/api/admin/transactions` | admin | Créer transaction |
| GET | `/api/admin/transactions` | admin | Liste transactions |
| GET | `/api/admin/token-packages` | admin | Forfaits tokens |
| POST | `/api/admin/token-packages` | admin | Créer forfait |
| PUT | `/api/admin/token-packages/{id}` | admin | Modifier forfait |
| GET | `/api/admin/messages` | admin | Messages |
| POST | `/api/admin/messages` | admin | Envoyer message |
| DELETE | `/api/admin/messages/{id}` | admin | Supprimer message |
| POST | `/api/admin/broadcast` | admin | Diffusion |
| GET | `/api/admin/settings` | admin | Paramètres |
| PUT | `/api/admin/settings` | admin | Modifier paramètre |
| POST | `/api/admin/settings/apply` | admin | Appliquer paramètres |
| POST | `/api/admin/settings/test-provider` | admin | Tester fournisseur AI |
| PUT | `/api/admin/settings/token-limits` | admin | Limites tokens |
| GET | `/api/admin/settings/token-limits` | admin | Voir limites |
| POST | `/api/admin/settings/refresh-cache` | admin | Rafraîchir cache |
| GET | `/api/admin/wallets` | admin | Portefeuilles |
| POST | `/api/admin/wallets/{id}/add` | admin | Ajouter solde |
| POST | `/api/admin/wallets/{id}/deduct` | admin | Débiter solde |
| POST | `/api/admin/wallet/allocate` | admin | Allouer solde |
| GET | `/api/admin/wallet/consumption-report` | admin | Rapport consommation |
| GET | `/api/admin/wallet/margin-report` | admin | Rapport marge |
| GET | `/api/admin/stats/global` | admin | Statistiques globales |
| GET | `/api/admin/teacher-registrations` | admin | Inscriptions enseignants |
| POST | `/api/admin/teacher-registrations/{id}/review` | admin | Réviser inscription |
| POST | `/api/admin/teacher/duplicate-trial-content` | admin | Dupliquer contenu essai |
| GET | `/api/admin/verifications/pending` | admin | Vérifications en attente |
| POST | `/api/admin/verifications/{id}/review` | admin | Réviser vérification |
| GET | `/api/admin/courses/{id}/analytics` | admin | Analytiques cours |
| GET | `/api/admin/audit-logs` | admin | Journal d'audit |
| GET | `/api/admin/subscriptions/expiring` | admin | Abonnements expirants |
| POST | `/api/admin/subscriptions/check-expirations` | admin | Vérifier expirations |
| POST | `/api/admin/users/{id}/extend-subscription` | admin | Prolonger abonnement |
| POST | `/api/admin/school/packs/purchase` | admin | Achat pack école |
| GET | `/api/admin/school/packs/active` | admin | Packs actifs école |
| GET | `/api/admin/packs/revenue-report` | admin | Rapport revenus packs |
| POST | `/api/admin/import-students` | admin | Importer étudiants |
| POST | `/api/admin/import-students/upload` | admin | Upload fichier import |

### 3.12 Enseignant

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/teacher/classes` | teacher | Mes classes |
| POST | `/api/teacher/classes` | teacher | Créer classe |
| GET | `/api/teacher/classes/{id}` | teacher | Détail classe |
| PUT | `/api/teacher/classes/{id}` | teacher | Modifier classe |
| DELETE | `/api/teacher/classes/{id}` | teacher | Supprimer classe |
| POST | `/api/teacher/classes/{id}/enroll` | teacher | Inscrire étudiant |
| DELETE | `/api/teacher/classes/{id}/students/{id}` | teacher | Retirer étudiant |
| GET | `/api/teacher/classes/{id}/students` | teacher | Étudiants classe |
| GET | `/api/teacher/classes/{id}/available-students` | teacher | Étudiants disponibles |
| POST | `/api/teacher/classes/{id}/assignments` | teacher | Créer devoir |

### 3.13 Parcours Adaptatif

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/pathway/eleves/{id}/profil-assimilation` | Authentifié | Profil assimilation |
| POST | `/api/pathway/profils-assimilation` | Authentifié | Créer profil |
| POST | `/api/pathway/profils-assimilation/{id}/validation` | Authentifié | Valider profil |
| GET | `/api/pathway/enseignants/{id}/notifications-reorientation` | Authentifié | Notifications réorientation |
| GET | `/api/pathway/notions/{id}/statut-publication` | Authentifié | Statut publication |
| GET | `/api/pathway/eleves/{id}/acces-effectif` | Authentifié | Accès effectif |
| POST | `/api/pathway/scores` | Authentifié | Enregistrer score |
| POST | `/api/pathway/evaluer-reorientation` | Authentifié | Évaluer réorientation |
| GET | `/api/pathway/notions/{id}/contenu` | Authentifié | Contenu notion |
| GET | `/api/pathway/niveaux-etude` | Authentifié | Niveaux d'étude |
| POST | `/api/pathway/niveaux-etude` | Authentifié | Créer niveau |
| PUT | `/api/pathway/niveaux-etude/{id}` | Authentifié | Modifier niveau |
| DELETE | `/api/pathway/niveaux-etude/{id}` | Authentifié | Supprimer niveau |
| GET | `/api/pathway/matieres` | Authentifié | Matières |
| POST | `/api/pathway/matieres` | Authentifié | Créer matière |
| PUT | `/api/pathway/matieres/{id}` | Authentifié | Modifier matière |
| DELETE | `/api/pathway/matieres/{id}` | Authentifié | Supprimer matière |
| GET | `/api/pathway/chapter-pathways` | Authentifié | Parcours chapitres |
| POST | `/api/pathway/chapter-pathways` | Authentifié | Créer parcours |
| PUT | `/api/pathway/chapter-pathways/{id}` | Authentifié | Modifier parcours |
| DELETE | `/api/pathway/chapter-pathways/{id}` | Authentifié | Supprimer parcours |
| GET | `/api/pathway/notions-list` | Authentifié | Liste notions |
| POST | `/api/pathway/notions-list` | Authentifié | Créer notion |
| PUT | `/api/pathway/notions-list/{id}` | Authentifié | Modifier notion |
| DELETE | `/api/pathway/notions-list/{id}` | Authentifié | Supprimer notion |
| GET | `/api/pathway/contenus` | Authentifié | Contenus |
| POST | `/api/pathway/contenus` | Authentifié | Créer contenu |
| PUT | `/api/pathway/contenus/{id}` | Authentifié | Modifier contenu |
| DELETE | `/api/pathway/contenus/{id}` | Authentifié | Supprimer contenu |
| GET | `/api/pathway/catalog` | Authentifié | Catalogue parcours |
| GET | `/api/pathway/mon-parcours` | Authentifié | Mon parcours |
| POST | `/api/pathway/auto-enroll-from-test` | Authentifié | Inscription auto depuis test |
| POST | `/api/pathway/enroll-pathway` | Authentifié | S'inscrire au parcours |
| GET | `/api/pathway/specialites-pedagogiques` | Authentifié | Spécialités |
| POST | `/api/pathway/specialites-pedagogiques` | Authentifié | Créer spécialité |
| POST | `/api/pathway/responsables-pedagogiques` | Authentifié | Créer resp. pédagogique |
| GET | `/api/pathway/responsables-pedagogiques/{id}/contenus` | Authentifié | Contenus resp. |
| POST | `/api/pathway/contenus-notion/{id}/valider` | Authentifié | Valider contenu |
| POST | `/api/pathway/contenus-notion/{id}/rejeter` | Authentifié | Rejeter contenu |

### 3.14 Gamification, Objectifs, Parent, Placement, LMS, Messagerie, Médias, Logs, Conversations, Paiements

| Méthode | Chemin | Rôle requis | Description |
|---------|--------|-------------|-------------|
| GET | `/api/gamification/badges` | Authentifié | Badges |
| POST | `/api/gamification/badges/check` | Authentifié | Vérifier badges |
| GET | `/api/gamification/streak` | Authentifié | Série quotidienne |
| POST | `/api/gamification/streak/record` | Authentifié | Enregistrer jour |
| GET | `/api/gamification/rankings` | Authentifié | Classements |
| GET | `/api/learner/goals` | Authentifié | Mes objectifs |
| POST | `/api/learner/goals` | Authentifié | Créer objectif |
| GET | `/api/learner/goals/{id}` | Authentifié | Détail objectif |
| PUT | `/api/learner/goals/{id}` | Authentifié | Modifier objectif |
| POST | `/api/learner/goals/monthly` | Authentifié | Objectif mensuel |
| GET | `/api/pedagogical-lead/goals` | pedagogical_lead | Objectifs école |
| GET | `/api/parents/me/enfants` | parent | Mes enfants |
| GET | `/api/parents/me/dashboard` | parent | Dashboard parent |
| GET | `/api/parents/me/enfants/{id}/suivi` | parent | Suivi enfant |
| GET | `/api/parents/me/enfants/{id}/progression` | parent | Progression enfant |
| POST | `/api/parents/me/enfants/lier` | parent | Lier enfant |
| DELETE | `/api/parents/me/enfants/{id}/delier` | parent | Délier enfant |
| GET | `/api/placement/tests` | Authentifié | Tests de placement |
| GET | `/api/placement/tests/{id}` | Authentifié | Détail test |
| POST | `/api/placement/tests/{id}/submit` | Authentifié | Soumettre test |
| POST | `/api/lms/assignments` | teacher | Créer devoir |
| GET | `/api/lms/assignments` | teacher | Liste devoirs |
| GET | `/api/lms/assignments/{id}` | teacher | Détail devoir |
| PUT | `/api/lms/assignments/{id}` | teacher | Modifier devoir |
| DELETE | `/api/lms/assignments/{id}` | teacher | Supprimer devoir |
| POST | `/api/lms/assignments/{id}/submit` | Authentifié | Soumettre devoir |
| GET | `/api/lms/submissions` | teacher | Soumissions |
| GET | `/api/lms/submissions/{id}` | teacher | Détail soumission |
| PUT | `/api/lms/submissions/{id}/grade` | teacher | Noter |
| GET | `/api/lms/classes` | Authentifié | Classes |
| POST | `/api/lms/enrollments` | teacher | Inscription |
| GET | `/api/lms/enrollments` | teacher | Liste inscriptions |
| DELETE | `/api/lms/enrollments/{id}` | teacher | Supprimer inscription |
| GET | `/api/lms/my-classes` | teacher | Mes classes |
| GET | `/api/lms/progress` | Authentifié | Progrès |
| POST | `/api/lms/progress` | Authentifié | Enregistrer progrès |
| GET | `/api/lms/classes/{id}/available-students` | teacher | Étudiants disponibles |
| GET | `/api/lms/classes/{id}/students` | teacher | Étudiants classe |
| POST | `/api/lms/classes/{id}/assignments` | teacher | Devoirs classe |
| GET | `/api/lms/classes/{id}/assignments` | teacher | Devoirs classe |
| POST | `/api/lms/classes` | teacher | Créer classe |
| DELETE | `/api/lms/classes/{id}` | teacher | Supprimer classe |
| DELETE | `/api/lms/classes/{id}/students/{id}` | teacher | Retirer étudiant |
| GET | `/api/pedagogical/courses/pending` | pedagogical_admin | Cours à réviser |
| PUT | `/api/pedagogical/courses/{id}/review` | pedagogical_admin | Réviser cours |
| GET | `/api/pedagogical/reports` | pedagogical_admin | Rapports |
| POST | `/api/pedagogical/packs` | pedagogical_admin | Créer pack |
| PUT | `/api/pedagogical/packs/{id}/publish` | pedagogical_admin | Publier pack |
| GET | `/api/pedagogical-lead/progress-report` | pedagogical_lead | Rapport progression |
| PUT | `/api/pedagogical-lead/courses/{id}/review-local` | pedagogical_lead | Révision locale |
| POST | `/api/pedagogical-lead/escalate/{id}` | pedagogical_lead | Escalade |
| GET | `/api/pedagogical-lead/performance` | pedagogical_lead | Performance |
| GET | `/api/inbox/messages` | Authentifié | Messages |
| PUT | `/api/inbox/messages/{id}/read` | Authentifié | Marquer lu |
| GET | `/api/inbox/unread-count` | Authentifié | Nombre non lus |
| POST | `/api/admin/media/upload` | Authentifié | Upload fichier |
| GET | `/api/admin/media/files` | Authentifié | Liste fichiers |
| GET | `/api/admin/logs/errors` | admin | Journal erreurs |
| GET | `/api/admin/logs/audit` | admin | Journal audit |
| GET | `/api/conversations` | Authentifié | Conversations |
| GET | `/api/conversations/{id}` | Authentifié | Détail conversation |
| POST | `/api/conversations` | Authentifié | Créer conversation |
| POST | `/api/conversations/{id}/messages` | Authentifié | Envoyer message |
| DELETE | `/api/conversations/{id}` | Authentifié | Supprimer |
| DELETE | `/api/conversations` | Authentifié | Supprimer tout |
| GET | `/api/conversations/{id}/export/pdf` | Authentifié | Exporter PDF |
| GET | `/api/conversations/{id}/export/docx` | Authentifié | Exporter DOCX |
| POST | `/api/conversations/export/message/pdf` | Authentifié | Exporter message PDF |
| POST | `/api/conversations/export/message/docx` | Authentifié | Exporter message DOCX |
| POST | `/api/payments/stripe/checkout` | Authentifié | Créer session paiement |
| POST | `/api/payments/stripe/webhook` | public (Stripe) | Webhook Stripe |

---

## 4. Décisions de Conception (ADR)

### ADR-001 : Multi-tenancy par school_id
- **Contexte** : La plateforme dessert plusieurs écoles dans la même base de données
- **Décision** : Colonne `school_id` dans chaque table + event listener SQLAlchemy ajoutant un filtre automatique
- **Alternatives** : Schéma séparé par école (non retenu — coût élevé)
- **Limites** : Pas de row-level security au niveau DB

### ADR-002 : Wallet Ledger Append-Only
- **Contexte** : Le portefeuille nécessite un traçage complet
- **Décision** : `WalletTransaction` append-only avec `Numeric(10,2)`. Soldes toujours calculés depuis le ledger
- **Alternatives** : Table `Wallet` avec solde mutable (colonnes dépréciées `users.dt_balance`)
- **Limites** : Performance inférieure pour les grands volumes

### ADR-003 : JWT sans Refresh Token
- **Décision** : Un seul JWT avec validité 24h. Pas de refresh token
- **Alternatives** : Système de refresh token (non implémenté)
- **Limites** : Les utilisateurs se connectent une fois toutes les 24h

### ADR-004 : RAG via TF-IDF
- **Décision** : TF-IDF (scikit-learn) sans service externe
- **Alternatives** : FAISS (non installé), embeddings API (OpenAI — quota épuisé)
- **Limites** : Pas de persistent index

### ADR-005 : 8 Fournisseurs AI
- **Décision** : 8 fournisseurs supportés avec fallback
- **Alternatives** : Un seul fournisseur
- **Limites** : Complexité de maintenance

### ADR-006 : Pas d'Alembic
- **Décision** : SQL direct dans `backend/migrations/` + `Base.metadata.create_all()`
- **Alternatives** : Alembic (présent dans Dockerfile mais non utilisé)
- **Limites** : Pas de versioning du schéma

### ADR-007 : Commit Atomique pour Achats
- **Décision** : `debit_dt(commit=False)` + `db.commit()` unique côté Caller
- **Alternatives** : Commit séparé pour chaque opération
- **Limites** : Pas de distributed transaction

### ADR-008 : Statut Pédagogique = Toujours Recalculé
- **Décision** : `LearningGoal.statut` jamais stocké — toujours calculé
- **Alternatives** : Stockage de l'état avec mise à jour périodique

### ADR-009 : Pack Découverte = Pas d'Objectifs Auto-Générés
- **Décision** : Aucun objectif généré automatiquement pour les utilisateurs Pack Découverte

### ADR-010 : Suppression du Filtre Tenant pour Packs Individuels
- **Décision** : `has_course_access()` supprime le filtre Tenant pour les PackPurchase avec `school_id=None`

### ADR-011 : Navigation 5 Sections pour Étudiant
- **Décision** : Sidebar en 5 sections (Accueil/Parcours/IA/Objectifs/Profil) avec sections rétractables

### ADR-012 : Commission Rate = Decimal
- **Décision** : `commission_rate` divisé par `Decimal("100")` et non `100` (float)

### ADR-013 : pg8000 Enum = UPPERCASE
- **Décision** : Les enums DB utilisent des valeurs UPPERCASE

### ADR-014 : Pas de Vérification Level-Up à l'Achat
- **Décision** : Aucune vérification level_up dans le flux d'achat

---

# PARTIE 3 — SYSTEM ARCHITECTURE (English)

---

## 1. Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                       Browser / App                              │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────┐  │
│  │  Web Interface   │   │  Flutter App     │   │  Swagger UI  │  │
│  │  React + Vite    │   │  Mobile          │   │  /docs       │  │
│  └────────┬─────────┘   └────────┬─────────┘   └──────┬───────┘  │
└───────────┼──────────────────────┼─────────────────────┼──────────┘
            │  REST API            │  REST API            │  REST API
            ▼                      ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11+)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Auth     │  │ Routers  │  │ Services │  │ RAG Engine       │  │
│  │ JWT      │  │ (30+)    │  │ (18)     │  │ TF-IDF + API    │  │
│  │ bcrypt   │  │          │  │          │  │ externals        │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│  ┌────┴─────────────┴─────────────┴──────────────────┴─────────┐  │
│  │                    SQLAlchemy ORM                            │  │
│  │  Multi-tenant: event listener + ContextVar                  │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────────┘
                              │  SQL
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PostgreSQL 15                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  50+ tables — multi-tenant via school_id                 │    │
│  │  Numeric(10,2) for monetary fields                       │    │
│  │  WalletTransaction (append-only ledger)                  │    │
│  └──────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  FAISS Indexes (JSON files in filesystem)                │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component | Role | Communicates With |
|-----------|------|-------------------|
| **React/Vite Frontend** | Main UI — Dashboard, courses, AI, wallet, admin | Backend via REST API |
| **Flutter Mobile** | Mobile app (under development) | Backend via REST API |
| **FastAPI Backend** | API server + business logic + RBAC + RAG engine | PostgreSQL, FAISS, external AI providers |
| **PostgreSQL 15** | Primary database — all tables + ledger | Backend via SQLAlchemy |
| **FAISS Indexes** | Semantic search index (TF-IDF) — JSON files | Backend via embeddings_service |
| **External AI Providers** | LLM for generating responses | Backend via provider_client.py |

### What Does NOT Exist

- No message queue (RabbitMQ, Redis pub/sub)
- No Redis cache in production
- No separate monitoring service
- No CDN or separate load balancer

---

## 2. Data Flows

### 2.1 Authentication Flow

```
POST /auth/login (email + password)
  -> auth.py:234        login() receives OAuth2PasswordRequestForm
  -> auth.py:240        DB lookup by email
  -> auth.py:248-254    Account lockout check (5 failures = lock 15 min)
  -> security.py:3-7    verify_password() — bcrypt.checkpw()
  -> auth.py:267-268    Reset failure counter
  -> auth.py:272        Update last_login
  -> auth.py:23-30      create_access_token() — JWT HS256
                         Payload: {sub: user_id, school_id, exp: +24h}
  -> auth.py:275        return {"access_token": "...", "token_type": "bearer"}
```

**JWT Validation**: `get_current_user()` in `auth.py:41-76` decodes JWT, extracts user_id, fetches user from DB. ContextVar `current_tenant_id` set automatically.

### 2.2 Course Purchase Flow

```
POST /api/courses/{course_id}/purchase
  -> courses.py:318     Query course from DB
  -> courses.py:322-323 Verify price > 0
  -> courses.py:326-331 Verify not already purchased
  -> courses.py:335     get_dt_balance() — sum of WalletTransaction ledger
  -> courses.py:336-340 Check balance vs price → 402 if insufficient
  -> courses.py:345     debit_dt(db, user_id, course.price, commit=False)
                         wallet.py:135-148: creates negative WalletTransaction
  -> courses.py:350-360 Create Transaction (COURSE_PURCHASE)
  -> courses.py:363-365 Calculate commission: price * (commission_rate / Decimal("100"))
  -> courses.py:367-377 Create CoursePurchase
  -> courses.py:380-384 Create CourseEnrollment (auto-enroll)
  -> courses.py:385     db.commit() — SINGLE ATOMIC COMMIT
  -> courses.py:389-395 Notify course author via notify_purchase()
  -> courses.py:397-404 return {purchase_id, amount_paid, remaining_balance}
```

### 2.3 AI Tutor Question Flow

```
POST /api/ai/ask {question, conversation_id?}
  -> ai.py:122          check_ai_rate_limit(user_id, "ai_ask") — 30 req/min
  -> ai.py:125          _validate_school_id()
  -> wallet.py:38       estimate_cost(AI_ASK, len(question)) ≈ 2 credits
  -> wallet.py:96-99    get_total_balance() — sum all pools
  -> ai.py:131-136      Balance >= estimated? Otherwise 402
  -> wallet.py:182-247  consume_credits() — debit pools by priority:
                         SUBSCRIPTION → SCHOOL_ALLOCATED → TRIAL → PURCHASED
                         (with row-level lock via with_for_update())
  -> ai.py:143          RAGService(db=db)
  -> ai.py:148-149      _get_or_create_conversation()
  -> ai.py:152          _load_conversation_history() — last 20 messages
  -> rag_service.py:362 ask_tutor() → generate(mode="tutor")
  -> rag_service.py:197 retrieve_context(school_id, prompt, k=5)
  -> embeddings_service.py:120-155 similarity_search()
                         TF-IDF (char_wb, ngram 2-4) + cosine similarity
  -> rag_service.py:205 _build_messages() — system prompt + context + question
  -> provider_client.py:100  get_enabled_provider() — first enabled from DB
  -> provider_client.py:282  client.chat.completions.create() — external API call
  -> ai.py:159-161      log_ai_usage()
  -> ai.py:164-165      _save_chat_message() x2
  -> ai.py:170-171      return AIResult(answer, sources=[], conversation_id)
  (on error: ai.py:172-178 refund via add_credits())
```

---

## 3. API Reference

> FastAPI auto-generates Swagger UI at `/docs` and OpenAPI JSON at `/openapi.json`.

### 3.1 Authentication

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| POST | `/auth/register` | public | Register + JWT |
| POST | `/auth/login` | public | Login + JWT |
| PUT | `/auth/me/language` | Authenticated | Change language |
| PUT | `/auth/me/onboarding-complete` | Authenticated | Complete onboarding |

### 3.2 Users

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/users/me` | Authenticated | My profile |
| GET | `/api/users` | Authenticated | User list |
| GET | `/api/users/{id}` | Authenticated | User detail |
| PUT | `/api/users/{id}` | Authenticated | Update user |

### 3.3 Courses

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/courses` | Authenticated | Course list |
| GET | `/api/courses/my-courses` | Authenticated | My courses (author) |
| GET | `/api/courses/{id}` | Authenticated | Course detail |
| POST | `/api/courses` | teacher/admin | Create course |
| PUT | `/api/courses/{id}` | teacher/admin | Update course |
| POST | `/api/courses/{id}/enroll` | Authenticated | Free enrollment |
| GET | `/api/courses/{id}/enrollments` | teacher | Student list |
| POST | `/api/courses/{id}/modules` | teacher | Create module |
| POST | `/api/courses/modules/{id}/lessons` | teacher | Create lesson |
| PUT | `/api/courses/{id}/price` | teacher | Update price |
| POST | `/api/courses/{id}/purchase` | Authenticated | Purchase course (DT) |
| GET | `/api/courses/my-sales` | teacher | My sales |
| POST | `/api/courses/{id}/refund-request` | Authenticated | Refund request |

### 3.4 Public Catalog

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/catalog/courses` | public | Search catalog |
| GET | `/catalog/courses/{slug}` | public | Public course detail |
| GET | `/catalog/stats` | public | Catalog stats |
| GET | `/catalog/categories` | public | Categories |

### 3.5 Learner

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/learner/courses/{id}/preview` | Authenticated | Course preview |
| GET | `/api/learner/courses` | Authenticated | My enrolled courses |
| GET | `/api/learner/catalog` | Authenticated | Student catalog |
| GET | `/api/learner/courses/{id}` | Authenticated | Enrolled course detail |
| GET | `/api/learner/courses/{id}/syllabus` | Authenticated | Syllabus |
| POST | `/api/learner/courses/{id}/enroll` | Authenticated | Enroll in course |
| GET | `/api/learner/my-courses` | Authenticated | My courses |
| GET | `/api/learner/lessons/{id}` | Authenticated | Lesson content |
| POST | `/api/learner/lessons/{id}/progress` | Authenticated | Record progress |
| POST | `/api/learner/quizzes/{id}/start` | Authenticated | Start quiz |
| GET | `/api/learner/quizzes/{id}` | Authenticated | View quiz |
| POST | `/api/learner/quizzes/{id}/submit` | Authenticated | Submit quiz |
| POST | `/api/learner/quiz-attempts/{id}/submit` | Authenticated | Submit attempt |
| GET | `/api/learner/certificates` | Authenticated | My certificates |
| GET | `/api/learner/certificates/{id}` | Authenticated | Certificate detail |
| GET | `/api/learner/courses/{id}/certificate` | Authenticated | Course certificate |
| POST | `/api/learner/lessons/{id}/notes` | Authenticated | Add note |
| GET | `/api/learner/lessons/{id}/notes` | Authenticated | My notes |
| POST | `/api/learner/lessons/{id}/bookmarks` | Authenticated | Add bookmark |
| GET | `/api/learner/lessons/{id}/bookmarks` | Authenticated | My bookmarks |
| POST | `/api/learner/verify-identity` | Authenticated | Verify identity |
| GET | `/api/learner/verify-identity/status` | Authenticated | Verification status |
| GET | `/api/learner/subscription/status` | Authenticated | Subscription status |
| GET | `/api/learner/dashboard` | Authenticated | Student dashboard |
| GET | `/api/learner/recommended-path` | Authenticated | Recommended path |
| GET | `/api/learner/daily-objective` | Authenticated | Daily objective |

### 3.6 AI

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| POST | `/api/ai/ask` | Authenticated | AI Tutor question |
| POST | `/api/ai/explain` | Authenticated | Explain concept |
| POST | `/api/ai/correct` | Authenticated | Correct answer |
| POST | `/api/ai/quiz` | Authenticated | Generate quiz |
| POST | `/api/ai/exercises` | Authenticated | Generate exercises |
| POST | `/api/ai/ingest/pdf` | Authenticated | Ingest PDF to RAG |
| POST | `/api/ai/ingest/text` | Authenticated | Ingest text to RAG |
| POST | `/api/ai/ingest/lesson/{id}` | Authenticated | Ingest lesson to RAG |
| GET | `/api/ai/usage` | Authenticated | Usage history |
| GET | `/api/ai/stats` | Authenticated | AI stats |
| POST | `/api/ai/generate` | Authenticated | Generate content |
| GET | `/api/ai/history` | Authenticated | Conversation history |

### 3.7 AI Factory (Admin)

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| POST | `/api/admin/ai-factory/generate-plan` | admin | Generate course plan |
| POST | `/api/admin/ai-factory/generate-content-stream` | admin | Generate content (SSE) |
| POST | `/api/admin/ai-factory/generate-quiz` | admin | Generate quiz |
| POST | `/api/admin/ai-factory/generate-media-prompts` | admin | Generate media |
| POST | `/api/admin/ai-factory/generate-image` | admin | Generate image |
| POST | `/api/admin/ai-factory/save-image-to-bundle` | admin | Save image to bundle |
| POST | `/api/admin/ai-factory/generate-bundle` | admin | Generate full bundle |
| POST | `/api/admin/ai-factory/publish` | admin | Publish course |
| POST | `/api/admin/ai-factory/preview` | admin | Preview course |
| GET | `/api/admin/ai-factory/rag-debug` | admin | RAG debug |

### 3.8 Course Builder (Admin)

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/admin/courses` | Authenticated | Course list |
| POST | `/api/admin/courses` | Authenticated | Create course |
| PATCH | `/api/admin/courses/{id}` | Authenticated | Update course |
| DELETE | `/api/admin/courses/{id}` | Authenticated | Delete course |
| POST | `/api/admin/courses/{id}/publish` | Authenticated | Publish |
| POST | `/api/admin/courses/{id}/submit-for-review` | Authenticated | Submit for review |
| POST | `/api/admin/courses/{id}/unpublish` | Authenticated | Unpublish |
| POST | `/api/admin/courses/{id}/archive` | Authenticated | Archive |
| POST | `/api/admin/courses/{id}/duplicate` | Authenticated | Duplicate |
| POST | `/api/admin/courses/{id}/reorder` | Authenticated | Reorder |
| GET | `/api/admin/courses/{id}/preview` | Authenticated | Preview |
| GET | `/api/admin/courses/{id}/analytics` | Authenticated | Analytics |
| GET | `/api/admin/courses/{id}/chapters` | Authenticated | Chapters |
| POST | `/api/admin/courses/{id}/chapters` | Authenticated | Create chapter |
| GET | `/api/admin/chapters` | Authenticated | Chapter list |
| POST | `/api/admin/chapters` | Authenticated | Create chapter |
| PATCH | `/api/admin/chapters/{id}` | Authenticated | Update chapter |
| DELETE | `/api/admin/chapters/{id}` | Authenticated | Delete chapter |
| POST | `/api/admin/chapters/reorder` | Authenticated | Reorder |
| GET | `/api/admin/lessons` | Authenticated | Lesson list |
| POST | `/api/admin/lessons` | Authenticated | Create lesson |
| PATCH | `/api/admin/lessons/{id}` | Authenticated | Update lesson |
| DELETE | `/api/admin/lessons/{id}` | Authenticated | Delete lesson |
| POST | `/api/admin/lessons/reorder` | Authenticated | Reorder |
| GET | `/api/admin/quizzes/lesson/{id}` | Authenticated | Lesson quizzes |
| POST | `/api/admin/quizzes` | Authenticated | Create quiz |
| PATCH | `/api/admin/quizzes/{id}` | Authenticated | Update quiz |
| DELETE | `/api/admin/quizzes/{id}` | Authenticated | Delete quiz |
| POST | `/api/admin/quizzes/{id}/questions` | Authenticated | Add question |
| PATCH | `/api/admin/quizzes/{id}/questions/{id}` | Authenticated | Update question |
| DELETE | `/api/admin/quizzes/{id}/questions/{id}` | Authenticated | Delete question |
| POST | `/api/admin/quizzes/{id}/questions/{id}/options` | Authenticated | Add option |
| DELETE | `/api/admin/quizzes/{id}/questions/{id}/options/{id}` | Authenticated | Delete option |

### 3.9 Academy (School-Scoped)

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| POST | `/api/academy/courses` | Authenticated | Create school course |
| GET | `/api/academy/courses` | Authenticated | School courses |
| GET | `/api/academy/courses/{id}/detail` | Authenticated | Detail + has_course_access |
| PUT | `/api/academy/courses/{id}` | Authenticated | Update course |
| PUT | `/api/academy/courses/{id}/publish` | Authenticated | Publish |
| DELETE | `/api/academy/courses/{id}` | Authenticated | Delete |
| POST | `/api/academy/modules` | Authenticated | Create module |
| PUT | `/api/academy/modules/{id}` | Authenticated | Update module |
| DELETE | `/api/academy/modules/{id}` | Authenticated | Delete module |
| GET | `/api/academy/courses/{id}/modules` | Authenticated | Course modules |
| POST | `/api/academy/lessons` | Authenticated | Create lesson |
| PUT | `/api/academy/lessons/{id}` | Authenticated | Update lesson |
| DELETE | `/api/academy/lessons/{id}` | Authenticated | Delete lesson |
| GET | `/api/academy/lessons/{id}/quizzes` | Authenticated | Lesson quizzes |
| POST | `/api/academy/quizzes` | Authenticated | Create quiz |
| GET | `/api/academy/quizzes/{id}` | Authenticated | Quiz detail |
| GET | `/api/academy/quizzes/{id}/questions` | Authenticated | Quiz questions |
| POST | `/api/academy/quizzes/{id}/attempt` | Authenticated | Start attempt |
| PUT | `/api/academy/quizzes/{id}/attempt/{id}` | Authenticated | Submit attempt |
| GET | `/api/academy/quizzes/{id}/attempts` | Authenticated | Attempts |
| GET | `/api/academy/my-courses` | Authenticated | My courses |

### 3.10 Wallet, Packs, Subscriptions

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/wallet/balance` | Authenticated | Wallet balance |
| GET | `/api/wallet/history` | Authenticated | Transaction history |
| POST | `/api/wallet/purchase` | Authenticated | Purchase DT |
| GET | `/api/packs` | Authenticated | Pack list |
| GET | `/api/packs/{id}` | Authenticated | Pack detail |
| POST | `/api/packs/{id}/purchase` | Authenticated | Purchase pack |
| GET | `/api/subscriptions/plans` | Authenticated | Available plans |
| POST | `/api/subscriptions/checkout` | Authenticated | Create Stripe session |
| GET | `/api/subscriptions/current` | Authenticated | My subscription |
| POST | `/api/subscriptions/webhook` | public (Stripe) | Stripe webhook |

### 3.11 Administration

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/admin/dashboard` | admin | Dashboard stats |
| POST | `/api/admin/schools` | admin | Create school |
| GET | `/api/admin/schools` | admin | School list |
| PUT | `/api/admin/schools/{id}` | admin | Update school |
| DELETE | `/api/admin/schools/{id}` | admin | Delete school |
| POST | `/api/admin/schools/{id}/regenerate-invite-code` | admin | Regenerate invite code |
| GET | `/api/admin/users` | admin | User list |
| GET | `/api/admin/users/{id}` | admin | User detail |
| POST | `/api/admin/user-update` | admin | Update user |
| POST | `/api/admin/users/{id}/reset-password` | admin | Reset password |
| POST | `/api/admin/users` | admin | Create user |
| PUT | `/api/admin/users/{id}` | admin | Update user |
| DELETE | `/api/admin/users/{id}` | admin | Delete user |
| PUT | `/api/admin/users/{id}/balance` | admin | Update balance |
| PUT | `/api/admin/users/{id}/toggle-active` | admin | Activate/Deactivate |
| PUT | `/api/admin/users/{id}/change-role` | admin | Change role |
| PUT | `/api/admin/users/{id}/approve` | admin | Approve user |
| GET | `/api/admin/users-all` | admin | All users |
| GET | `/api/admin/classes` | admin | Class list |
| POST | `/api/admin/classes` | admin | Create class |
| POST | `/api/admin/enrollments` | admin | Enrollment |
| GET | `/api/admin/enrollments` | admin | Enrollment list |
| GET | `/api/admin/analytics/overview` | admin | Overview |
| GET | `/api/admin/analytics/users` | admin | User analytics |
| GET | `/api/admin/analytics/revenue` | admin | Revenue |
| GET | `/api/admin/analytics/enrollments` | admin | Enrollment analytics |
| GET | `/api/admin/analytics/api-costs` | admin | API costs |
| POST | `/api/admin/transactions` | admin | Create transaction |
| GET | `/api/admin/transactions` | admin | Transaction list |
| GET | `/api/admin/token-packages` | admin | Token packages |
| POST | `/api/admin/token-packages` | admin | Create package |
| PUT | `/api/admin/token-packages/{id}` | admin | Update package |
| GET | `/api/admin/messages` | admin | Messages |
| POST | `/api/admin/messages` | admin | Send message |
| DELETE | `/api/admin/messages/{id}` | admin | Delete message |
| POST | `/api/admin/broadcast` | admin | Broadcast |
| GET | `/api/admin/settings` | admin | Settings |
| PUT | `/api/admin/settings` | admin | Update setting |
| POST | `/api/admin/settings/apply` | admin | Apply settings |
| POST | `/api/admin/settings/test-provider` | admin | Test AI provider |
| PUT | `/api/admin/settings/token-limits` | admin | Token limits |
| GET | `/api/admin/settings/token-limits` | admin | View limits |
| POST | `/api/admin/settings/refresh-cache` | admin | Refresh cache |
| GET | `/api/admin/wallets` | admin | Wallets |
| POST | `/api/admin/wallets/{id}/add` | admin | Add balance |
| POST | `/api/admin/wallets/{id}/deduct` | admin | Deduct balance |
| POST | `/api/admin/wallet/allocate` | admin | Allocate balance |
| GET | `/api/admin/wallet/consumption-report` | admin | Consumption report |
| GET | `/api/admin/wallet/margin-report` | admin | Margin report |
| GET | `/api/admin/stats/global` | admin | Global stats |
| GET | `/api/admin/teacher-registrations` | admin | Teacher registrations |
| POST | `/api/admin/teacher-registrations/{id}/review` | admin | Review registration |
| POST | `/api/admin/teacher/duplicate-trial-content` | admin | Duplicate trial content |
| GET | `/api/admin/verifications/pending` | admin | Pending verifications |
| POST | `/api/admin/verifications/{id}/review` | admin | Review verification |
| GET | `/api/admin/courses/{id}/analytics` | admin | Course analytics |
| GET | `/api/admin/audit-logs` | admin | Audit log |
| GET | `/api/admin/subscriptions/expiring` | admin | Expiring subscriptions |
| POST | `/api/admin/subscriptions/check-expirations` | admin | Check expirations |
| POST | `/api/admin/users/{id}/extend-subscription` | admin | Extend subscription |
| POST | `/api/admin/school/packs/purchase` | admin | School pack purchase |
| GET | `/api/admin/school/packs/active` | admin | Active school packs |
| GET | `/api/admin/packs/revenue-report` | admin | Pack revenue report |
| POST | `/api/admin/import-students` | admin | Import students |
| POST | `/api/admin/import-students/upload` | admin | Upload import file |

### 3.12 Teacher

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/teacher/classes` | teacher | My classes |
| POST | `/api/teacher/classes` | teacher | Create class |
| GET | `/api/teacher/classes/{id}` | teacher | Class detail |
| PUT | `/api/teacher/classes/{id}` | teacher | Update class |
| DELETE | `/api/teacher/classes/{id}` | teacher | Delete class |
| POST | `/api/teacher/classes/{id}/enroll` | teacher | Enroll student |
| DELETE | `/api/teacher/classes/{id}/students/{id}` | teacher | Remove student |
| GET | `/api/teacher/classes/{id}/students` | teacher | Class students |
| GET | `/api/teacher/classes/{id}/available-students` | teacher | Available students |
| POST | `/api/teacher/classes/{id}/assignments` | teacher | Create assignment |

### 3.13 Adaptive Pathway

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/pathway/eleves/{id}/profil-assimilation` | Authenticated | Assimilation profile |
| POST | `/api/pathway/profils-assimilation` | Authenticated | Create profile |
| POST | `/api/pathway/profils-assimilation/{id}/validation` | Authenticated | Validate profile |
| GET | `/api/pathway/enseignants/{id}/notifications-reorientation` | Authenticated | Reorientation notifications |
| GET | `/api/pathway/notions/{id}/statut-publication` | Authenticated | Publication status |
| GET | `/api/pathway/eleves/{id}/acces-effectif` | Authenticated | Effective access |
| POST | `/api/pathway/scores` | Authenticated | Record score |
| POST | `/api/pathway/evaluer-reorientation` | Authenticated | Evaluate reorientation |
| GET | `/api/pathway/notions/{id}/contenu` | Authenticated | Notion content |
| GET | `/api/pathway/niveaux-etude` | Authenticated | Study levels |
| POST | `/api/pathway/niveaux-etude` | Authenticated | Create level |
| PUT | `/api/pathway/niveaux-etude/{id}` | Authenticated | Update level |
| DELETE | `/api/pathway/niveaux-etude/{id}` | Authenticated | Delete level |
| GET | `/api/pathway/matieres` | Authenticated | Subjects |
| POST | `/api/pathway/matieres` | Authenticated | Create subject |
| PUT | `/api/pathway/matieres/{id}` | Authenticated | Update subject |
| DELETE | `/api/pathway/matieres/{id}` | Authenticated | Delete subject |
| GET | `/api/pathway/chapter-pathways` | Authenticated | Chapter pathways |
| POST | `/api/pathway/chapter-pathways` | Authenticated | Create pathway |
| PUT | `/api/pathway/chapter-pathways/{id}` | Authenticated | Update pathway |
| DELETE | `/api/pathway/chapter-pathways/{id}` | Authenticated | Delete pathway |
| GET | `/api/pathway/notions-list` | Authenticated | Notions list |
| POST | `/api/pathway/notions-list` | Authenticated | Create notion |
| PUT | `/api/pathway/notions-list/{id}` | Authenticated | Update notion |
| DELETE | `/api/pathway/notions-list/{id}` | Authenticated | Delete notion |
| GET | `/api/pathway/contenus` | Authenticated | Contents |
| POST | `/api/pathway/contenus` | Authenticated | Create content |
| PUT | `/api/pathway/contenus/{id}` | Authenticated | Update content |
| DELETE | `/api/pathway/contenus/{id}` | Authenticated | Delete content |
| GET | `/api/pathway/catalog` | Authenticated | Pathway catalog |
| GET | `/api/pathway/mon-parcours` | Authenticated | My pathway |
| POST | `/api/pathway/auto-enroll-from-test` | Authenticated | Auto-enroll from test |
| POST | `/api/pathway/enroll-pathway` | Authenticated | Enroll in pathway |
| GET | `/api/pathway/specialites-pedagogiques` | Authenticated | Specialties |
| POST | `/api/pathway/specialites-pedagogiques` | Authenticated | Create specialty |
| POST | `/api/pathway/responsables-pedagogiques` | Authenticated | Create resp. pedagogique |
| GET | `/api/pathway/responsables-pedagogiques/{id}/contenus` | Authenticated | Resp. contents |
| POST | `/api/pathway/contenus-notion/{id}/valider` | Authenticated | Validate content |
| POST | `/api/pathway/contenus-notion/{id}/rejeter` | Authenticated | Reject content |

### 3.14 Gamification, Goals, Parent, Placement, LMS, Messaging, Media, Logs, Conversations, Payments

| Method | Path | Required Role | Description |
|--------|------|---------------|-------------|
| GET | `/api/gamification/badges` | Authenticated | Badges |
| POST | `/api/gamification/badges/check` | Authenticated | Check badges |
| GET | `/api/gamification/streak` | Authenticated | Daily streak |
| POST | `/api/gamification/streak/record` | Authenticated | Record day |
| GET | `/api/gamification/rankings` | Authenticated | Rankings |
| GET | `/api/learner/goals` | Authenticated | My goals |
| POST | `/api/learner/goals` | Authenticated | Create goal |
| GET | `/api/learner/goals/{id}` | Authenticated | Goal detail |
| PUT | `/api/learner/goals/{id}` | Authenticated | Update goal |
| POST | `/api/learner/goals/monthly` | Authenticated | Monthly goal |
| GET | `/api/pedagogical-lead/goals` | pedagogical_lead | School goals |
| GET | `/api/parents/me/enfants` | parent | My children |
| GET | `/api/parents/me/dashboard` | parent | Parent dashboard |
| GET | `/api/parents/me/enfants/{id}/suivi` | parent | Child tracking |
| GET | `/api/parents/me/enfants/{id}/progression` | parent | Child progress |
| POST | `/api/parents/me/enfants/lier` | parent | Link child |
| DELETE | `/api/parents/me/enfants/{id}/delier` | parent | Unlink child |
| GET | `/api/placement/tests` | Authenticated | Placement tests |
| GET | `/api/placement/tests/{id}` | Authenticated | Test detail |
| POST | `/api/placement/tests/{id}/submit` | Authenticated | Submit test |
| POST | `/api/lms/assignments` | teacher | Create assignment |
| GET | `/api/lms/assignments` | teacher | Assignment list |
| GET | `/api/lms/assignments/{id}` | teacher | Assignment detail |
| PUT | `/api/lms/assignments/{id}` | teacher | Update assignment |
| DELETE | `/api/lms/assignments/{id}` | teacher | Delete assignment |
| POST | `/api/lms/assignments/{id}/submit` | Authenticated | Submit assignment |
| GET | `/api/lms/submissions` | teacher | Submissions |
| GET | `/api/lms/submissions/{id}` | teacher | Submission detail |
| PUT | `/api/lms/submissions/{id}/grade` | teacher | Grade |
| GET | `/api/lms/classes` | Authenticated | Classes |
| POST | `/api/lms/enrollments` | teacher | Enrollment |
| GET | `/api/lms/enrollments` | teacher | Enrollment list |
| DELETE | `/api/lms/enrollments/{id}` | teacher | Delete enrollment |
| GET | `/api/lms/my-classes` | teacher | My classes |
| GET | `/api/lms/progress` | Authenticated | Progress |
| POST | `/api/lms/progress` | Authenticated | Record progress |
| GET | `/api/lms/classes/{id}/available-students` | teacher | Available students |
| GET | `/api/lms/classes/{id}/students` | teacher | Class students |
| POST | `/api/lms/classes/{id}/assignments` | teacher | Class assignments |
| GET | `/api/lms/classes/{id}/assignments` | teacher | Class assignments |
| POST | `/api/lms/classes` | teacher | Create class |
| DELETE | `/api/lms/classes/{id}` | teacher | Delete class |
| DELETE | `/api/lms/classes/{id}/students/{id}` | teacher | Remove student |
| GET | `/api/pedagogical/courses/pending` | pedagogical_admin | Courses to review |
| PUT | `/api/pedagogical/courses/{id}/review` | pedagogical_admin | Review course |
| GET | `/api/pedagogical/reports` | pedagogical_admin | Reports |
| POST | `/api/pedagogical/packs` | pedagogical_admin | Create pack |
| PUT | `/api/pedagogical/packs/{id}/publish` | pedagogical_admin | Publish pack |
| GET | `/api/pedagogical-lead/progress-report` | pedagogical_lead | Progress report |
| PUT | `/api/pedagogical-lead/courses/{id}/review-local` | pedagogical_lead | Local review |
| POST | `/api/pedagogical-lead/escalate/{id}` | pedagogical_lead | Escalate |
| GET | `/api/pedagogical-lead/performance` | pedagogical_lead | Performance |
| GET | `/api/inbox/messages` | Authenticated | Messages |
| PUT | `/api/inbox/messages/{id}/read` | Authenticated | Mark read |
| GET | `/api/inbox/unread-count` | Authenticated | Unread count |
| POST | `/api/admin/media/upload` | Authenticated | Upload file |
| GET | `/api/admin/media/files` | Authenticated | File list |
| GET | `/api/admin/logs/errors` | admin | Error log |
| GET | `/api/admin/logs/audit` | admin | Audit log |
| GET | `/api/conversations` | Authenticated | Conversations |
| GET | `/api/conversations/{id}` | Authenticated | Conversation detail |
| POST | `/api/conversations` | Authenticated | Create conversation |
| POST | `/api/conversations/{id}/messages` | Authenticated | Send message |
| DELETE | `/api/conversations/{id}` | Authenticated | Delete conversation |
| DELETE | `/api/conversations` | Authenticated | Delete all |
| GET | `/api/conversations/{id}/export/pdf` | Authenticated | Export PDF |
| GET | `/api/conversations/{id}/export/docx` | Authenticated | Export DOCX |
| POST | `/api/conversations/export/message/pdf` | Authenticated | Export message PDF |
| POST | `/api/conversations/export/message/docx` | Authenticated | Export message DOCX |
| POST | `/api/payments/stripe/checkout` | Authenticated | Create payment session |
| POST | `/api/payments/stripe/webhook` | public (Stripe) | Stripe webhook |

---

## 4. Architecture Decision Records (ADR)

### ADR-001: Multi-tenancy via school_id
- **Context**: Platform serves multiple schools in one database
- **Decision**: `school_id` column in every table + SQLAlchemy event listener for automatic filtering
- **Alternatives**: Separate schema per school (not adopted — high cost)
- **Trade-offs**: No row-level security at DB level

### ADR-002: Wallet Ledger Append-Only
- **Context**: Wallet needs complete transaction traceability
- **Decision**: `WalletTransaction` append-only with `Numeric(10,2)`. Balances always calculated from ledger
- **Alternatives**: `Wallet` table with mutable balance (deprecated `users.dt_balance` columns)
- **Trade-offs**: Lower performance for large volumes

### ADR-003: JWT without Refresh Token
- **Decision**: Single JWT with 24h validity. No refresh token
- **Alternatives**: Refresh token system (not implemented)
- **Trade-offs**: Users log in once every 24 hours

### ADR-004: RAG via TF-IDF
- **Decision**: TF-IDF (scikit-learn) without external service
- **Alternatives**: FAISS (not installed), embeddings API (OpenAI — quota exhausted)
- **Trade-offs**: No persistent index

### ADR-005: 8 AI Providers
- **Decision**: 8 providers supported with fallback
- **Alternatives**: Single provider
- **Trade-offs**: Maintenance complexity

### ADR-006: No Alembic
- **Decision**: Direct SQL in `backend/migrations/` + `Base.metadata.create_all()`
- **Alternatives**: Alembic (present in Dockerfile but unused)
- **Trade-offs**: No schema versioning

### ADR-007: Atomic Commit for Purchases
- **Decision**: `debit_dt(commit=False)` + single `db.commit()` from Caller
- **Alternatives**: Separate commit per operation
- **Trade-offs**: No distributed transaction

### ADR-008: Pedagogical Status = Always Recalculated
- **Decision**: `LearningGoal.statut` never stored — always computed from current values
- **Alternatives**: State storage with periodic update

### ADR-009: Pack Découverte = No Auto-Generated Goals
- **Decision**: No auto-generated goals for Découverte pack users

### ADR-010: Tenant Filter Suppression for Individual Packs
- **Decision**: `has_course_access()` suppresses Tenant filter for PackPurchase with `school_id=None`

### ADR-011: 5-Section Student Navigation
- **Decision**: Sidebar split into 5 collapsible sections (Accueil/Parcours/IA/Objectifs/Profil)

### ADR-012: Commission Rate = Decimal
- **Decision**: `commission_rate` divided by `Decimal("100")` not `100` (float)

### ADR-013: pg8000 Enum = UPPERCASE
- **Decision**: DB enums use UPPERCASE values

### ADR-014: No Level-Up Check in Course Purchase
- **Decision**: No level_up verification in purchase flow

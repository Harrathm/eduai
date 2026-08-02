# EDUAI Learning

---

## العربية — نظرة عامة على المشروع

### تعريف المشروع

**EDUAI Learning** هو منصة تعليمية إلكترونية SaaS متعددة المستأجرين (multi-tenant) مصممة للسوق التونسي. المنصة توفر:

- **نظام صلاحيات (RBAC) بـ 7 أدوار**: `student` (طالب)، `teacher` (أستاذ)، `admin_school` (مدير مدرسة)، `super_admin` (مدير عام)، `pedagogical_admin` (مدير بيداغوجي عام على مستوى المنصة)، `pedagogical_lead` (مدير بيداغوجي على مستوى المدرسة)، `parent` (ولي أمر الطالب — وصول للقراءة فقط لতাتبوع التقدم)
- **محفظة مالية موحدة (Wallet)**: نظام ائتمانات بـ 5 مجمعات (`trial`، `school_allocated`، `purchased`، `subscription`، `dt_purchased`) مع دفتر漪iskAppend-Only عبر `WalletTransaction`
- **نظام الاشتراكات والباقات**: باقات مدرسية (`StudyPack`) وعمليات شراء الباقة (`PackPurchase`) مع صلاحية محددة
- **سوق الدورات**: دورات خاصة بالمدرسة، دورات أساتذة مستقلين، وكتالوج EDUAI الرسمي مع نظام عمولات
- **مسار تعليمي تكيفي (Adaptive Pathway)**: 5 طبقات (اكتشاف، تأسيس، تطوير، تخصص، إتقان) مع تتبع الأهداف اليومية والأسبوعية والشهرية
- **نظام الذكاء الاصطناعي**: مدرس AI، توليد اختبارات، شرح المفاهيم، استيراد ملفات PDF إلى RAG
- **الاختبار التوضيحي (Placement Test)**: تحديد مستوى الطالب تسجيله تلقائياً في المسار المناسب
- **النظام التحفيزي (Gamification)**: شارات وإنجازات بناءً على معايير كمية
- **إدارة الفصول الدراسية**: أساتذة، صفوف، تسجيلات طلاب
- **نظام الوالدين**: وصول لمتابعة تقدم الأبناء (قراءة فقط)
- **البريد الداخلي**: رسائل مباشرة وعمومية
- **سجل التدقيق (Audit Log)**: تتبع جميع الإجراءات المالية والإدارية
- **دعم ثلاث لغات**: فرنسية، إنجليزية، عربية (عبر i18next)

**لمن**: منصات تعليمية برمجية (B2B) — مدارس ومجموعات تعليمية في تونس. الأساتذة المستقلون يمكنهم亦ت also بيع دوراتهم عبر المنصة.

**البنية التقنية**:

| المكون | التقنية | الإصدار |
|--------|---------|---------|
| الخادم (Backend) | Python | 3.11 |
| إطار العمل | FastAPI | ≥0.95.0 |
| ORM | SQLAlchemy | ≥2.0 |
| قاعدة البيانات | PostgreSQL | 15 |
| مترجم SQL | pg8000 | ≥1.0.0 |
| الواجهة الأمامية | React | 18.2.0 |
| بناء الواجهة | Vite | 5.1.0 |
| لغة الواجهة | TypeScript | 6.0.3 |
| التنسيق | TailwindCSS | 3.4.1 |
| التطبيق المحمول | Flutter (Dart) | SDK ≥3.0.0 <4.0.0 |
| حاوية | Docker | — |
| نظام التشغيل | Windows / Linux | — |

### المتطلبات المسبقة

| الأداة | الإصدار المطلوب | ملاحظة |
|--------|----------------|--------|
| Python | 3.11 | محدد في `backend/Dockerfile` |
| Node.js | 20 | محدد في `frontend/Dockerfile` |
| Flutter SDK | ≥3.0.0 | محدد في `mobile/pubspec.yaml` |
| PostgreSQL | 15 | محدد في `docker-compose.yml` |
| Docker | غير محدد في المستودع | اختياري — للتشغيل عبر Docker Compose |

### التثبيت

#### الخادم (Backend)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt
```

#### الواجهة الأمامية (Frontend)

```bash
cd frontend
npm install
```

#### التطبيق المحمول (Mobile)

```bash
cd mobile
flutter pub get
```

### متغيرات البيئة

#### Backend (`backend/.env.example`)

| المتغير | مطلوب | الوصف | القيمة الافتراضية |
|---------|-------|-------|-------------------|
| `DATABASE_URL` | نعم | ربط PostgreSQL | — |
| `JWT_SECRET` | نعم (إنتاج ≥32 حرف) | مفتاح توقيع JWT | — |
| `JWT_ALGORITHM` | لا | خوارزمية JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | لا | صلاحية التوكن (دقائق) | `1440` |
| `OPENAI_API_KEY` | لا | مفتاح OpenAI | — |
| `OPENAI_ORG_ID` | لا | معرف مؤسسة OpenAI | — |
| `GROQ_API_KEY` | لا | مفتاح Groq | — |
| `OPENROUTER_API_KEY` | لا | مفتاح OpenRouter | — |
| `MINIMAX_API_KEY` | لا | مفتاح MiniMax | — |
| `MINIMAX_BASE_URL` | لا | عنوان MiniMax | `https://inference.dahl.global/v1` |
| `STRIPE_SECRET_KEY` | لا | مفتاح Stripe السري | — |
| `STRIPE_WEBHOOK_SECRET` | لا | سر Webhook Stripe | — |
| `STRIPE_PRICE_PRO` | لا | معرّف سعر الخطة Pro | `price_teacher_pro` |
| `STRIPE_PRICE_SCHOOL` | لا | معرّف سعر خطة المدرسة | `price_school` |
| `STRIPE_PRICE_INSTITUTION` | لا | معرّف سعر خطة المؤسسة | `price_institution` |
| `ALLOWED_ORIGINS` | لا | أصول CORS (مفصولة بفاصلة) | `http://localhost:5173` |
| `ENVIRONMENT` | لا | بيئة التشغيل | `development` |
| `REDIS_URL` | لا | ربط Redis (معدل الطلبات) | — |
| `DB_POOL_SIZE` | لا | حجم مجمع الاتصالات | `5` |
| `DB_MAX_OVERFLOW` | لا | الحد الأقصى للمجمع | `10` |
| `DB_POOL_TIMEOUT` | لا | مهلة المجمع (ثواني) | `30` |
| `DB_POOL_RECYCLE` | لا | دورة المجمع (ثواني) | `3600` |
| `S3_BUCKET` | لا | دلو S3 للوسائط | `eduai-media` |
| `S3_ENDPOINT` | لا | نقطة نهاية S3 | `http://localhost:9000` |
| `S3_ACCESS_KEY` | لا | مفتاح الوصول S3 | `minioadmin` |
| `S3_SECRET_KEY` | لا | السر S3 | `minioadmin` |
| `FRONTEND_URL` | لا | رابط الواجهة الأمامية | `http://localhost:5173` |

#### Frontend (`frontend/.env.example`)

| المتغير | مطلوب | الوصف | القيمة الافتراضية |
|---------|-------|-------|-------------------|
| `VITE_API_BASE_URL` | لا | رابط API الخادم | `http://localhost:8000` |
| `VITE_STRIPE_PUBLISHABLE_KEY` | لا | المفتاح العام لـ Stripe | — |
| `VITE_APP_NAME` | لا | اسم التطبيق | `EDUAI Learning` |

### أوامر التشغيل

#### تشغيل محلي (بدون Docker)

```bash
# الخادم
cd backend
python -m uvicorn app.main:app --port 8000 --reload

# الواجهة الأمامية
cd frontend
npm run dev
```

#### تشغيل عبر Docker

```bash
docker-compose up --build
```

هذا يشغّل:
- PostgreSQL على المنفذ `5432`
- الخادم على المنفذ `8000`
- الواجهة الأمامية على المنفذ `80`

### الاختبارات

```bash
# اختبارات الخادم (pytest — 180 اختبار)
cd backend
pytest

# اختبارات الواجهة الأمامية (vitest)
cd frontend
npm run test:run
```

### هيكل المجلدات

```
RAG_APP_new/
├── backend/                    # تطبيق Python/FastAPI
│   ├── app/
│   │   ├── ai/                 # خدمات الذكاء الاصطناعي (RAG, embeddings, PDF)
│   │   ├── core/               # الإعدادات والأمان
│   │   ├── db/                 # جلسة قاعدة البيانات + تصفية المستأجرين
│   │   ├── payment/            # خدمات الدفع (Stripe)
│   │   ├── routers/            # نقاط نهاية API (30+ موزّع)
│   │   ├── services/           # منطق الأعمال
│   │   ├── tasks/              # المهام الخلفية
│   │   ├── main.py             # نقطة الدخول
│   │   ├── models.py           # نماذج SQLAlchemy (2000+ سطر)
│   │   └── schemas.py          # مخططات Pydantic
│   ├── tests/                  # اختبارات pytest (180 اختبار)
│   ├── migrations/             # هجرة SQL
│   ├── Dockerfile              # بناء Docker
│   ├── requirements.txt        # التبعيات
│   └── .env.example            # نموذج متغيرات البيئة
├── frontend/                   # تطبيق React/Vite
│   ├── src/
│   │   ├── api/                # طبقة API
│   │   ├── components/         # مكونات مشتركة
│   │   ├── features/           # وحدات وظيفية (admin, teacher, student, parent)
│   │   ├── i18n/               # التدويل (fr, en, ar)
│   │   └── App.tsx             # التطبيق الرئيسي
│   ├── Dockerfile              # بناء Docker (Node 20 + Nginx)
│   ├── package.json            # التبعيات
│   └── vercel.json             # إعداد Vercel
├── mobile/                     # تطبيق Flutter
│   ├── lib/
│   │   ├── core/               # التخزين الآمن، الاتصال بالـ API، المُوجّه
│   │   ├── features/           # الشاشات (auth, home, courses, ai_tutor, assignments)
│   │   └── main.dart           # نقطة الدخول
│   └── pubspec.yaml            # التبعيات
├── Docs/                       # التوثيق والتقارير
├── docker-compose.yml          # تجميع Docker
└── start_server.bat            # سكريبت بدء التشغيل (Windows)
```

### معلومات غير موجودة في المستودع

التالي مذكور في `.env.example` لكن لا يوجد نموذج محدد في المستودع:
- **الرخصة (LICENSE)**: غير موجودة
- **إصدار Python محدد**: غير محدد في ملف `.python-version` (الإصدار 3.11 محدد فقط في `Dockerfile`)
- **alembic.ini**: غير موجود (يُستخدم `alembic upgrade head` في `docker-compose.yml` بدون ملف تكوين)
- **pytest.ini**: غير موجود (يُستخدم `conftest.py` في `backend/tests/`)
- **اسم مستودع Git / رابط GitHub**: غير محدد
- **معلومات الاتصال / البريد الإلكتروني**: غير محددة

---

## Français — Aperçu du projet

### Définition du projet

**EDUAI Learning** est une plateforme éducative SaaS multi-tenants conçue pour le marché tunisien. La plateforme offre :

- **Système RBAC à 7 rôles** : `student` (élève), `teacher` (enseignant), `admin_school` (administrateur d'école), `super_admin` (administrateur général), `pedagogical_admin` (administrateur pédagogique — portée plateforme), `pedagogical_lead` (responsable pédagogique — portée école), `parent` (parent d'élève — accès lecture seule progression)
- **Wallet unifié** : système de crédits avec 5 pools (`trial`, `school_allocated`, `purchased`, `subscription`, `dt_purchased`) et un ledger append-only via `WalletTransaction`
- **Système d'abonnements et packs** : packs scolaires (`StudyPack`) et achats de packs (`PackPurchase`) avec durée de validité
- **Marketplace de cours** : cours d'école, cours d'enseignants indépendants, catalogue officiel EDUAI avec système de commissions
- **Parcours pédagogique adaptatif** : 5 couches (Découverte, Fondamentaux, Développement, Spécialisation, Maîtrise) avec suivi d'objectifs quotidien/hebdomadaire/mensuel
- **Système d'IA** : tuteur IA, génération de quiz, explication de concepts, ingestion de PDF vers RAG
- **Test de positionnement** : détermination du niveau de l'élève et inscription automatique dans le parcours approprié
- **Gamification** : badges et achievements basés sur des critères quantitatifs
- **Gestion des classes** : enseignants, salles, inscriptions d'élèves
- **Rôle parent** : accès en lecture seule à la progression des enfants
- **Messagerie interne** : messages directs et broadcast
- **Journal d'audit** : suivi de toutes les actions financières et administratives
- **Support trilingue** : français, anglais, arabe (via i18next)

**Pour qui** : plateformes éducatives B2B — écoles et groupes éducatifs en Tunisie. Les enseignants indépendants peuvent亦t vendre leurs cours via la plateforme.

**Stack technique** :

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend | Python | 3.11 |
| Framework | FastAPI | ≥0.95.0 |
| ORM | SQLAlchemy | ≥2.0 |
| Base de données | PostgreSQL | 15 |
| Driver SQL | pg8000 | ≥1.0.0 |
| Frontend | React | 18.2.0 |
| Build | Vite | 5.1.0 |
| Langage frontend | TypeScript | 6.0.3 |
| CSS | TailwindCSS | 3.4.1 |
| App mobile | Flutter (Dart) | SDK ≥3.0.0 <4.0.0 |
| Conteneurisation | Docker | — |
| Système d'exploitation | Windows / Linux | — |

### Prérequis

| Outil | Version requise | Notes |
|-------|-----------------|-------|
| Python | 3.11 | Spécifié dans `backend/Dockerfile` |
| Node.js | 20 | Spécifié dans `frontend/Dockerfile` |
| Flutter SDK | ≥3.0.0 | Spécifié dans `mobile/pubspec.yaml` |
| PostgreSQL | 15 | Spécifié dans `docker-compose.yml` |
| Docker | Non spécifié dans le repo | Optionnel — pour Docker Compose |

### Installation

#### Backend

```bash
cd backend
python -m venv .venv
# Windows :
.venv\Scripts\activate
# Linux/Mac :
source .venv/bin/activate
pip install -r requirements.txt
```

#### Frontend

```bash
cd frontend
npm install
```

#### Mobile

```bash
cd mobile
flutter pub get
```

### Variables d'environnement

#### Backend (`backend/.env.example`)

| Variable | Obligatoire | Description | Défaut |
|----------|-------------|-------------|--------|
| `DATABASE_URL` | Oui | Chaîne de connexion PostgreSQL | — |
| `JWT_SECRET` | Oui (prod ≥32 car.) | Clé de signature JWT | — |
| `JWT_ALGORITHM` | Non | Algorithme JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | Non | Durée de validité du token (min) | `1440` |
| `OPENAI_API_KEY` | Non | Clé API OpenAI | — |
| `OPENAI_ORG_ID` | Non | ID organisation OpenAI | — |
| `GROQ_API_KEY` | Non | Clé API Groq | — |
| `OPENROUTER_API_KEY` | Non | Clé API OpenRouter | — |
| `MINIMAX_API_KEY` | Non | Clé API MiniMax | — |
| `MINIMAX_BASE_URL` | Non | URL de base MiniMax | `https://inference.dahl.global/v1` |
| `STRIPE_SECRET_KEY` | Non | Clé secrète Stripe | — |
| `STRIPE_WEBHOOK_SECRET` | Non | Secret webhook Stripe | — |
| `STRIPE_PRICE_PRO` | Non | ID prix plan Pro | `price_teacher_pro` |
| `STRIPE_PRICE_SCHOOL` | Non | ID prix plan École | `price_school` |
| `STRIPE_PRICE_INSTITUTION` | Non | ID prix plan Institution | `price_institution` |
| `ALLOWED_ORIGINS` | Non | Origines CORS (séparées par virgule) | `http://localhost:5173` |
| `ENVIRONMENT` | Non | Environnement d'exécution | `development` |
| `REDIS_URL` | Non | Connexion Redis (rate limiting) | — |
| `DB_POOL_SIZE` | Non | Taille du pool de connexions | `5` |
| `DB_MAX_OVERFLOW` | Non | Débordement max du pool | `10` |
| `DB_POOL_TIMEOUT` | Non | Timeout du pool (sec) | `30` |
| `DB_POOL_RECYCLE` | Non | Recyclage du pool (sec) | `3600` |
| `S3_BUCKET` | Non | Bucket S3 pour médias | `eduai-media` |
| `S3_ENDPOINT` | Non | Point de terminaison S3 | `http://localhost:9000` |
| `S3_ACCESS_KEY` | Non | Clé d'accès S3 | `minioadmin` |
| `S3_SECRET_KEY` | Non | Secret S3 | `minioadmin` |
| `FRONTEND_URL` | Non | URL du frontend | `http://localhost:5173` |

#### Frontend (`frontend/.env.example`)

| Variable | Obligatoire | Description | Défaut |
|----------|-------------|-------------|--------|
| `VITE_API_BASE_URL` | Non | URL de base de l'API backend | `http://localhost:8000` |
| `VITE_STRIPE_PUBLISHABLE_KEY` | Non | Clé publique Stripe | — |
| `VITE_APP_NAME` | Non | Nom de l'application | `EDUAI Learning` |

### Commandes de lancement

#### Exécution locale (sans Docker)

```bash
# Backend
cd backend
python -m uvicorn app.main:app --port 8000 --reload

# Frontend
cd frontend
npm run dev
```

#### Exécution via Docker

```bash
docker-compose up --build
```

Ceci lance :
- PostgreSQL sur le port `5432`
- Backend sur le port `8000`
- Frontend sur le port `80`

### Tests

```bash
# Tests backend (pytest — 180 tests)
cd backend
pytest

# Tests frontend (vitest)
cd frontend
npm run test:run
```

### Structure des dossiers

```
RAG_APP_new/
├── backend/                    # Application Python/FastAPI
│   ├── app/
│   │   ├── ai/                 # Services IA (RAG, embeddings, PDF)
│   │   ├── core/               # Configuration et sécurité
│   │   ├── db/                 # Session DB + filtrage multi-tenant
│   │   ├── payment/            # Services de paiement (Stripe)
│   │   ├── routers/            # Points d'entrée API (30+ répartis)
│   │   ├── services/           # Logique métier
│   │   ├── tasks/              # Tâches en arrière-plan
│   │   ├── main.py             # Point d'entrée
│   │   ├── models.py           # Modèles SQLAlchemy (2000+ lignes)
│   │   └── schemas.py          # Schémas Pydantic
│   ├── tests/                  # Tests pytest (180 tests)
│   ├── migrations/             # Migrations SQL
│   ├── Dockerfile              # Build Docker
│   ├── requirements.txt        # Dépendances
│   └── .env.example            # Modèle de variables d'environnement
├── frontend/                   # Application React/Vite
│   ├── src/
│   │   ├── api/                # Couche API
│   │   ├── components/         # Composants réutilisables
│   │   ├── features/           # Modules fonctionnels (admin, teacher, student, parent)
│   │   ├── i18n/               # Internationalisation (fr, en, ar)
│   │   └── App.tsx             # Application principale
│   ├── Dockerfile              # Build Docker (Node 20 + Nginx)
│   ├── package.json            # Dépendances
│   └── vercel.json             # Configuration Vercel
├── mobile/                     # Application Flutter
│   ├── lib/
│   │   ├── core/               # Stockage sécurisé, API client, routeur
│   │   ├── features/           # Écrans (auth, home, courses, ai_tutor, assignments)
│   │   └── main.dart           # Point d'entrée
│   └── pubspec.yaml            # Dépendances
├── Docs/                       # Documentation et rapports
├── docker-compose.yml          # Orchestration Docker
└── start_server.bat            # Script de démarrage (Windows)
```

### Informations non trouvées dans le repo

Les éléments suivants sont absents ou non spécifiés dans le dépôt :
- **Licence (LICENSE)** : non trouvée
- **Version Python précise** : non spécifiée dans un fichier `.python-version` (la version 3.11 est uniquement définie dans le `Dockerfile`)
- **alembic.ini** : absent (bien que `alembic upgrade head` soit utilisé dans `docker-compose.yml`)
- **pytest.ini** : absent (utilisation de `conftest.py` dans `backend/tests/`)
- **Nom du dépôt Git / lien GitHub** : non spécifié
- **Coordonnées de contact** : non spécifiées

---

## English — Project Overview

### Project Definition

**EDUAI Learning** is a multi-tenant SaaS educational platform designed for the Tunisian market. The platform provides:

- **RBAC system with 7 roles**: `student`, `teacher`, `admin_school`, `super_admin`, `pedagogical_admin` (platform-wide), `pedagogical_lead` (school-scoped), `parent` (read-only access to student progress)
- **Unified Wallet**: credit system with 5 pools (`trial`, `school_allocated`, `purchased`, `subscription`, `dt_purchased`) and an append-only ledger via `WalletTransaction`
- **Subscription and pack system**: school packs (`StudyPack`) and pack purchases (`PackPurchase`) with validity duration
- **Course marketplace**: school courses, independent teacher courses, official EDUAI catalog with commission system
- **Adaptive learning pathway**: 5 tiers (Discovery, Fundamentals, Development, Specialization, Mastery) with daily/weekly/monthly goal tracking
- **AI system**: AI tutor, quiz generation, concept explanation, PDF ingestion to RAG
- **Placement test**: student level determination with automatic enrollment in the appropriate pathway
- **Gamification**: badges and achievements based on quantitative criteria
- **Classroom management**: teachers, classes, student enrollments
- **Parent role**: read-only access to children's progress
- **Internal messaging**: direct and broadcast messages
- **Audit log**: tracking of all financial and administrative actions
- **Trilingual support**: French, English, Arabic (via i18next)

**Target audience**: B2B educational platforms — schools and educational groups in Tunisia. Independent teachers can亦t sell their courses via the platform.

**Tech stack**:

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Python | 3.11 |
| Framework | FastAPI | ≥0.95.0 |
| ORM | SQLAlchemy | ≥2.0 |
| Database | PostgreSQL | 15 |
| SQL driver | pg8000 | ≥1.0.0 |
| Frontend | React | 18.2.0 |
| Build | Vite | 5.1.0 |
| Frontend language | TypeScript | 6.0.3 |
| CSS | TailwindCSS | 3.4.1 |
| Mobile app | Flutter (Dart) | SDK ≥3.0.0 <4.0.0 |
| Containerization | Docker | — |
| Operating system | Windows / Linux | — |

### Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.11 | Specified in `backend/Dockerfile` |
| Node.js | 20 | Specified in `frontend/Dockerfile` |
| Flutter SDK | ≥3.0.0 | Specified in `mobile/pubspec.yaml` |
| PostgreSQL | 15 | Specified in `docker-compose.yml` |
| Docker | Not specified in repo | Optional — for Docker Compose |

### Installation

#### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt
```

#### Frontend

```bash
cd frontend
npm install
```

#### Mobile

```bash
cd mobile
flutter pub get
```

### Environment Variables

#### Backend (`backend/.env.example`)

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | — |
| `JWT_SECRET` | Yes (prod ≥32 chars) | JWT signing key | — |
| `JWT_ALGORITHM` | No | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | No | Token validity (minutes) | `1440` |
| `OPENAI_API_KEY` | No | OpenAI API key | — |
| `OPENAI_ORG_ID` | No | OpenAI organization ID | — |
| `GROQ_API_KEY` | No | Groq API key | — |
| `OPENROUTER_API_KEY` | No | OpenRouter API key | — |
| `MINIMAX_API_KEY` | No | MiniMax API key | — |
| `MINIMAX_BASE_URL` | No | MiniMax base URL | `https://inference.dahl.global/v1` |
| `STRIPE_SECRET_KEY` | No | Stripe secret key | — |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook secret | — |
| `STRIPE_PRICE_PRO` | No | Stripe Pro plan price ID | `price_teacher_pro` |
| `STRIPE_PRICE_SCHOOL` | No | Stripe School plan price ID | `price_school` |
| `STRIPE_PRICE_INSTITUTION` | No | Stripe Institution plan price ID | `price_institution` |
| `ALLOWED_ORIGINS` | No | CORS origins (comma-separated) | `http://localhost:5173` |
| `ENVIRONMENT` | No | Runtime environment | `development` |
| `REDIS_URL` | No | Redis connection (rate limiting) | — |
| `DB_POOL_SIZE` | No | Connection pool size | `5` |
| `DB_MAX_OVERFLOW` | No | Max pool overflow | `10` |
| `DB_POOL_TIMEOUT` | No | Pool timeout (seconds) | `30` |
| `DB_POOL_RECYCLE` | No | Pool recycle (seconds) | `3600` |
| `S3_BUCKET` | No | S3 bucket for media | `eduai-media` |
| `S3_ENDPOINT` | No | S3 endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY` | No | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | No | S3 secret key | `minioadmin` |
| `FRONTEND_URL` | No | Frontend URL | `http://localhost:5173` |

#### Frontend (`frontend/.env.example`)

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `VITE_API_BASE_URL` | No | Backend API base URL | `http://localhost:8000` |
| `VITE_STRIPE_PUBLISHABLE_KEY` | No | Stripe publishable key | — |
| `VITE_APP_NAME` | No | Application name | `EDUAI Learning` |

### Launch Commands

#### Local execution (without Docker)

```bash
# Backend
cd backend
python -m uvicorn app.main:app --port 8000 --reload

# Frontend
cd frontend
npm run dev
```

#### Docker execution

```bash
docker-compose up --build
```

This launches:
- PostgreSQL on port `5432`
- Backend on port `8000`
- Frontend on port `80`

### Tests

```bash
# Backend tests (pytest — 180 tests)
cd backend
pytest

# Frontend tests (vitest)
cd frontend
npm run test:run
```

### Folder Structure

```
RAG_APP_new/
├── backend/                    # Python/FastAPI application
│   ├── app/
│   │   ├── ai/                 # AI services (RAG, embeddings, PDF)
│   │   ├── core/               # Configuration and security
│   │   ├── db/                 # DB session + tenant filtering
│   │   ├── payment/            # Payment services (Stripe)
│   │   ├── routers/            # API endpoints (30+ distributed)
│   │   ├── services/           # Business logic
│   │   ├── tasks/              # Background tasks
│   │   ├── main.py             # Entry point
│   │   ├── models.py           # SQLAlchemy models (2000+ lines)
│   │   └── schemas.py          # Pydantic schemas
│   ├── tests/                  # pytest tests (180 tests)
│   ├── migrations/             # SQL migrations
│   ├── Dockerfile              # Docker build
│   ├── requirements.txt        # Dependencies
│   └── .env.example            # Environment variable template
├── frontend/                   # React/Vite application
│   ├── src/
│   │   ├── api/                # API layer
│   │   ├── components/         # Reusable components
│   │   ├── features/           # Feature modules (admin, teacher, student, parent)
│   │   ├── i18n/               # Internationalization (fr, en, ar)
│   │   └── App.tsx             # Main application
│   ├── Dockerfile              # Docker build (Node 20 + Nginx)
│   ├── package.json            # Dependencies
│   └── vercel.json             # Vercel configuration
├── mobile/                     # Flutter application
│   ├── lib/
│   │   ├── core/               # Secure storage, API client, router
│   │   ├── features/           # Screens (auth, home, courses, ai_tutor, assignments)
│   │   └── main.dart           # Entry point
│   └── pubspec.yaml            # Dependencies
├── Docs/                       # Documentation and reports
├── docker-compose.yml          # Docker orchestration
└── start_server.bat            # Startup script (Windows)
```

### Information Not Found in the Repository

The following items are missing or unspecified in the repo:
- **License (LICENSE)**: not found
- **Exact Python version**: not specified in a `.python-version` file (version 3.11 is only defined in the `Dockerfile`)
- **alembic.ini**: absent (although `alembic upgrade head` is used in `docker-compose.yml`)
- **pytest.ini**: absent (uses `conftest.py` in `backend/tests/`)
- **Git repository name / GitHub link**: not specified
- **Contact information**: not specified

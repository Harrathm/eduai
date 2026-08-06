# خطة التنفيذ — EDUAI Learning

# IMPLEMENTATION PLAN — EDUAI Learning

---

## أولاً: تقييم الوضع الحالي

### RBAC والتوثيق
| المكون | الحالة |
|--------|--------|
| 7 أدوار (super_admin, admin_school, pedagogical_admin, pedagogical_lead, teacher, student, parent) | ✅ مُنفّذ ومُختبَر |
| نظام multi-tenancy مع `set_tenant_context` | ⚠️ مُنفّذ لكن **غير مفعّل** في courses.py و lms.py و academy.py — كلها تستخدم `get_current_user` مباشرة بدون تنشيط فلتر الإيجار |
| حماية تسجيل الدخول + قفل الحساب (5 محاولات) | ✅ مُنفّذ ومُختبَر |
| أكواد دعوة المدارس | ✅ مُنفّذ |
| فحص `check_school_access()` | ✅ مُنفّذ لكن **غير مستخدم** في courses.py و academy.py |
| فحص `has_course_access()` | ✅ مُنفّذ ومُختبَر (23 اختبار + 13 اختبار 403) |

### المحافظة المالية
| المكون | الحالة |
|--------|--------|
| `debit_dt()` / `credit_dt()` — Numeric(10,2) | ✅ مُنفّذ ومُختبَر (6 اختبارات) |
| `consume_credits()` — استهلاك الأولوية | ⚠️ مُنفّذ لكن **لم يُختبَر** + فرصة سباق (race condition) |
| `purchase_course()` — خصم ذري + تسجيل | ✅ مُنفّذ ومُختبَر |
| Stripe subscriptions | ⚠️ مُنفّذ لكن **لم يُختبَر** |
| خصم الدورات المدفوعة | ✅ مُنفّذ ومُختبَر |

### الدورات والمحتوى
| المكون | الحالة |
|--------|--------|
| CRUD الدورات (admin/academy) | ✅ مُنفّذ ومُختبَر |
| `course_lifecycle.py` — انتقالات الحالة | ⚠️ مُنفّذ لكن **صفر اختبارات** |
| التحقق المزدوج للمحتوى | ✅ مُنفّذ |
| `has_course_access()` 7 خطوات | ✅ مُنفّذ ومُختبَر |

### المسار التكيّفي
| المكون | الحالة |
|--------|--------|
| 5 طبقات (Découverte → Maîtrise) | ✅ مُنفّذ ومُختبَر (10 اختبارات) |
| التوجيه التلقائي | ✅ مُنفّذ ومُختبَر |
| التحقق من النشر | ✅ مُنفّذ ومُختبَر |
| ملف التعريف التكيّفي | ✅ مُنفّذ ومُختبَر |
| الأقسام والمفاهيم | ✅ مُنفّذ |

### الذكاء الاصطناعي
| المكون | الحالة |
|--------|--------|
| AI Tutor (ask/explain/correct) | ✅ مُنفّذ لكن **لم يُختبَر** |
| RAG (TF-IDF) | ⚠️ مُنفّذ لكن **لم يُختبَر** + يعيد بناء المتجه في كل استعلام |
| AI Factory | ✅ مُنفّذ لكن **لم يُختبَر** |
| 9 مزوّدين | ✅ مُنفّذ |

### الأهداف التعليمية
| المكون | الحالة |
|--------|--------|
| أهداف يومية/أسبوعية (auto) | ✅ مُنفّذ ومُختبَر |
| أهداف شهرية (auto) | ⚠️ مُنفّذ لكن **لم يُختبَر** + تسرّب ذاكرة في `_status_cache` |
| جدولة الأهداف (APScheduler) | ⚠️ مُنفّذ لكن **لم يُختبَر** |

### التلعيم
| المكون | الحالة |
|--------|--------|
| شارات + سلاسل + تصنيفات | ⚠️ مُنفّذ لكن **لم يُختبَر** + `compute_rankings()` يستعلم كل الطلاب في بايثون |
| إشعارات | ⚠️ مُنفّذ لكن **لم يُختبَر** + `sender_id=1` ثابت |

### الواجهة الأمامية
| المكون | الحالة |
|--------|--------|
| صفحات المشرف (41 صفحة) | ✅ مُنفّذ |
| صفحات المعلم (8 صفحات) | ✅ مُنفّذ (7/8 — إضافة طلاب مُعلّقة) |
| صفحات الطالب (13 صفحة) | ✅ مُنفّذ |
| صفحات ولي الأمر (2 صفحة) | ✅ مُنفّذ |
| صفحة إنشاء الدورات للمعلم | ❌ غير مُنفّذ |
| إعادة تعيين كلمة المرور | ❌ غير مُنفّذ |

### البنية التحتية
| المكون | الحالة |
|--------|--------|
| Alembic (هجرة قاعدة البيانات) | ❌ **غير موجود** — Docker يشير إليه لكن لا يوجد |
| pyproject.toml vs requirements.txt | ⚠️ غير متطابق (SQLAlchemy 1.4 vs 2.0) |
| SQLite اختبارات | ✅ مُنفّذ لكن تكرار كبير في تكوين الاختبارات |

---

## ثانياً: الخطة المرحلية

### المرحلة 0: إصلاح البنية التحتية
**الهدف:** تأسيس بيئات التطوير والاختبار والنشر بشكل صحيح

1. إنشاء `alembic.ini` + `alembic/` + `env.py` مع إعدادات PostgreSQL
2. تحويل المكتبات SQL الخامة إلى إصدارات Alembic (هجرة `numeric_monetary.sql` و `wallet_amount_float.sql`)
3. مزامنة `pyproject.toml` مع `requirements.txt` (SQLAlchemy 2.0 + pg8000)
4. إصلاح `backend/docker-compose.yml` — إزالة بيانات اعتماد قاعدة البيانات المضمنة
5. توحيد `conftest.py` — نقل جميع ملفات الاختبار إلى نظام fixtures موحد

### المرحلة 1: إصلاح عزل الإيجار (Tenant Isolation)
**الهدف:** ضمان أن جميع نقاط النهاية تحترم عزل المدارس

1. **courses.py**: استبدال `require_teacher` المحلي بـ `require_teacher_or_admin` من `deps.py`
2. **courses.py**: إضافة `set_tenant_context` في جميع نقاط النهاية
3. **courses.py**: إضافة `check_school_access()` في `update_course`
4. **lms.py**: إضافة `set_tenant_context` في جميع نقاط النهاية
5. **lms.py**: فحص `classroom.school_id` في `delete_enrollment`
6. **academy.py**: إضافة `set_tenant_context` في جميع نقاط النهاية
7. **academy.py**: إضافة عزل المدرسة في `list_quiz_attempts`
8. **adaptive_pathway.py**: إضافة فحص الدور في `/notions/{id}/statut-publication`

### المرحلة 2: إصلاح الأخطاء المالية الحرجة
**الهدف:** ضمان سلامة المعاملات المالية

1. إصلاح فرصة السباق في `consume_credits()` — استخدام `SELECT FOR UPDATE` في استعلام واحد
2. إضافة اختبارات `consume_credits()` (5 اختبارات على الأقل)
3. إصلاح `course_lifecycle.py` — إضافة اختبارات لجميع انتقالات الحالة (12+ اختبار)
4. إضافة اختبارات `goal_scheduler.py` (4 اختبارات على الأقل)
5. إصلاح تسرّب الذاكرة في `_status_cache` — إضافة `maxsize` + `TTL`

### المرحلة 3: اختبارات الخدمات الحرجة
**الهدف:** تغطية اختبارات للخدمات التي تتطلب صفر اختبارات

1. اختبارات `gamification.py` (5 اختبارات: شارات + سلاسل + تصنيفات)
2. اختبارات `notification_service.py` (4 اختبارات: إرسال مباشر + إذاعي)
3. اختبارات `rag_service.py` (3 اختبارات: سؤال + استيعاب + سياق)
4. اختبارات `embeddings_service.py` (3 اختبارات: إضافة + بحث + إحصائيات)
5. اختبارات `provider_client.py` (2 اختبارات: اتصال + توليد)

### المرحلة 4: واجهة المعلم + إصلاحات الأمام
**الهدف:** إكمال تجربة المعلم وإصلاح الأخطاء البصرية

1. **إضافة طلاب للصف** — إنشاء نقطة نهاية `GET /api/teacher/students/search` + واجهة بحث في `ClassroomManager.tsx`
2. **صفحة إنشاء الدورات للمعلم** — صفحة مخصصة تختلف عن `CourseBuilderPage` الخاص بالمشرف
3. إصلاح `ler_eleve` — التحقق من المدرسة عند ربط الطفل
4. صفحة إعادة تعيين كلمة المرور (نسيت كلمة المرور)

### المرحلة 5: اختبارات API المفقودة
**الهدف:** تغطية اختبارات لنقاط النهاية غير المُختبَرة

1. اختبارات `POST /api/wallet/purchase` (شراء محفظة)
2. اختبارات `GET /api/lms/classes` + CRUD (نقطة نهاية LMS)
3. اختبارات `POST /api/pathway/*` (نقاط نهاية المسار)
4. اختبارات `POST /api/payments/checkout` + `webhook` (Stripe)
5. اختبارات `POST /api/conversations` + رسائل (محادثات)
6. اختبارات `POST /api/gamification/*` (نقاط نهاية التلعيم)
7. اختبارات `POST /api/pedagogical-lead/*` (نقاط نهاية القيادة التعليمية)
8. اختبارات تسجيل المستخدمين (نجاح + فشل)

### المرحلة 6: تحسينات الأداء
**الهدف:** إصلاح مشاكل الأداء المحددة في التدقيق

1. `embeddings_service.py` — تخزين متجه TF-IDF مؤقتاً بدلاً من إعادة بنائه في كل استعلام
2. `rag_service.py` — إزالة الدالة المكررة `ask_tutor()`
3. `gamification.py` — تحويل `compute_rankings()` إلى SQL بدل بايثون
4. `goal_scheduler.py` — إضافة حجم الدفعة لتجنب تحميل جميع الطلاب في الذاكرة
5. `notification_service.py` — جعل `sender_id` قابل للتكوين بدلاً من `1` ثابت

---

## ثالثاً: نطاق كل مرحلة

### المرحلة 0: البنية التحتية
**ضمن النطاق:**
- ملفات `alembic.ini` + `alembic/env.py` + `alembic/versions/`
- هجرة SQL → Alembic versions
- تحديث `pyproject.toml` و `requirements.txt`
- تحديث `docker-compose.yml`
- إعادة هيكلة `conftest.py`

**خارج النطاق:**
- إعادة كتابة جميع الاختبارات
- تغيير بنية قاعدة البيانات
- إضافة جداول جديدة

### المرحلة 1: عزل الإيجار
**ضمن النطاق:**
- `courses.py` — 14 نقطة نهاية
- `lms.py` — 23 نقطة نهاية
- `academy.py` — 23 نقطة نهاية
- `adaptive_pathway.py` — 3 نقاط نهاية (فقط those بدون فحص دور)
- اختبارات جديدة لعزل المدرسة

**خارج النطاق:**
- تعديل `deps.py` (النظام الحالي صحيح)
- إضافة أدوار جديدة
- تغيير منطق `has_course_access()`

### المرحلة 2: المالية
**ضمن النطاق:**
- `consume_credits()` — فرصة السباق
- `course_lifecycle.py` — اختبارات
- `goal_scheduler.py` — اختبارات + أداء
- `_status_cache` — تسرّب ذاكرة

**خارج النطاق:**
- Stripe webhooks
- نظام الدفع الجديد
- تغيير نموذج العمل

### المرحلة 3: اختبارات الخدمات
**ضمن النطاق:**
- ملفات اختبار جديدة لكل خدمة
- fixtures مشتركة

**خارج النطاق:**
- اختبارات الأداء (load testing)
- اختبارات الأمان (penetration testing)

### المرحلة 4: واجهة المعلم
**ضمن النطاق:**
- `ClassroomManager.tsx` — نموذج إضافة طلاب
- `TeacherCourseCreatePage.tsx` — صفحة جديدة
- `parent.py` — فحص المدرسة في `lier_eleve`
- صفحة إعادة تعيين كلمة المرور

**خارج النطاق:**
- تطبيق Flutter
- تحسينات واجهة المستخدم العامة

### المرحلة 5: اختبارات API
**ضمن النطاق:**
- 50+ اختبار جديدة لنقاط النهاية غير المُختبَرة

**خارج النطاق:**
- اختبارات التكامل الكاملة
- اختبارات E2E

### المرحلة 6: الأداء
**ضمن النطاق:**
- 5 خدمات محددة
- تحسينات الاستعلام

**خارج النطاق:**
- تحسينات قاعدة البيانات (فهارس جديدة)
- CDN / caching عام

---

## رابعاً: معايير القبول

> **قاعدة أساسية:** مرحلة تُ considered مكتملة فقط إذا كان لكل معيار قبول فيها دليل تنفيذ (اختبار جارٍ، نتيجة اختبار). لا يُعتبر كود غير مُختبَر مُنجزاً.

### المرحلة 0: البنية التحتية
- [ ] `alembic upgrade head` ينجح مع PostgreSQL
- [ ] `alembic history` يعرض الهجرتين القديمتين
- [ ] `pip install -e .` ينجح مع `pyproject.toml` المُحدَّث
- [ ] `docker-compose up` يعمل بدون أخطاء (بدون `alembic upgrade head || true`)
- [ ] `pytest` ينجح مع `conftest.py` المُوحَّد (لا تكرار في إعداد قاعدة البيانات)

### المرحلة 1: عزل الإيجار
- [ ] `GET /api/courses` يُرجع 403 للمعلم من مدرسة مختلفة (اختبار جارٍ)
- [ ] `PUT /api/courses/{id}` يُرجع 403 للمعلم غير المالك (اختبار جارٍ)
- [ ] `GET /api/lms/progress` لا يُرجع بيانات مدرسة مختلفة (اختبار جارٍ)
- [ ] `GET /api/academy/quizzes/{id}/attempts` يُرجع فقط محاولات المدرسة (اختبار جارٍ)
- [ ] `GET /api/pathway/notions/{id}/statut-publication` يُرجع 403 لطالب عادي (اختبار جارٍ)

### المرحلة 2: المالية
- [ ] `consume_credits()` — 5 اختبارات سباق (اختبار جارٍ)
- [ ] `can_transition_status()` — 12 اختبار انتقال (اختبار جارٍ)
- [ ] `start_goal_scheduler()` — اختبار توليد الأهداف (اختبار جارٍ)
- [ ] `_status_cache` — لا تسرّب ذاكرة بعد 1000 إدخال (اختبار جارٍ)

### المرحلة 3: اختبارات الخدمات
- [ ] `gamification.py` — اختبار شارة + اختبار سلسلة + اختبار تصنيف (اختبار جارٍ)
- [ ] `notification_service.py` — اختبار إرسال مباشر + إذاعي (اختبار جارٍ)
- [ ] `rag_service.py` — اختبار سؤال + استيعاب (اختبار جارٍ)
- [ ] `embeddings_service.py` — اختبار إضافة + بحث (اختبار جارٍ)

### المرحلة 4: واجهة المعلم
- [ ] `POST /api/teacher/students/search` يُرجع نتائج بحث (اختبار جارٍ)
- [ ] `ClassroomManager.tsx` — نموذج إضافة طلاب يعمل مع API
- [ ] `POST /auth/register` مع `parent` role يفشل إذا لم تتطابق المدرسة (اختبار جارٍ)
- [ ] صفحة إعادة تعيين كلمة المرور تُظهر نموذج + ترسل بريد (اختبار يدوي)

### المرحلة 5: اختبارات API
- [ ] `POST /api/wallet/purchase` — 3 اختبارات (نقر، رصيد غير كافٍ، تكرار)
- [ ] `GET /api/lms/classes` — 2 اختبارات (قائمة + تفاصيل)
- [ ] `POST /api/pathway/auto-enroll-from-test` — 2 اختبار (نجاح + بالفعل مسجل)
- [ ] `POST /api/conversations` — 2 اختبار (إنشاء + رسائل)
- [ ] `POST /auth/register` — 3 اختبار (نجاح + فشل + مدرسة)

### المرحلة 6: الأداء
- [ ] `embeddings_service.similarity_search()` لا يعيد بناء المتجه في كل استعلام (اختبار جارٍ)
- [ ] `compute_rankings()` يستعلم عبر SQL بدل بايثون (اختبار جارٍ)
- [ ] `goal_scheduler` لا يحمل كل الطلاب في الذاكرة (اختبار جارٍ)

---

## خامساً: الأولوية

### 🔴 حرج — يجب إصلاحه قبل أي إطلاق تجاري
1. **عزل الإيجار** (المرحلة 1) — فشل عزل المدارس = اختراق أمان
2. **البنية التحتية** (المرحلة 0) — بدون Alembic لا يمكن نشر تحديثات
3. **المالية** (المرحلة 2) — فرصة السباق في `consume_credits()` = خسارة مالية

### 🟡 مهم — يمكن تأجيله قليلاً
4. اختبارات الخدمات الحرجة (المرحلة 3)
5. واجهة المعلم + إضافة طلاب (المرحلة 4)
6. اختبارات API (المرحلة 5)

### 🟢 تحسينات مستقبلية
7. أداء التخزين المؤقت (المرحلة 6)
8. إعادة تعيين كلمة المرور
9. صفحة إنشاء الدورات للمعلم

---

## سادساً: تقدير الجهد

| المرحلة | الجهد النسبي | السبب |
|---------|-------------|-------|
| 0: البنية التحتية | **متوسط** | 5 ملفات + هجرة SQL + مزامنة تبعيات — لكن لا يلمس كود الأعمال |
| 1: عزل الإيجار | **عالي** | 80+ نقطة نهاية عبر 4 ملفات + اختبارات جديدة — لكن النمط موحد |
| 2: المالية | **متوسط** | تعديل 3 خدمات + 20+ اختبار — لكن التعقيد في فرصة السباق |
| 3: اختبارات الخدمات | **عالي** | 5 خدمات × ~4 اختبارات = ~20 ملف اختبار جديد |
| 4: واجهة المعلم | **متوسط** | نقطة نهاية جديدة + صفحة React + تعديل 1 ملف بايثون |
| 5: اختبارات API | **عالي** | ~50 اختبار جديد عبر ~10 ملفات |
| 6: الأداء | **منخفض** | 5 تعديلات في 5 خدمات — تغييرات بسيطة |

**الإجمالي المقدر:** ~40-60 ساعة عمل تقريباً

---

> تاريخ آخر تحديث: 2026-08-01

---
---

# PLAN D'IMPLÉMENTATION — EDUAI Learning

---

## 1. ÉTAT DES LIEUX RÉEL

### RBAC & Authentification
| Composant | État |
|-----------|------|
| 7 rôles RBAC (super_admin, admin_school, pedagogical_admin, pedagogical_lead, teacher, student, parent) | ✅ Implémenté et testé |
| Multi-tenancy avec `set_tenant_context` | ⚠️ Implémenté mais **non activé** dans courses.py, lms.py, academy.py — ces fichiers utilisent `get_current_user` directement sans activer le filtre tenant |
| Protection login + lockout compte (5 tentatives) | ✅ Implémenté et testé |
| Codes d'invitation école | ✅ Implémenté |
| Vérification `check_school_access()` | ✅ Implémenté mais **non utilisé** dans courses.py et academy.py |
| Vérification `has_course_access()` | ✅ Implémenté et testé (23 tests + 13 tests 403) |

### Portefeuille & Finances
| Composant | État |
|-----------|------|
| `debit_dt()` / `credit_dt()` — Numeric(10,2) | ✅ Implémenté et testé (6 tests) |
| `consume_credits()` — consommation par priorité | ⚠️ Implémenté mais **non testé** + race condition |
| `purchase_course()` — débit atomique + inscription | ✅ Implémenté et testé |
| Abonnements Stripe | ⚠️ Implémenté mais **non testé** |
| Achat cours payants | ✅ Implémenté et testé |

### Cours & Contenu
| Composant | État |
|-----------|------|
| CRUD cours (admin/academy) | ✅ Implémenté et testé |
| `course_lifecycle.py` — transitions de statut | ⚠️ Implémenté avec **0 test** |
| Validation pédagogique double | ✅ Implémenté |
| `has_course_access()` 7 étapes | ✅ Implémenté et testé |

### Parcours Adaptatif
| Composant | État |
|-----------|------|
| 5 niveaux (Découverte → Maîtrise) | ✅ Implémenté et testé (10 tests) |
| Réorientation automatique | ✅ Implémenté et testé |
| Vérification publication | ✅ Implémenté et testé |
| Profil d'assimilation | ✅ Implémenté et testé |
| Arborescence (niveaux/matieres/chapitres) | ✅ Implémenté |

### Intelligence Artificielle
| Composant | État |
|-----------|------|
| AI Tutor (ask/explain/correct) | ✅ Implémenté mais **non testé** |
| RAG (TF-IDF) | ⚠️ Implémenté mais **non testé** + reconstruit le vecteur à chaque requête |
| AI Factory | ✅ Implémenté mais **non testé** |
| 9 fournisseurs IA | ✅ Implémenté |

### Objectifs Pédagogiques
| Composant | État |
|-----------|------|
| Objectifs daily/weekly (auto) | ✅ Implémenté et testé |
| Objectifs mensuels (auto) | ⚠️ Implémenté mais **non testé** + fuite mémoire dans `_status_cache` |
| Planification objectifs (APScheduler) | ⚠️ Implémenté mais **non testé** |

### Gamification
| Composant | État |
|-----------|------|
| Badges/streaks/rankings | ⚠️ Implémenté mais **non testé** + `compute_rankings()` charge tous les élèves en Python |
| Notifications gamification | ⚠️ Implémenté mais **non testé** + `sender_id=1` en dur |

### Frontend
| Composant | État |
|-----------|------|
| Pages admin (41 pages) | ✅ Implémenté |
| Pages enseignant (8 pages) | ✅ Implémenté (7/8 — ajout d'élèves bloqué) |
| Pages élève (13 pages) | ✅ Implémenté |
| Pages parent (2 pages) | ✅ Implémenté |
| Page création cours enseignant | ❌ Non implémenté |
| Réinitialisation mot de passe | ❌ Non implémenté |

### Infrastructure
| Composant | État |
|-----------|------|
| Alembic (migrations DB) | ❌ **Inexistant** — Docker le référence mais absent |
| pyproject.toml vs requirements.txt | ⚠️ Incohérent (SQLAlchemy 1.4 vs 2.0) |
| Tests SQLite | ✅ Implémenté avec duplication massive (~15 copies du setup) |

---

## 2. DÉCOUPAGE EN PHASES

### Phase 0: Infrastructure & DevOps
**Objectif:** Établir des environnements de développement, test et déploiement fiables.

1. Créer `alembic.ini` + `alembic/env.py` avec configuration PostgreSQL
2. Convertir les SQL bruts en versions Alembic (`numeric_monetary.sql`, `wallet_amount_float.sql`)
3. Synchroniser `pyproject.toml` avec `requirements.txt` (SQLAlchemy 2.0 + pg8000)
4. Corriger `backend/docker-compose.yml` — supprimer les credentials DB hardcodés
5. Unifier `conftest.py` — migrer tous les fichiers de test vers un système de fixtures partagé

### Phase 1: Isolation Tenant (Multi-école)
**Objectif:** Garantir que TOUTES les endpoints respectent l'isolation par école.

1. **courses.py** : Remplacer le `require_teacher` local par `require_teacher_or_admin` depuis `deps.py`
2. **courses.py** : Ajouter `set_tenant_context` dans toutes les endpoints
3. **courses.py** : Ajouter `check_school_access()` dans `update_course`
4. **lms.py** : Ajouter `set_tenant_context` dans toutes les endpoints
5. **lms.py** : Vérifier `classroom.school_id` dans `delete_enrollment`
6. **academy.py** : Ajouter `set_tenant_context` dans toutes les endpoints
7. **academy.py** : Ajouter isolation école dans `list_quiz_attempts`
8. **adaptive_pathway.py** : Ajouter vérification de rôle dans `/notions/{id}/statut-publication`

### Phase 2: Bugs Financiers Critiques
**Objectif:** Assurer l'intégrité des transactions financières.

1. Corriger la race condition dans `consume_credits()` — utiliser `SELECT FOR UPDATE` dans une seule requête
2. Ajouter des tests pour `consume_credits()` (minimum 5 tests)
3. Corriger `course_lifecycle.py` — ajouter des tests pour toutes les transitions (12+ tests)
4. Ajouter des tests pour `goal_scheduler.py` (minimum 4 tests)
5. Corriger la fuite mémoire dans `_status_cache` — ajouter `maxsize` + `TTL`

### Phase 3: Tests des Services Critiques
**Objectif:** Couverture de tests pour les services à 0 test.

1. Tests `gamification.py` (5 tests : badges, streaks, rankings)
2. Tests `notification_service.py` (4 tests : envoi direct + broadcast)
3. Tests `rag_service.py` (3 tests : ask, ingest, context)
4. Tests `embeddings_service.py` (3 tests : add, search, stats)
5. Tests `provider_client.py` (2 tests : connexion, génération)

### Phase 4: Expérience Enseignant + Corrections Frontend
**Objectif:** Compléter l'expérience enseignant et corriger les bugs visuels.

1. **Ajout d'élèves en classe** — créer endpoint `GET /api/teacher/students/search` + recherche dans `ClassroomManager.tsx`
2. **Page création cours enseignant** — page dédiée distincte de `CourseBuilderPage` admin
3. Corriger `lier_eleve` — vérifier l'école lors de la liaison parent-élève
4. Page réinitialisation mot de passe (forgot password)

### Phase 5: Tests API Manquants
**Objectif:** Couverture de tests pour les endpoints non testés.

1. Tests `POST /api/wallet/purchase`
2. Tests `GET /api/lms/classes` + CRUD
3. Tests `POST /api/pathway/*`
4. Tests `POST /api/payments/checkout` + `webhook`
5. Tests `POST /api/conversations` + messages
6. Tests `POST /api/gamification/*`
7. Tests `POST /api/pedagogical-lead/*`
8. Tests inscription utilisateurs (succès + échec)

### Phase 6: Optimisations Performance
**Objectif:** Corriger les problèmes de performance identifiés dans l'audit.

1. `embeddings_service.py` — cache du vecteur TF-IDF au lieu de le reconstruire à chaque requête
2. `rag_service.py` — supprimer la fonction dupliquée `ask_tutor()`
3. `gamification.py` — convertir `compute_rankings()` en SQL au lieu de Python
4. `goal_scheduler.py` — ajouter un batch size pour ne pas charger tous les élèves en mémoire
5. `notification_service.py` — rendre `sender_id` configurable au lieu de `1` en dur

---

## 3. PÉRIMÈTRE PRÉCIS PAR PHASE

### Phase 0: Infrastructure
**Dans le périmètre :**
- Fichiers `alembic.ini` + `alembic/env.py` + `alembic/versions/`
- Migration SQL → versions Alembic
- Mise à jour `pyproject.toml` et `requirements.txt`
- Mise à jour `docker-compose.yml`
- Restructuration `conftest.py`

**Hors périmètre :**
- Réécriture de tous les tests
- Changement de schéma de base de données
- Ajout de nouvelles tables

**Dépendances :** Aucune — première phase, fondation pour toutes les autres.

### Phase 1: Isolation Tenant
**Dans le périmètre :**
- `courses.py` — 14 endpoints
- `lms.py` — 23 endpoints
- `academy.py` — 23 endpoints
- `adaptive_pathway.py` — 3 endpoints (celles sans vérification de rôle)
- Nouveaux tests d'isolation école

**Hors périmètre :**
- Modification de `deps.py` (le système actuel est correct)
- Ajout de nouveaux rôles
- Changement de la logique `has_course_access()`

**Dépendances :** Phase 0 (Alembic doit fonctionner pour exécuter les tests).

### Phase 2: Financier
**Dans le périmètre :**
- `consume_credits()` — race condition
- `course_lifecycle.py` — tests
- `goal_scheduler.py` — tests + performance
- `_status_cache` — fuite mémoire

**Hors périmètre :**
- Webhooks Stripe
- Nouveau système de paiement
- Changement de modèle économique

**Dépendances :** Phase 1 (l'isolation tenant doit être en place avant de tester les transactions financières cross-école).

### Phase 3: Tests Services
**Dans le périmètre :**
- Nouveaux fichiers de test pour chaque service
- Fixtures partagées

**Hors périmètre :**
- Tests de performance (load testing)
- Tests de sécurité (penetration testing)

**Dépendances :** Phase 2 (les tests financiers doivent être stables avant d'ajouter d'autres couches de test).

### Phase 4: Enseignant
**Dans le périmètre :**
- `ClassroomManager.tsx` — formulaire ajout élèves
- `TeacherCourseCreatePage.tsx` — nouvelle page
- `parent.py` — vérification école dans `lier_eleve`
- Page réinitialisation mot de passe

**Hors périmètre :**
- Application Flutter
- Améliorations UI globales

**Dépendances :** Phase 1 (l'isolation tenant doit être active pour les endpoints enseignant).

### Phase 5: Tests API
**Dans le périmètre :**
- ~50 nouveaux tests pour endpoints non testés

**Hors périmètre :**
- Tests d'intégration complets
- Tests E2E

**Dépendances :** Phases 1+2 (les endpoints doivent être sécurisés avant d'être testés positivement).

### Phase 6: Performance
**Dans le périmètre :**
- 5 services spécifiques
- Optimisations de requêtes

**Hors périmètre :**
- Nouvelles index DB
- CDN / caching général

**Dépendances :** Phase 3 (les tests doivent couvrir les services avant d'optimiser).

---

## 4. CRITÈRES D'ACCEPTATION PAR PHASE

> **Règle fondamentale :** Une phase n'est considérée terminée que si TOUS ses critères d'acceptation ont une preuve d'exécution (test passant, capture de résultat). Le code non testé n'est pas considéré comme livré.

### Phase 0: Infrastructure
- [ ] `alembic upgrade head` réussit sur PostgreSQL
- [ ] `alembic history` affiche les 2 migrations historiques
- [ ] `pip install -e .` réussit avec `pyproject.toml` mis à jour
- [ ] `docker-compose up` fonctionne sans erreurs (sans `alembic upgrade head || true`)
- [ ] `pytest` réussit avec `conftest.py` unifié (pas de duplication de setup DB)

### Phase 1: Isolation Tenant
- [ ] `GET /api/courses` retourne 403 pour un enseignant d'une autre école (test passant)
- [ ] `PUT /api/courses/{id}` retourne 403 pour un enseignant non propriétaire (test passant)
- [ ] `GET /api/lms/progress` ne retourne pas les données d'une autre école (test passant)
- [ ] `GET /api/academy/quizzes/{id}/attempts` retourne uniquement les tentatives de l'école (test passant)
- [ ] `GET /api/pathway/notions/{id}/statut-publication` retourne 403 pour un élève standard (test passant)

### Phase 2: Financier
- [ ] `consume_credits()` — 5 tests de race condition (test passant)
- [ ] `can_transition_status()` — 12 tests de transition (test passant)
- [ ] `start_goal_scheduler()` — test de génération d'objectifs (test passant)
- [ ] `_status_cache` — pas de fuite mémoire après 1000 entrées (test passant)

### Phase 3: Tests Services
- [ ] `gamification.py` — test badge + test streak + test ranking (test passant)
- [ ] `notification_service.py` — test envoi direct + broadcast (test passant)
- [ ] `rag_service.py` — test ask + ingest (test passant)
- [ ] `embeddings_service.py` — test add + search (test passant)

### Phase 4: Enseignant
- [ ] `POST /api/teacher/students/search` retourne des résultats (test passant)
- [ ] `ClassroomManager.tsx` — formulaire ajout élèves fonctionne avec l'API
- [ ] `POST /auth/register` avec rôle `parent` échoue si école ne correspond pas (test passant)
- [ ] Page réinitialisation mot de passe affiche formulaire + envoie email (test manuel)

### Phase 5: Tests API
- [ ] `POST /api/wallet/purchase` — 3 tests (succès, solde insuffisant, doublon)
- [ ] `GET /api/lms/classes` — 2 tests (liste + détail)
- [ ] `POST /api/pathway/auto-enroll-from-test` — 2 tests (succès, déjà inscrit)
- [ ] `POST /api/conversations` — 2 tests (création + messages)
- [ ] `POST /auth/register` — 3 tests (succès, échec, école)

### Phase 6: Performance
- [ ] `embeddings_service.similarity_search()` ne reconstruit pas le vecteur à chaque requête (test passant)
- [ ] `compute_rankings()` utilise SQL au lieu de Python (test passant)
- [ ] `goal_scheduler` ne charge pas tous les élèves en mémoire (test passant)

---

## 5. PRIORISATION

### 🔴 Bloquant — doit être corrigé avant tout lancement commercial
1. **Isolation Tenant** (Phase 1) — échec d'isolation école = faille de sécurité critique
2. **Infrastructure** (Phase 0) — sans Alembic, impossible de déployer des mises à jour
3. **Financier** (Phase 2) — race condition dans `consume_credits()` = perte financière

### 🟡 Important — peut être différé légèrement
4. Tests services critiques (Phase 3)
5. Expérience enseignant + ajout élèves (Phase 4)
6. Tests API (Phase 5)

### 🟢 Améliorations futures
7. Optimisations performance (Phase 6)
8. Réinitialisation mot de passe
9. Page création cours enseignant

---

## 6. ESTIMATION D'EFFORT

| Phase | Effort relatif | Justification |
|-------|----------------|---------------|
| 0: Infrastructure | **Moyen** | 5 fichiers + migration SQL + sync dépendances — mais ne touche pas le code métier |
| 1: Isolation Tenant | **Élevé** | 80+ endpoints sur 4 fichiers + nouveaux tests — mais le pattern est unifié |
| 2: Financier | **Moyen** | 3 services modifiés + 20+ tests — mais le complexe est dans la race condition |
| 3: Tests Services | **Élevé** | 5 services × ~4 tests = ~20 nouveaux fichiers de test |
| 4: Enseignant | **Moyen** | Nouvel endpoint + page React + 1 fichier Python modifié |
| 5: Tests API | **Élevé** | ~50 nouveaux tests sur ~10 fichiers |
| 6: Performance | **Faible** | 5 modifications dans 5 services — changements simples |

**Total estimé :** ~40-60 heures de travail

---

### Phase 7: ABAC Engine & CMS Lifecycle
**Objectif:** Préparer l'évolution RBAC → ABAC et implémenter le cycle de vie du contenu.

1. **Context Switcher** — ajouter `active_context_role` sur `users`, endpoint `PUT /auth/switch-context`, frontend role-switcher
2. **Impersonation** — créer table `audit_impersonations`, endpoints `/api/support/impersonate/*`, durée max 30min
3. **ABAC Engine (foundation)** — créer table `abac_policies`, parser les politiques JSON, évaluer au moment de la requête
4. **CMS Lifecycle (backend)** — ajouter `cms_status` sur `lessons`, transitions d'état, notifications automatiques
5. **AI Factory Atomization** — endpoints `generate-lesson`, `generate-quiz`, `generate-chapter` séparés
6. **Versioning / Fork** — colonnes `version_number`, `is_active_version` sur `courses`, endpoint `/courses/{id}/version`
7. **Bulk Seats** — table `bulk_seat_vouchers`, endpoint `/api/schools/bulk-seats/purchase`
8. **Revenue Share Ledger** — table `teacher_revenue_ledger`, calcul automatique après chaque achat

**Dépendances:** Phase 2 (financial) + Phase 3 (service tests) doivent être stables.

**Critères d'acceptation:**
- [ ] `PUT /auth/switch-context` change le rôle actif sans reconnexion (test passant)
- [ ] `POST /api/support/impersonate/{user_id}` crée une session avec durée max 30min (test passant)
- [ ] `audit_impersonations` enregistre chaque session avec impersonator, target, reason, timestamps (test passant)
- [ ] `POST /api/ai-factory/generate-lesson` produit 1 leçon draft (test passant)
- [ ] `POST /api/cms/lessons/{id}/submit` passe `cms_status` de `brouillon` à `soumis` (test passant)
- [ ] `POST /api/schools/bulk-seats/purchase` crée des vouchers (test passant)
- [ ] `GET /api/teacher/revenue-report` affiche les revenus (test passant)
- [ ] `POST /api/courses/{id}/version` crée un fork avec `version_number` incrémenté (test passant)

---

> Dernière mise à jour : 2026-08-06

---
---

# IMPLEMENTATION PLAN — EDUAI Learning

---

## 1. CURRENT STATE ASSESSMENT

### RBAC & Authentication
| Component | Status |
|-----------|--------|
| 7 RBAC roles (super_admin, admin_school, pedagogical_admin, pedagogical_lead, teacher, student, parent) | ✅ Implemented and tested |
| Multi-tenancy with `set_tenant_context` | ⚠️ Implemented but **not activated** in courses.py, lms.py, academy.py — all use `get_current_user` directly without enabling tenant filter |
| Login protection + account lockout (5 attempts) | ✅ Implemented and tested |
| School invite codes | ✅ Implemented |
| `check_school_access()` verification | ✅ Implemented but **not used** in courses.py and academy.py |
| `has_course_access()` verification | ✅ Implemented and tested (23 tests + 13 tests 403) |

### Wallet & Finances
| Component | Status |
|-----------|--------|
| `debit_dt()` / `credit_dt()` — Numeric(10,2) | ✅ Implemented and tested (6 tests) |
| `consume_credits()` — priority consumption | ⚠️ Implemented but **not tested** + race condition |
| `purchase_course()` — atomic debit + enrollment | ✅ Implemented and tested |
| Stripe subscriptions | ⚠️ Implemented but **not tested** |
| Paid course purchases | ✅ Implemented and tested |

### Courses & Content
| Component | Status |
|-----------|--------|
| Course CRUD (admin/academy) | ✅ Implemented and tested |
| `course_lifecycle.py` — status transitions | ⚠️ Implemented with **0 tests** |
| Double pedagogical validation | ✅ Implemented |
| `has_course_access()` 7-step check | ✅ Implemented and tested |

### Adaptive Pathway
| Component | Status |
|-----------|--------|
| 5 layers (Découverte → Maîtrise) | ✅ Implemented and tested (10 tests) |
| Auto-reorientation | ✅ Implemented and tested |
| Publication status check | ✅ Implemented and tested |
| Assimilation profile | ✅ Implemented and tested |
| Tree structure (levels/subjects/chapters) | ✅ Implemented |

### Artificial Intelligence
| Component | Status |
|-----------|--------|
| AI Tutor (ask/explain/correct) | ✅ Implemented but **not tested** |
| RAG (TF-IDF) | ⚠️ Implemented but **not tested** + rebuilds vector on every query |
| AI Factory | ✅ Implemented but **not tested** |
| 9 AI providers | ✅ Implemented |

### Learning Goals
| Component | Status |
|-----------|--------|
| Daily/weekly goals (auto) | ✅ Implemented and tested |
| Monthly goals (auto) | ⚠️ Implemented but **not tested** + memory leak in `_status_cache` |
| Goal scheduling (APScheduler) | ⚠️ Implemented but **not tested** |

### Gamification
| Component | Status |
|-----------|--------|
| Badges/streaks/rankings | ⚠️ Implemented but **not tested** + `compute_rankings()` loads all students in Python |
| Gamification notifications | ⚠️ Implemented but **not tested** + hardcoded `sender_id=1` |

### Frontend
| Component | Status |
|-----------|--------|
| Admin pages (41 pages) | ✅ Implemented |
| Teacher pages (8 pages) | ✅ Implemented (7/8 — add students blocked) |
| Student pages (13 pages) | ✅ Implemented |
| Parent pages (2 pages) | ✅ Implemented |
| Teacher course creation page | ❌ Not implemented |
| Password reset flow | ❌ Not implemented |

### Infrastructure
| Component | Status |
|-----------|--------|
| Alembic (DB migrations) | ❌ **Missing** — Docker references it but it doesn't exist |
| pyproject.toml vs requirements.txt | ⚠️ Inconsistent (SQLAlchemy 1.4 vs 2.0) |
| SQLite tests | ✅ Implemented with massive duplication (~15 copies of setup) |

---

## 2. PHASED PLAN

### Phase 0: Infrastructure & DevOps
**Objective:** Establish reliable development, testing, and deployment environments.

1. Create `alembic.ini` + `alembic/env.py` with PostgreSQL configuration
2. Convert raw SQL to Alembic versions (`numeric_monetary.sql`, `wallet_amount_float.sql`)
3. Sync `pyproject.toml` with `requirements.txt` (SQLAlchemy 2.0 + pg8000)
4. Fix `backend/docker-compose.yml` — remove hardcoded DB credentials
5. Unify `conftest.py` — migrate all test files to shared fixture system

### Phase 1: Tenant Isolation
**Objective:** Ensure ALL endpoints respect school-based data isolation.

1. **courses.py**: Replace local `require_teacher` with `require_teacher_or_admin` from `deps.py`
2. **courses.py**: Add `set_tenant_context` to all endpoints
3. **courses.py**: Add `check_school_access()` to `update_course`
4. **lms.py**: Add `set_tenant_context` to all endpoints
5. **lms.py**: Verify `classroom.school_id` in `delete_enrollment`
6. **academy.py**: Add `set_tenant_context` to all endpoints
7. **academy.py**: Add school isolation to `list_quiz_attempts`
8. **adaptive_pathway.py**: Add role check to `/notions/{id}/statut-publication`

### Phase 2: Critical Financial Bugs
**Objective:** Ensure financial transaction integrity.

1. Fix race condition in `consume_credits()` — use `SELECT FOR UPDATE` in a single query
2. Add tests for `consume_credits()` (minimum 5 tests)
3. Fix `course_lifecycle.py` — add tests for all status transitions (12+ tests)
4. Add tests for `goal_scheduler.py` (minimum 4 tests)
5. Fix memory leak in `_status_cache` — add `maxsize` + `TTL`

### Phase 3: Critical Service Tests
**Objective:** Test coverage for services with 0 tests.

1. Tests for `gamification.py` (5 tests: badges, streaks, rankings)
2. Tests for `notification_service.py` (4 tests: direct + broadcast)
3. Tests for `rag_service.py` (3 tests: ask, ingest, context)
4. Tests for `embeddings_service.py` (3 tests: add, search, stats)
5. Tests for `provider_client.py` (2 tests: connection, generation)

### Phase 4: Teacher Experience + Frontend Fixes
**Objective:** Complete the teacher experience and fix visual bugs.

1. **Add students to class** — create `GET /api/teacher/students/search` endpoint + search in `ClassroomManager.tsx`
2. **Teacher course creation page** — dedicated page different from admin's `CourseBuilderPage`
3. Fix `lier_eleve` — verify school when linking parent-child
4. Password reset page (forgot password)

### Phase 5: Missing API Tests
**Objective:** Test coverage for untested endpoints.

1. Tests for `POST /api/wallet/purchase`
2. Tests for `GET /api/lms/classes` + CRUD
3. Tests for `POST /api/pathway/*`
4. Tests for `POST /api/payments/checkout` + `webhook`
5. Tests for `POST /api/conversations` + messages
6. Tests for `POST /api/gamification/*`
7. Tests for `POST /api/pedagogical-lead/*`
8. User registration tests (success + failure)

### Phase 6: Performance Optimizations
**Objective:** Fix performance issues identified in audit.

1. `embeddings_service.py` — cache TF-IDF vectorizer instead of rebuilding on every query
2. `rag_service.py` — remove duplicate `ask_tutor()` function
3. `gamification.py` — convert `compute_rankings()` to SQL instead of Python
4. `goal_scheduler.py` — add batch size to avoid loading all students into memory
5. `notification_service.py` — make `sender_id` configurable instead of hardcoded `1`

---

## 3. PRECISE SCOPE PER PHASE

### Phase 0: Infrastructure
**In scope:**
- `alembic.ini` + `alembic/env.py` + `alembic/versions/` files
- SQL → Alembic version migrations
- `pyproject.toml` and `requirements.txt` updates
- `docker-compose.yml` updates
- `conftest.py` restructuring

**Out of scope:**
- Rewriting all tests
- Changing database schema
- Adding new tables

**Dependencies:** None — first phase, foundation for all others.

### Phase 1: Tenant Isolation
**In scope:**
- `courses.py` — 14 endpoints
- `lms.py` — 23 endpoints
- `academy.py` — 23 endpoints
- `adaptive_pathway.py` — 3 endpoints (those without role checks)
- New school isolation tests

**Out of scope:**
- Modifying `deps.py` (current system is correct)
- Adding new roles
- Changing `has_course_access()` logic

**Dependencies:** Phase 0 (Alembic must work to run tests).

### Phase 2: Financial
**In scope:**
- `consume_credits()` — race condition
- `course_lifecycle.py` — tests
- `goal_scheduler.py` — tests + performance
- `_status_cache` — memory leak

**Out of scope:**
- Stripe webhooks
- New payment system
- Business model changes

**Dependencies:** Phase 1 (tenant isolation must be in place before testing cross-school financial transactions).

### Phase 3: Service Tests
**In scope:**
- New test files for each service
- Shared fixtures

**Out of scope:**
- Performance testing (load testing)
- Security testing (penetration testing)

**Dependencies:** Phase 2 (financial tests must be stable before adding other test layers).

### Phase 4: Teacher Experience
**In scope:**
- `ClassroomManager.tsx` — add student form
- `TeacherCourseCreatePage.tsx` — new page
- `parent.py` — school check in `lier_eleve`
- Password reset page

**Out of scope:**
- Flutter mobile app
- Global UI improvements

**Dependencies:** Phase 1 (tenant isolation must be active for teacher endpoints).

### Phase 5: API Tests
**In scope:**
- ~50 new tests for untested endpoints

**Out of scope:**
- Full integration tests
- E2E tests

**Dependencies:** Phases 1+2 (endpoints must be secured before positive testing).

### Phase 6: Performance
**In scope:**
- 5 specific services
- Query optimizations

**Out of scope:**
- New DB indexes
- General CDN / caching

**Dependencies:** Phase 3 (tests must cover services before optimization).

---

## 4. ACCEPTANCE CRITERIA PER PHASE

> **Fundamental rule:** A phase is considered complete ONLY if ALL its acceptance criteria have execution proof (passing test, result capture). Untested code is NOT considered delivered.

### Phase 0: Infrastructure
- [ ] `alembic upgrade head` succeeds on PostgreSQL
- [ ] `alembic history` displays the 2 historical migrations
- [ ] `pip install -e .` succeeds with updated `pyproject.toml`
- [ ] `docker-compose up` works without errors (without `alembic upgrade head || true`)
- [ ] `pytest` passes with unified `conftest.py` (no DB setup duplication)

### Phase 1: Tenant Isolation
- [ ] `GET /api/courses` returns 403 for teacher from different school (passing test)
- [ ] `PUT /api/courses/{id}` returns 403 for non-owner teacher (passing test)
- [ ] `GET /api/lms/progress` does not return data from different school (passing test)
- [ ] `GET /api/academy/quizzes/{id}/attempts` returns only school's attempts (passing test)
- [ ] `GET /api/pathway/notions/{id}/statut-publication` returns 403 for regular student (passing test)

### Phase 2: Financial
- [ ] `consume_credits()` — 5 race condition tests (passing tests)
- [ ] `can_transition_status()` — 12 transition tests (passing tests)
- [ ] `start_goal_scheduler()` — goal generation test (passing test)
- [ ] `_status_cache` — no memory leak after 1000 entries (passing test)

### Phase 3: Service Tests
- [ ] `gamification.py` — badge test + streak test + ranking test (passing tests)
- [ ] `notification_service.py` — direct send + broadcast test (passing tests)
- [ ] `rag_service.py` — ask + ingest test (passing tests)
- [ ] `embeddings_service.py` — add + search test (passing tests)

### Phase 4: Teacher Experience
- [ ] `POST /api/teacher/students/search` returns results (passing test)
- [ ] `ClassroomManager.tsx` — add student form works with API
- [ ] `POST /auth/register` with `parent` role fails if school doesn't match (passing test)
- [ ] Password reset page shows form + sends email (manual test)

### Phase 5: API Tests
- [ ] `POST /api/wallet/purchase` — 3 tests (success, insufficient balance, duplicate)
- [ ] `GET /api/lms/classes` — 2 tests (list + detail)
- [ ] `POST /api/pathway/auto-enroll-from-test` — 2 tests (success, already enrolled)
- [ ] `POST /api/conversations` — 2 tests (creation + messages)
- [ ] `POST /auth/register` — 3 tests (success, failure, school)

### Phase 6: Performance
- [ ] `embeddings_service.similarity_search()` does not rebuild vector on every query (passing test)
- [ ] `compute_rankings()` uses SQL instead of Python (passing test)
- [ ] `goal_scheduler` does not load all students into memory (passing test)

---

## 5. PRIORITIZATION

### 🔴 Blocking — must be fixed before any commercial launch
1. **Tenant Isolation** (Phase 1) — school isolation failure = critical security breach
2. **Infrastructure** (Phase 0) — without Alembic, impossible to deploy updates
3. **Financial** (Phase 2) — race condition in `consume_credits()` = financial loss

### 🟡 Important — can be slightly deferred
4. Critical service tests (Phase 3)
5. Teacher experience + add students (Phase 4)
6. API tests (Phase 5)

### 🟢 Future improvements
7. Performance optimizations (Phase 6)
8. Password reset flow
9. Teacher course creation page

---

## 6. EFFORT ESTIMATION

| Phase | Relative Effort | Justification |
|-------|-----------------|---------------|
| 0: Infrastructure | **Medium** | 5 files + SQL migration + dependency sync — but doesn't touch business logic |
| 1: Tenant Isolation | **High** | 80+ endpoints across 4 files + new tests — but the pattern is unified |
| 2: Financial | **Medium** | 3 services modified + 20+ tests — but complexity is in race condition |
| 3: Service Tests | **High** | 5 services × ~4 tests = ~20 new test files |
| 4: Teacher Experience | **Medium** | New endpoint + React page + 1 Python file modified |
| 5: API Tests | **High** | ~50 new tests across ~10 files |
| 6: Performance | **Low** | 5 modifications across 5 services — simple changes |

**Total estimated:** ~40-60 hours of work

---

> Last updated: 2026-08-01

---

## ANNEXE A — Tâches du roadmap devenues obsolètes ou déjà résolues

| Tâche | Raison de l'obsolescence |
|-------|--------------------------|
| Conversion `Float → Numeric(10,2)` pour les colonnes monétaires | ✅ Résolu — migration `numeric_monetary.sql` appliquée, 11 colonnes converties |
| Fix `has_course_access()` sur endpoints de contenu | ✅ Résolu — 17 endpoints câblés, 13 tests 403 passants |
| Fix `academy.py` NameError `_role_str` | ✅ Résolu — remplacé par `get_user_role()` |
| Fix `lms.py` POST `/progress` guard `has_course_access` | ✅ Résolu — guard ajouté |
| Fix Decimal/float assertion failures dans tests | ✅ Résolu — 9 tests corrigés |
| Fix `courses.py` commission_rate `Decimal("100")` | ✅ Résolu — division corrigée |
| Fix tenant filter pack individuel `_tenant_filter_suppressed` | ✅ Résolu — packs avec `school_id=None` excluent le filtre auto |
| Fix teacher frontend role case sensitivity | ✅ Résolu — comparaison avec `.toUpperCase()` |
| Fix admin.py `timedelta` NameError | ✅ Résolu |
| Navigation 5 zones étudiant (DashboardLayout) | ✅ Résolu — sidebar complète |
| Fix teacher endpoints (8 pages) | ✅ Résolu — tous les endpoints enseignant testés via TestClient |
| Fix `teacher_classes` route mismatch | ✅ Résolu — route `GET /api/teacher/students/search` ajoutée |
| Script de réconciliation testé | ✅ Résolu — 3 tests passent sur SQLite |
| Documentation trilingue (6 livrables) | ✅ Résolu — README, PRD, Specification, Technical, Architecture, DataModel |

---

## ANNEXE B — Écarts entre les objectifs documentés et le plan proposé

| Objectif documenté (PRD/PS) | État | Raison si non planifié |
|-----------------------------|------|------------------------|
| Système de notification par email | ❌ Non implémenté | Aucun code d'envoi d'email dans le repo — nécessite choix technique (SMTP/SendGrid/Resend) + template engine. Non planifiable sans décision architecture. |
| Application Flutter mobile | ⚠️ Structure squelette | Structure `mobile/lib/` existe mais fonctionnalités basiques uniquement. Nécessite un projet dédié séparé. |
| Dashboard BI avancé | ❌ Hors périmètre PRD | Explicitement marqué "Out of Scope" dans PRODUCT-REQUIREMENTS.md |
| Système d'évaluation des enseignants | ❌ Hors périmètre PRD | Explicitement marqué "Out of Scope" dans PRODUCT-REQUIREMENTS.md |
| Passerelles de paiement tunisiennes (FDL etc.) | ❌ Hors périmètre PRD | Seul Stripe implémenté. Nécessite partenariat commercial. |
| Application offline | ❌ Hors périmètre PRD | Explicitement marqué "Out of Scope" |
| Modèle de tarification détaillé | ⚠️ Informations manquantes | PRD indique "Pricing model" comme "Info Missing" — nécessite input métier |
| Système de support client | ⚠️ Informations manquantes | PRD indique "Customer support" comme "Info Missing" |
| Sondages NPS/CSAT | ❌ Non planifié | Aucun code existant — nécessite UI + backend + intégration email |
| Suivi du temps par leçon | ❌ Non planifié | PRD mentionne comme métrique mais aucun tracking implémenté |
| Suivi des changements de palier | ❌ Non planifié | PRD mentionne comme métrique mais aucun tracking implémenté |
| Remboursement DT automatique pour eduai_catalog | ⚠️ Bug potentiel | Le chemin de remboursement met à jour l'enregistrement mais ne crédite pas DT au portefeuille — nécessite vérification |
| Action enseignant sur réorientation (confirmer/annuler) | ⚠️ Backend partiel | `NotificationReorientation` créée mais aucun endpoint pour l'action enseignant — le frontend `TeacherReorientationPage.tsx` existe mais le backend est incomplet |

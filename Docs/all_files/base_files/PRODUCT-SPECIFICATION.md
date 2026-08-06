# PRODUCT-SPECIFICATION.md — EDUAI Learning

---

## العربية — المواصفات الوظيفية الشاملة

### 1. إدارة الأدوار والصلاحيات (RBAC)

#### 1.1 الأدوار السبعة المحددة في الكود

**المصدر**: `models.py:39-47` — `UserRole` enum

| الدور | القيمة | النطاق | من يمكنه إنشاءه |
|-------|--------|--------|-----------------|
| `student` | "student" | مدرسة واحدة (school_id) |_auto-inscription_ عبر `POST /auth/register` — لا يحتاج موافقة مدير (`auth.py:79-135`) |
| `teacher` | "teacher" | مدرسة واحدة (school_id) | 3 مسارات: (1) تسجيل تجريبي فوري عبر `POST /auth/register-trial-teacher` (`auth.py:138-194`)، (2) تسجيل عادي + موافقة مدير عبر `POST /auth/teacher-register` ثم `POST /admin/teacher-registrations/{id}/review` (`admin.py:1829-1898`)، (3) تحويل من trial عبر Stripe `POST /subscriptions/upgrade-to-independent` (`subscriptions.py:306-338`) |
| `admin_school` | "admin_school" | مدرسة واحدة (school_id) | `POST /admin/user-create` — فقط super_admin يمكنه تعيين هذا الدور (`admin.py:297-298`) |
| `super_admin` | "super_admin" | شامل (جميع المدارس) | `POST /admin/user-create` — فقط super_admin آخر (`admin.py:297`) |
| `pedagogical_admin` | "pedagogical_admin" | شامل (جميع المدارس) | `POST /admin/user-create` — فقط super_admin (`admin.py:297-298`) |
| `pedagogical_lead` | "pedagogical_lead" | مدرسة واحدة (school_id) | `POST /admin/user-create` — فقط super_admin (`admin.py:297-298`) |
| `parent` | "parent" | مدرسة واحدة (school_id) | لا يوجد endpoint تسجيل عام — يتم إنشاؤه عبر `POST /admin/user-create` فقط |

#### 1.2 فصل subscription_plan عن الدور

**المصدر**: `models.py:55-59` — `SubscriptionPlan` enum

```python
class SubscriptionPlan(str, Enum):
    TRIAL = "trial"
    SCHOOL_AFFILIATED = "school_affiliated"
    INDEPENDENT_PAID = "independent_paid"
```

- `subscription_plan` ينطبق **فقط على الأساتذة** — ليس على الطلاب أو المديرين
- **لا يُستخدم للصلاحيات**: `require_active_subscription` (`deps.py:244-259`) يمنع **الكتابة فقط** (إنشاء دورات/فصول/اختبارات) khi `subscription_plan == "independent_paid"` AND منتهي الصلاحية — القراءة تمر دائماً
- `SubscriptionTier` (`models.py:48-52`) على موديل `School` — يحدد `max_users` (free=10, teacher_pro=50, school=200, institution=1000)

#### 1.3 مصفوفة الصلاحيات الكاملة

**المصدر**: `deps.py` — جميع دوال RBAC

| الإجراء | dependency المطلوب | الأدوار المسموح بها |
|---------|-------------------|---------------------|
| إدارة المدارس (CRUD) | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| إدارة المستخدمين (قراءة) | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| إنشاء مستخدم بأي دور | `require_admin` + فحص داخلي | super_admin فقط: جميع الأدوار (`admin.py:297`) |
| إنشاء مستخدم student/teacher | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead (`admin.py:299-300`) |
| تغيير دور المستخدم | `require_platform_admin` | super_admin, pedagogical_admin (`admin.py:636`) |
| تعطيل/تفعيل مستخدم | `require_platform_admin` | super_admin, pedagogical_admin |
| حذف مستخدم | `require_platform_admin` | super_admin, pedagogical_admin |
| إدارة محفظة المستخدمين | `require_platform_admin` | super_admin, pedagogical_admin |
| إعدادات المنصة | `require_platform_admin` | super_admin, pedagogical_admin |
| إدارة الباقات (tokens) | `require_platform_admin` | super_admin, pedagogical_admin |
| تكاليف/API keys | `require_platform_admin` | super_admin فقط (فحص داخلي `admin.py:1048`) |
| عرض أكواد الدعوة | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| شراء باقة مدرسية | `require_school_admin_strict` | admin_school فقط (`admin.py:2366`) |
| استيراد طلاب CSV | `require_school_admin_strict` | admin_school فقط |
| استيراد أساتذة CSV | `require_school_admin_strict` | admin_school فقط |
| مراجعة طلبات الأساتذة | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| مراجعة التحقق الهويتي | `require_super_admin` | super_admin فقط |
| إنشاء/تعديل/حذف دورات | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| نشر/إلغاء نشر دورة | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| إنشاء دروس/فصول/اختبارات | `require_admin` + `require_active_subscription` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| مراجعة بيداغوجية (B2B) | `require_pedagogical_admin` | pedagogical_admin فقط |
| مراجعة بيداغوجية محلية | `require_pedagogical_lead` | pedagogical_lead فقط |
| تعيين أهداف فصلية | `require_pedagogical_lead` | pedagogical_lead فقط |
| عرض تقارير الأداء | `require_pedagogical_lead` | pedagogical_lead فقط |
| إنشاء فصول (teacher) | `_require_teacher` | teacher, super_admin, admin_school, pedagogical_admin, pedagogical_lead (`teacher_classes.py:22-27`) |
| إدارة فصول teacher | `_require_teacher` + فحص ملكية | teacher فقط (مع ownership check) |
| AI Factory (توليد محتوى) | `require_platform_admin` | super_admin, pedagogical_admin |
| AI Tutor (أسئلة/شروحات) | `get_current_user` | جميع المستخدمين المسجلين — التحكم بالرصيد |
| شراء باقة فردية | `require_authenticated` | student فقط (فحص داخلي `packs.py:129-131`) |
| شراء دورة | `get_current_user` | جميع المستخدمين المسجلين |
| عرض واجهة الوالدين | `require_parent` | parent فقط |

#### 1.4 قواعد فصل البيانات (Multi-Tenancy)

**المصدر**: `db/session.py:1-121`

- `set_tenant_context` (`deps.py:13-33`) يضبط `current_tenant_id` تلقائياً
- `super_admin` و `pedagogical_admin` يتجاوزون الفلتر (`deps.py:25-27`)
- `check_school_access(user, resource_school_id)` (`deps.py:141-154`) يتحقق من تطابق school_id

**معايير القبول:**
- ✅ `POST /auth/register` مع `school_name` ينشئ مدرسة جديدة ويحيل الطالب لها
- ✅ `super_admin` يرى بيانات جميع المدارس
- ✅ `admin_school` في مدرسة A لا يرى بيانات مدرسة B (مختبر: `test_tenant_filter.py`)
- ✅ `parent` يرى فقط أبناءه المرتبطين عبر `ParentEnfant` (`parent.py:58-105`)

---

### 2. دورة حياة الدورة التعليمية

#### 2.1 نظام الحالة المزدوج

**المصدر**: `models.py:141-155`

كل دورة لها **حالتان مستقلتان**:

| الحقل | القيم | الغرض |
|-------|-------|-------|
| `Course.status` (SQLEnum) | draft, pending, approved, rejected, published, archived | **تشغيلي** — رؤية الدورة |
| `Course.pedagogical_status` (String) | draft, pending_review, approved_local, approved_for_b2b, needs_revision | **بيداغوجي** — صلاحية التوزيع B2B |

#### 2.2 الانتقالات المسموحة

**المصدر**: `services/course_lifecycle.py:11-23`

| من | إلى | الفاحص | من يملك الصلاحية |
|----|-----|--------|-----------------|
| draft → pending_review | `_check_author` | صاحب الدورة فقط |
| pending_review → approved_local | `_check_pedagogical_lead` | pedagogical_lead في نفس المدرسة + `owner_type="school"` |
| pending_review → approved_for_b2b | `_check_pedagogical_admin_only` | pedagogical_admin **فقط** — pedagogical_lead **لا يملك** الصلاحية أبداً |
| pending_review → needs_revision | `_check_pedagogical_reviewer` | pedagogical_admin أو pedagogical_lead |
| needs_revision → pending_review | `_check_author` | صاحب الدورة فقط |
| approved_local → approved_for_b2b | `_check_pedagogical_admin_only` | pedagogical_admin فقط |
| * → archived | `_check_archival` | pedagogical_admin أو super_admin دائماً؛ صاحب الدورة إذا لم تكن `approved_for_b2b` |

**قاعدة ذهبية**: `pedagogical_lead` **لا يُمكنه أبداً** الموافقة على B2B — فقط `pedagogical_admin` (`course_lifecycle.py:55-63`)

#### 2.3 نشر/إلغاء النشر (CourseStatus)

**المصدر**: `routers/admin_courses.py`

| الإجراء | Endpoint | الحقل المتأثر | الشرط |
|---------|----------|---------------|-------|
| نشر | `POST /admin/courses/{id}/publish` (340) | `status=PUBLISHED`, `is_published=True` | عنوان + وصف + فصل واحد + درس واحد على الأقل |
| إلغاء النشر | `POST /admin/courses/{id}/unpublish` (389) | `status=DRAFT`, `is_published=False` | — |
| أرشفة | `POST /admin/courses/{id}/archive` (406) | `status=ARCHIVED`, `is_published=False` | — |
| تسليم للمراجعة | `POST /admin/courses/{id}/submit-for-review` (370) | `pedagogical_status="pending_review"` | يستخدم `can_transition_status()` |

**معايير القبول:**
- ✅ `POST /admin/courses/{id}/submit-for-review` مع `pedagogical_status=draft` → `pending_review` (200)
- ✅ `POST /admin/courses/{id}/submit-for-review` مع `pedagogical_status=pending_review` → خطأ 400
- ✅ `POST /pedagogical/courses/{id}/review` مع `action=approved_for_b2b` من pedagogical_lead → 403
- ✅ `POST /pedagogical-lead/courses/{id}/review-local` مع `action=approved_for_b2b` → خطأ (الانتقال غير مسموح)

---

### 3. الوصول إلى الدورات والمحتوى

#### 3.1 `has_course_access()` — 7 خطوات فحص

**المصدر**: `services/course_access.py:21-106`

```python
def has_course_access(user, course, db) -> bool:
    # 1. دورة مجانية (price None أو 0) → True
    # 2. المستخدم هو صاحب الدورة → True
    # 3. تسجيل نشط (CourseEnrollment.status == "active") → True
    # 4. شراء فردي (CoursePurchase موجود) → True
    # 5. وصول مدرسة (SchoolCourseAccess.is_active == True) → True
    # 6. باقة فردية نشطة (purchaser_type=student, niveau يطابق، pack نشط) → True
    # 7. باقة مدرسية نشطة (purchaser_type=school, مستوى الطالب يطابق، pack نشط) → True
    # وإلا → False
```

**تفاصيل فحص الباقة** (`course_access.py:109-122`):
- `course.niveau_scolaire` يجب أن يطابق `pack.niveau_scolaire`
- إذا `pack.matieres` = null → جميع المغطاة
- وإلا → `course.category` يجب أن يكون في `pack.matieres`

#### 3.2 حالة تغيير مستوى الطالب

**المصدر**: `course_access.py:67-85` + `course_access.py:87-104`

- الفحص يعتمد على `user.niveau_scolaire`
- إذا تغير مستوى الطالب → `StudyPack.niveau_scolaire == user.niveau_scolaire` لا يطابق بعد الآن
- **النتيجة**: الطالب **يفقد الوصول** إلى الدورات المشمولة بالباقة القديمة
- الباقة القديمة تبقى نشطة (لا تُلغى تلقائياً) لكنها لا تُعطي وصولاً

**معايير القبول:**
- ✅ طالب بمستوى `9ème de base` لديه باقة لنفس المستوى → وصول = True
- ✅ بعد تغيير مستوى الطالب إلى `1ère année secondaire` → وصول = False (الباقة لا تطابق)
- ✅ الباقة القديمة تبقى في `pack_purchases` بحالة `active` (لا حذف)

#### 3.3 حالة الانضمام لمدرسة بعد شراء باقة فردية

**المصدر**: `course_access.py:67-85`

- باقة فردية (`purchaser_type=student`) تبقى مربوطة بالطالب (`student_id`)
- **لا تأثير**: الوصول يعتمد على `user.niveau_scolaire` و `pack.niveau_scolaire`
- إذا الطالب انضم لمدرسة بنفس المستوى → باقته الفردية لا تزال تعمل
- إذا انضم لمدرسة بمستوى مختلف → باقته الفردية تفقد الفعالية (لا تطابق niveau)

**معايير القبول:**
- ✅ طالب بباقة فردية `9ème de base` ينضم لمدرسة `9ème de base` → باقته الفردية لا تزال تعمل
- ✅ إذا المدرسة لديها باقة مدرسية لنفس المستوى → كلاهما يعمل (ال학습 يأخذ الأولوية حسب الترتيب: فردي أولاً ثم مدرسي)

---

### 4. المحفظة المالية واستهلاك رصيد AI

#### 4.1 مجمعات المحفظة الخمسة

**المصدر**: `models.py:79-85` — `WalletPool` enum

| المجمع | القيمة | الصلاحية |
|--------|--------|----------|
| `TRIAL` | "trial" | تنتهي بعد N يوم (يُحدد لكل مستخدم) |
| `SCHOOL_ALLOCATED` | "school_allocated" | تنتهي مع انتهاء العقد |
| `PURCHASED` | "purchased" | لا تنتهي أبداً |
| `SUBSCRIPTION` | "subscription" | تتجدد مع كل دورة فوترة |
| `DT_PURCHASED` | "dt_purchased" | أرصدة بالدينار التونسي — دفتر المشتريات |

#### 4.2 ترتيب الاستهلاك الفعلي

**المصدر**: `wallet.py:212-217`

```python
CONSUMPTION_ORDER = [
    WalletPool.SUBSCRIPTION,      # 1. الأكثر فناءً — يتجدد لكل دورة
    WalletPool.SCHOOL_ALLOCATED,  # 2. ينتهي مع انتهاء العقد
    WalletPool.TRIAL,             # 3. ينتهي بعد N يوم
    WalletPool.PURCHASED,         # 4. لا ينتهي — يُ saving لآخر
]
```

**ملاحظة**: `DT_PURCHASED` **لا يُستخدم** لاستهلاك AI —它是 for real-money purchases only.

#### 4.3 آلية الاستهلاك

**المصدر**: `wallet.py:182-247` — `consume_credits()`

1. **قفل صف**: `SELECT ... FOR UPDATE` (`wallet.py:199-205`) — يمنع سباق التعديلات
2. **فحص الرصيد الإجمالي**: `get_total_balance()` يجب أن يكون ≥ المبلغ المطلوب
3. **استهلاك حسب الترتيب**: يبدأ من `SUBSCRIPTION` حتى يُغطّي المبلغ
4. **سجل漪isk**: إدراج `WalletTransaction` سالب لكل مجمع تم الت touched

#### 4.4 نمط AI: خصم قبل الاستدعاء، استرداد عند الفشل

**المصدر**: `routers/ai.py:122-178` (مكرر في جميع endpoints AI)

```python
# 1. فحص المعدل
check_ai_rate_limit(user_id, action_key)

# 2. تقدير التكلفة + فحص الرصيد
estimated = wallet_estimate_cost(feature, len(input))
balance = get_total_balance(db, user.id)
if balance < estimated:
    raise HTTPException(status_code=402, ...)

# 3. خصم الرصيد (قبل استدعاء AI)
debits = consume_credits(db, user.id, estimated, feature, request_id)

# 4. استدعاء AI
try:
    response = call_ai(...)
except Exception:
    # 5. استرداد عند الفشل
    for d in debits:
        add_credits(db, user.id, d["pool"], d["amount"])
    raise
```

**معايير القبول:**
- ✅ طالب برصيد 100 استدعى AI بتكلفة 10 → الرصيد = 90 بعد الاستدعاء الناجح
- ✅ إذا فشل استدعاء AI → الرصيد يعود 100 (لا خصم)
- ✅ إذا الرصيد < التكلفة المقدرة → 402 قبل أي خصم
- ✅ الاستهلاك يبدأ من `subscription` ثم `school_allocated` ثم `trial` ثم `purchased`

#### 4.5 تنبيهات الرصيد المنخفض

**المصدر**: `wallet.py:334-424`

| العتبة | الرسالة | الشرط |
|--------|--------|-------|
| 20% | "warning" | الرصيد < 20% من إجمالي الأرصدة الممنوحة (غير المنتهية) |
| 10% | "critical" | الرصيد < 10% |

- يتحقق بعد كل `consume_credits()` (`wallet.py:245`)
- لا يُرسل تنبيه مكرر (يتحقق من `metadata`是否存在)

#### 4.6 فصل صارم: محفظة AI مقابل الدفع

**المصدر**: `wallet.py` + `routers/courses.py`

| المحفظة | الاستخدام | المجمع |
|---------|----------|--------|
| AI Credits | استهلاك AI (ask/explain/quiz/generate) | `TRIAL`, `SCHOOL_ALLOCATED`, `PURCHASED`, `SUBSCRIPTION` |
| DT (Dinars) | شراء دورات، باقات، اشتراكات | `DT_PURCHASED` فقط |

- `consume_credits()` (`wallet.py:182`) تستخدم `TRIAL/SCHOOL_ALLOCATED/PURCHASED/SUBSCRIPTION`
- `debit_dt()` (`wallet.py:122`) تستخدم `DT_PURCHASED` فقط
- **لا توجد وظيفة تجمع بينهما** — كل مسار مستقل

**معايير القبول:**
- ✅ استهلاك AI لا يقلل رصيد DT
- ✅ شراء دورة لا يقلل رصيد AI credits
- ✅ `GET /balance` يعرض كلاهما منفصلين

---

### 5. الشراء والدفع

#### 5.1 شراء دورة فردية

**المصدر**: `routers/courses.py:309-404`

**التدفق خطوة بخطوة:**
1. التحقق من وجود الدورة (404 إذا غير موجودة)
2. التحقق من أن الدورة **مدفوعة** (400 إذا مجانية)
3. التحقق من عدم الشراء المسبق (400 إذا موجود)
4. فحص رصيد DT الكافي (402 إذا غير كافٍ)
5. خصم DT عبر `debit_dt(commit=False)` — التأخير
6. إنشاء سجل `Transaction` (COURSE_PURCHASE)
7. حساب العمولة: `platform_fee = price × (commission_rate / 100)`
8. حساب `teacher_revenue = price - platform_fee`
9. إنشاء `CoursePurchase` مع `amount_paid`, `platform_fee`, `teacher_revenue`
10. إنشاء `CourseEnrollment` تلقائي
11. **commit موحد** — كل شيء في `db.commit()` واحد (ذري)
12. إشعار صاحب الدورة

**معايير القبول:**
- ✅ شراء دورة بسعر 14.99 DT من رصيد 100.00 → الرصيد = 85.01
- ✅ شراء مزدوج لنفس الدورة → 400
- ✅ رصيد غير كافٍ → 402 مع تفاصيل المبلغ المطلوب والمتوفر
- ✅ فشل في أي خطوة بعد الخصم → rollback كامل (لا خصم بدون enrollment)

#### 5.2 استرداد المبالغ

**المصدر**: `routers/courses.py:455-515`

| الشرط | النتيجة |
|-------|---------|
| الدورة من `eduai_catalog` | استرداد **تلقائي** — `refunded=True` |
| الدورة من `independent_teacher` أو `school` | **مراجعة يدوية** مطلوبة — `status=pending_validation` |
| التقدم > `refund_max_progress_percent` (25% افتراضي) | **مرفوض** |

**⚠️ ملاحظة هامة**: مسار الاسترداد التلقائي (`courses.py:504-510`) يُحدّث سجل `CoursePurchase` فقط **دون** إرجاع DT للمحفظة. هذا قد يكون فجوة في التنفيذ.

**معايير القبول:**
- ✅ استرداد دورة من الكتالوج الداخلي → `refunded=True` فوراً
- ✅ استرداد دورة من أستاذ مستقل → `pending_validation`
- ✅ تقدم > 25% → 400 مرفوض

---

### 6. باقات الدراسة (StudyPack / PackPurchase)

#### 6.1 شراء باقة فردية

**المصدر**: `routers/packs.py:118-242`

**Validation chain:**
1. `role == "student"` فقط (`packs.py:129-131`)
2. الباقة موجودة و `PUBLISHED` (`packs.py:134-139`)
3. `user.niveau_scolaire == pack.niveau_scolaire` (`packs.py:142-151`)
4. لا توجد باقة نشطة بنفس المستوى (`packs.py:154-166`)
5. **المدرسة لديها باقة مدرسية لنفس المستوى** → يمنع الشراء الفردي (`packs.py:169-181`)
6. فحص DT balance (`packs.py:184-190`)
7. `debit_dt(commit=False)` → `Transaction` → `PackPurchase` → `commit` موحد

#### 6.2 شراء باقة مدرسية

**المصدر**: `routers/admin.py:2362-2475`

1. `require_school_admin_strict` — admin_school فقط
2. الباقة موجودة و `PUBLISHED`
3. المدير لديه `school_id`
4. **حجز مزدوج**: باقة نشطة لنفس `(school_id, niveau_scolaire)` → 400 مع تاريخ انتهاء الباقة الحالية (`admin.py:2392-2404`)
5. فحص DT → خصم → `PackPurchase` بـ `purchaser_type=SCHOOL`
6. يُغطي **جميع الطلاب النشطين** بنفس `niveau_scolaire` في المدرسة

#### 6.3 الوصول الديناميكي (Live Recalculation)

**المصدر**: `services/course_access.py:67-104`

- **لا توجد قائمة ثابتة** — الوصول يُحسب عند كل طلب
- `has_course_access()` تتحقق من `PackPurchase` مع `valid_until > now` و `status == "active"`
- إذا انتهت الصلاحية → `expire_pack_purchases()` (`course_access.py:125-166`) يُحدّث الحالة إلى `EXPIRED` (ساعياً كل ساعة)
- **لا يحذف الصفوف** — فقط يُحدّث الحالة (`course_access.py:127`)

**معايير القبول:**
- ✅ باقة نشطة + مستوى يطابق + صلاحية لم تنتهِ → الوصول = True
- ✅ باقة منتهية الصلاحية → الوصول = False (حتى لو `status=active` — الفحص يتحقق من `valid_until`)
- ✅ بعد انتهاء الصلاحية بساعة → `status` يتحول إلى `expired` تلقائياً

---

### 7. الإشعارات والأحداث

#### 7.1 الأحداث المُبلغ عنها فعلياً

**المصدر**: `services/notification_service.py`

| الحدث | الدالة | من يصله | الشرط |
|-------|--------|---------|-------|
| الحصول على شارة | `notify_badge_earned()` (80-87) | صاحب الشارة (رسالة مباشرة) | `check_and_award_badges()` نجح |
| اكتمال/عدم تحقيق هدف | `notify_goal_status()` (90-101) | صاحب الهدف (رسالة مباشرة) | `status == "completed"` أو `"missed"` فقط — `on_track`/`behind` لا تُبلغ |
| تسجيل طالب في دورة | `notify_enrollment()` (104-111) | الأستاذ (رسالة مباشرة) | — |
| شراء طالب لدورة | `notify_purchase()` (114-121) | صاحب الدورة (رسالة مباشرة) | — |
| رسالة عامة | `NotificationService.broadcast()` (45-62) | جميع المستخدمين/أساتذة/طلاب/مدراء | حسب `target` |

**معايير القبول:**
- ✅ شارة مكتسبة → رسالة مباشرة لصاحبها
- ✅ هدف مكتمل → إشعار. هدف `on_track` → لا إشعار
- ✅ طالب يشتري دورة → الأستاذ يحصل على رسالة

---

### 8. الأهداف والتتبع البيداغوجي

#### 8.1 الأفق الخمسة

**المصدر**: `models.py` — `GoalHorizon` enum + `goal_scheduler.py`

| الأفق | التلقائي | اليدوي | التفاصيل |
|-------|---------|--------|----------|
| يومي (`daily`) | ✅ APScheduler يومياً 00:05 (`goal_scheduler.py:139-154`) | ✅ `ensure_goals_exist()` عند تسجيل الدخول | هدف افتراضي: 2 دروس/يوم |
| أسبوعي (`weekly`) | ✅ APScheduler يومياً 00:05 | ✅ عند تسجيل الدخول | هدف افتراضي: 5 ساعات/أسبوع |
| شهري (`monthly`) | ✅ APScheduler يوم 1 الساعة 01:00 (`goal_scheduler.py:156-163`) | ✅ `POST /learner/goals/monthly` | هدف افتراضي: 10 دروس/شهر |
| فصلي (`quarterly`) | ❌ لا يوجد scheduler | ✅ `POST /pedagogical-lead/goals/quarterly` | يُعيّن لفصل كامل دفعة واحدة |
| سنوي (`annual`) | ❌ لا يوجد scheduler | ✅ `POST /learner/goals/annual` | هدف افتراضي: تغطية 80% من المنهج |

#### 8.2 قاعدة الحالة المحسوبة ديناميكياً

**المصدر**: `models.py` — `LearningGoal` (لا يوجد حقل `status`)

- `compute_goal_status()` تُحسب عند كل طلب
- لا تُخزَّن في قاعدة البيانات أبداً

#### 8.3 قاعدة Découverte

**المصدر**: `goal_scheduler.py:36-37` + `goal_scheduler.py:77`

- الطلاب في `Découverte` (بدون باقة) **لا يحصلون على أهداف مُولّدة تلقائياً**
- يمكنهم إنشاء أهداف يدوياً فقط

#### 8.4 إشعار انتهاء الأهداف

**المصدر**: `goal_scheduler.py:92-136`

- APScheduler يومياً الساعة 06:00
- يتحقق من الأهداف التي `period_end` هو اليوم أو أمس
- يحسب الحالة ويُبلغ فقط عن `completed` أو `missed`
- **يتحقق من عدم التكرار**: يبحث عن رسالة موجودة بنفس الموضوع

**معايير القبول:**
- ✅ طالب `excellence` بدون أهداف → `ensure_goals_exist()` يُنشئ أهداف يومية وأسبوعية
- ✅ طالب `Découverte` → لا أهداف مُولّدة تلقائياً
- ✅ هدف يومي منتهي + مكتمل → إشعار "completed"
- ✅ هدف يومي منتهي + غير مكتمل → إشعار "missed"
- ✅ هدف أسبوعي `on_track` → لا إشعار

---

### ملاحظات ختامية

#### ⚠️ غير مُنفَّذ (موجود في التصميم لكن ليس في الكود)
1. **واجهة الوالدين**: endpoints موجودة (`parent.py`) لكن لا توجد صفحة React مخصصة
2. **واجهة Gamification الكاملة**: الخادم موجود لكن الواجهة جزئية
3. **استرداد DT تلقائي**: مسار `eduai_catalog` يُحدّث السجل فقط دون إرجاع DT
4. **تأكيد/إلغاء إعادة التوجيه من الأستاذ**: `NotificationReorientation` يُنشئ لكن لا يوجد endpoint لتأكيد الأستاذ

#### ⚠️ اختلافات بين التصميم والتنفيذ
1. **PedagogicalStatus**: الكود يستخدم `approved_local` بدلاً من `approved_for_platform` الموجود في `LIVRABLE_COURSES.md`
2. **حزمة الاستهلاك**: التصميم يذكر `subscription → school_allocated → trial → purchased` — الكود يفعل ذلك فعلياً (`wallet.py:212-217`)

---

## Français — Spécification Fonctionnelle Complète

### 1. Gestion des Rôles et Accès (RBAC)

#### 1.1 Les Sept Rôles Définis dans le Code

**Source** : `models.py:39-47` — enum `UserRole`

| Rôle | Valeur | Portée | Création |
|------|--------|--------|----------|
| `student` | "student" | École (school_id) | Auto-inscription `POST /auth/register` — pas d'approbation requise (`auth.py:79-135`) |
| `teacher` | "teacher" | École (school_id) | 3 voies : (1) inscription trial instantanée (`auth.py:138-194`), (2) inscription + approbation admin (`admin.py:1829-1898`), (3) conversion via Stripe (`subscriptions.py:306-338`) |
| `admin_school` | "admin_school" | École (school_id) | `POST /admin/user-create` — super_admin uniquement (`admin.py:297-298`) |
| `super_admin` | "super_admin" | Globale | `POST /admin/user-create` — super_admin uniquement |
| `pedagogical_admin` | "pedagogical_admin" | Globale | `POST /admin/user-create` — super_admin uniquement |
| `pedagogical_lead` | "pedagogical_lead" | École (school_id) | `POST /admin/user-create` — super_admin uniquement |
| `parent` | "parent" | École (school_id) | Pas d'inscription publique — `POST /admin/user-create` uniquement |

#### 1.2 Séparation subscription_plan vs. rôle

**Source** : `models.py:55-59` + `deps.py:244-259`

- `SubscriptionPlan` (trial/school_affiliated/independent_paid) s'applique **uniquement aux enseignants**
- `require_active_subscription` bloque **uniquement l'écriture** (création de cours/chapitres/leçons/quizzes) quand `independent_paid` est expiré — la lecture passe toujours
- `SubscriptionTier` sur le modèle `School` (free/teacher_pro/school/institution) gère `max_users`

#### 1.3 Matrice Complète des Permissions

**Source** : `deps.py` + tous les routers

| Action | Dependency | Rôles autorisés |
|--------|-----------|-----------------|
| CRUD écoles | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| Lecture utilisateurs | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| Créer user (tout rôle) | `require_admin` + check interne | super_admin : tous (`admin.py:297`) |
| Créer user student/teacher | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead (`admin.py:299-300`) |
| Changer rôle | `require_platform_admin` | super_admin, pedagogical_admin |
| Activer/Désactiver | `require_platform_admin` | super_admin, pedagogical_admin |
| Supprimer user | `require_platform_admin` | super_admin, pedagogical_admin |
| Gérer wallets | `require_platform_admin` | super_admin, pedagogical_admin |
| Settings plateforme | `require_platform_admin` | super_admin, pedagogical_admin |
| Packages tokens | `require_platform_admin` | super_admin, pedagogical_admin |
| Clés API/coûts | `require_platform_admin` | super_admin uniquement (check interne) |
| Codes d'invitation | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| Achat pack scolaire | `require_school_admin_strict` | admin_school uniquement |
| Import CSV élèves | `require_school_admin_strict` | admin_school uniquement |
| Review pédago B2B | `require_pedagogical_admin` | pedagogical_admin uniquement |
| Review pédago local | `require_pedagogical_lead` | pedagogical_lead uniquement |
| Assigner objectifs trimestriels | `require_pedagogical_lead` | pedagogical_lead uniquement |
| Créer cours/leçons/chapitres | `require_admin` + `require_active_subscription` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| AI Factory | `require_platform_admin` | super_admin, pedagogical_admin |
| AI Tutor (ask/explain) | `get_current_user` | Tous — contrôle par crédits |
| Achat pack individuel | `require_authenticated` | student uniquement (check interne) |
| Achat cours | `get_current_user` | Tous les utilisateurs authentifiés |
| Interface parent | `require_parent` | parent uniquement |

#### 1.4 Règles Multi-Tenancy

**Source** : `db/session.py` + `deps.py:13-33`

- `set_tenant_context` injecte `WHERE school_id = :tid` automatiquement
- `super_admin` et `pedagogical_admin` contournent le filtre
- `check_school_access()` vérifie la correspondance `user.school_id == resource.school_id`

**Critères d'acceptation :**
- ✅ Un `admin_school` de l'école A ne voit PAS les données de l'école B (testé : `test_tenant_filter.py`)
- ✅ Un `parent` ne voit QUE ses enfants liés via `ParentEnfant`
- ✅ Un `student` ne voit QUE les cours de son école

---

### 2. Cycle de Vie d'un Cours

#### 2.1 Système de Statut Double

**Source** : `models.py:141-155`

| Champ | Valeurs | But |
|-------|---------|-----|
| `Course.status` | draft, pending, approved, rejected, published, archived | **Opérationnel** — visibilité |
| `Course.pedagogical_status` | draft, pending_review, approved_local, approved_for_b2b, needs_revision | **Pédagogique** — validation B2B |

#### 2.2 Transitions Autorisées

**Source** : `services/course_lifecycle.py:11-23`

| De | Vers | Vérificateur | Qui |
|----|------|-------------|-----|
| draft → pending_review | `_check_author` | Auteur du cours |
| pending_review → approved_local | `_check_pedagogical_lead` | pedagogical_lead même école + `owner_type="school"` |
| pending_review → approved_for_b2b | `_check_pedagogical_admin_only` | pedagogical_admin **uniquement** |
| pending_review → needs_revision | `_check_pedagogical_reviewer` | pedagogical_admin OU pedagogical_lead |
| needs_revision → pending_review | `_check_author` | Auteur du cours |
| approved_local → approved_for_b2b | `_check_pedagogical_admin_only` | pedagogical_admin uniquement |
| * → archived | `_check_archival` | pedagogical_admin/super_admin toujours ; auteur si ≠ approved_for_b2b |

**Règle d'or** : `pedagogical_lead` ne peut **JAMAIS** approuver pour B2B

---

### 3. Accès aux Cours et Contenu

#### 3.1 `has_course_access()` — 7 Étapes de Vérification

**Source** : `services/course_access.py:21-106`

1. Gratuit (`price None/0`) → True
2. Auteur → True
3. `CourseEnrollment` actif → True
4. `CoursePurchase` existant → True
5. `SchoolCourseAccess` actif → True
6. Pack individuel actif (niveau + matières correspondent) → True
7. Pack école actif (niveau de l'ÉLÈVE + matières correspondent) → True

#### 3.2 Cas Limite : Changement de Niveau

Si le `niveau_scolaire` de l'élève change, `StudyPack.niveau_scolaire == user.niveau_scolaire` ne correspond plus → **l'accès est perdu**. L'ancienne pack reste active (pas de suppression) mais ne donne plus accès.

#### 3.3 Cas Limite : Nouvel Élève avec Pack Individuel

Le pack individuel reste lié à l'élève (`student_id`). Si l'élève rejoint une école avec une pack scolaire pour le même niveau, **les deux fonctionnent** — `has_course_access()` vérifie d'abord le pack individuel (étape 6) avant le pack école (étape 7).

---

### 4. Wallet et Consommation de Crédits IA

#### 4.1 Les 5 Pools

**Source** : `models.py:79-85`

| Pool | Usage | Expiration |
|------|-------|-----------|
| TRIAL | Crédits d'essai | Après N jours |
| SCHOOL_ALLOCATED | Alloués par l'admin école | Fin de contrat |
| PURCHASED | Achat direct | Jamais |
| SUBSCRIPTION | Inclus dans abonnement | Chaque cycle |
| DT_PURCHASED | Argent réel (TND) | — (ledger achats) |

#### 4.2 Ordre de Consommation

**Source** : `wallet.py:212-217`

```
SUBSCRIPTION → SCHOOL_ALLOCATED → TRIAL → PURCHASED
```

`DT_PURCHASED` n'est PAS utilisé pour l'IA — seulement pour les achats.

#### 4.3 Patron AI : Débit Avant Appel, Remboursement sur Échec

**Source** : `routers/ai.py` (pattern identique à chaque endpoint)

1. Rate limit check
2. Estimation coût + vérification solde → 402 si insuffisant
3. `consume_credits()` — débit avant l'appel IA
4. Appel IA dans `try`
5. Sur exception : remboursement de chaque débit via `add_credits()`

**Critères d'acceptation :**
- ✅ Solde 100, appel IA coût 10 → solde 90 après succès
- ✅ Échec appel IA → solde retourne 100
- ✅ Solde < coût estimé → 402 avant tout débit
- ✅ Consommation commence par `subscription` puis `school_allocated` puis `trial` puis `purchased`

---

### 5. Achat et Paiement

#### 5.1 Flux Achat Cours

**Source** : `routers/courses.py:309-404`

Étape par étape : vérification existence → vérification payant → vérification doublon → vérification solde DT → débit `debit_dt(commit=False)` → création Transaction → calcul commission → création CoursePurchase → création CourseEnrollment → commit atomique → notification auteur

#### 5.2 Flux Achat Pack Individuel

**Source** : `routers/packs.py:118-242`

Validation : rôle student → pack publié → niveau correspondant → pas de pack actif pour même niveau → école n'a pas de pack pour ce niveau → solde DT → débit atomique → PackPurchase

#### 5.3 Flux Achat Pack Scolaire

**Source** : `routers/admin.py:2362-2475`

admin_school uniquement → pack publié → vérification doublon (un pack actif par tuple school+niveau) → débit → PackPurchase avec `purchaser_type=SCHOOL` → couvre automatiquement tous les élèves du niveau

---

### 6. Notifications et Événements

#### 6.1 Événements Déclenchant une Notification

**Source** : `services/notification_service.py`

| Événement | Fonction | Destinataire |
|-----------|----------|-------------|
| Badge gagné | `notify_badge_earned()` | Élève (message direct) |
| Objectif complété/manqué | `notify_goal_status()` | Élève (message direct) — seulement completed/missed |
| Inscription à un cours | `notify_enrollment()` | Enseignant (message direct) |
| Achat d'un cours | `notify_purchase()` | Auteur du cours (message direct) |
| Message broadcast | `NotificationService.broadcast()` | Public cible (tous/teachers/students/admins) |

---

### 7. Objectifs et Suivi Pédagogique

#### 7.1 Horizons Automatisés vs. Manuels

| Horizon | Automatique | Manuel |
|---------|------------|--------|
| Daily | ✅ APScheduler 00:05 + ensure_goals_exist() au login | — |
| Weekly | ✅ APScheduler 00:05 + ensure_goals_exist() au login | — |
| Monthly | ✅ APScheduler 1er du mois 01:00 | ✅ POST /learner/goals/monthly |
| Quarterly | ❌ | ✅ POST /pedagogical-lead/goals/quarterly |
| Annual | ❌ | ✅ POST /learner/goals/annual |

#### 7.2 Règle Pack Découverte

Les élèves en Découverte (sans pack actif) ne reçoivent **PAS** d'objectifs auto-générés. Ils peuvent créer des objectifs manuellement.

---

## English — Complete Functional Specification

### 1. Role Management & Access (RBAC)

#### 1.1 Seven Roles Defined in Code

**Source**: `models.py:39-47`

| Role | Value | Scope | Creation |
|------|-------|-------|----------|
| `student` | "student" | School (school_id) | Self-registration `POST /auth/register` — no admin approval (`auth.py:79-135`) |
| `teacher` | "teacher" | School (school_id) | 3 paths: (1) instant trial (`auth.py:138-194`), (2) registration + admin approval (`admin.py:1829-1898`), (3) Stripe upgrade (`subscriptions.py:306-338`) |
| `admin_school` | "admin_school" | School (school_id) | `POST /admin/user-create` — super_admin only (`admin.py:297-298`) |
| `super_admin` | "super_admin" | Global | `POST /admin/user-create` — super_admin only |
| `pedagogical_admin` | "pedagogical_admin" | Global | `POST /admin/user-create` — super_admin only |
| `pedagogical_lead` | "pedagogical_lead" | School (school_id) | `POST /admin/user-create` — super_admin only |
| `parent` | "parent" | School (school_id) | No public registration — admin creation only |

#### 1.2 subscription_plan vs. Role Separation

- `SubscriptionPlan` applies **only to teachers** — not students or admins
- `require_active_subscription` blocks **writes only** when `independent_paid` is expired — reads always pass
- `SubscriptionTier` on `School` model governs `max_users` limits

#### 1.3 Complete Permission Matrix

| Action | Dependency | Allowed Roles |
|--------|-----------|---------------|
| School CRUD | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| User read | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| Create user (any role) | `require_admin` + internal check | super_admin: all roles |
| Create user student/teacher | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| Change user role | `require_platform_admin` | super_admin, pedagogical_admin |
| Enable/disable user | `require_platform_admin` | super_admin, pedagogical_admin |
| Delete user | `require_platform_admin` | super_admin, pedagogical_admin |
| Manage wallets | `require_platform_admin` | super_admin, pedagogical_admin |
| Platform settings | `require_platform_admin` | super_admin, pedagogical_admin |
| Token packages | `require_platform_admin` | super_admin, pedagogical_admin |
| API keys/costs | `require_platform_admin` | super_admin only (internal check) |
| Invite codes | `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| School pack purchase | `require_school_admin_strict` | admin_school only |
| CSV import students | `require_school_admin_strict` | admin_school only |
| B2B pedagogical review | `require_pedagogical_admin` | pedagogical_admin only |
| Local pedagogical review | `require_pedagogical_lead` | pedagogical_lead only |
| Assign quarterly goals | `require_pedagogical_lead` | pedagogical_lead only |
| Create courses/lessons/chapters | `require_admin` + `require_active_subscription` | super_admin, admin_school, pedagogical_admin, pedagogical_lead |
| AI Factory | `require_platform_admin` | super_admin, pedagogical_admin |
| AI Tutor | `get_current_user` | All authenticated — credit-gated |
| Individual pack purchase | `require_authenticated` | student only (internal check) |
| Course purchase | `get_current_user` | All authenticated |
| Parent interface | `require_parent` | parent only |

---

### 2. Course Lifecycle

#### 2.1 Dual Status System

| Field | Values | Purpose |
|-------|--------|---------|
| `Course.status` | draft, pending, approved, rejected, published, archived | **Operational** — visibility |
| `Course.pedagogical_status` | draft, pending_review, approved_local, approved_for_b2b, needs_revision | **Pedagogical** — B2B distribution |

#### 2.2 Allowed Transitions

**Source**: `services/course_lifecycle.py:11-23`

| From | To | Checker | Who |
|------|----|---------|-----|
| draft → pending_review | `_check_author` | Course author only |
| pending_review → approved_local | `_check_pedagogical_lead` | pedagogical_lead same school + `owner_type="school"` |
| pending_review → approved_for_b2b | `_check_pedagogical_admin_only` | pedagogical_admin **ONLY** |
| pending_review → needs_revision | `_check_pedagogical_reviewer` | pedagogical_admin OR pedagogical_lead |
| needs_revision → pending_review | `_check_author` | Course author only |
| approved_local → approved_for_b2b | `_check_pedagogical_admin_only` | pedagogical_admin only |
| * → archived | `_check_archival` | pedagogical_admin/super_admin always; author if not approved_for_b2b |

**Golden rule**: `pedagogical_lead` can **NEVER** approve for B2B

---

### 3. Course Access

#### 3.1 `has_course_access()` — 7 Check Steps

**Source**: `services/course_access.py:21-106`

1. Free (`price None/0`) → True
2. Author → True
3. Active `CourseEnrollment` → True
4. `CoursePurchase` exists → True
5. Active `SchoolCourseAccess` → True
6. Individual pack active (level + subjects match) → True
7. School pack active (student's level + subjects match) → True

#### 3.2 Edge Case: Student Level Change

When `niveau_scolaire` changes, `StudyPack.niveau_scolaire == user.niveau_scolaire` no longer matches → **access is lost**. The old pack stays active but grants no access.

#### 3.3 Edge Case: New Student Joining School After Pack Purchase

Individual pack remains linked to student (`student_id`). If school has a school pack for same level, **both work** — `has_course_access()` checks individual pack (step 6) before school pack (step 7).

---

### 4. Wallet & AI Credit Consumption

#### 4.1 Five Wallet Pools

| Pool | Usage | Expiration |
|------|-------|-----------|
| TRIAL | Trial credits | After N days |
| SCHOOL_ALLOCATED | School admin allocated | Contract end |
| PURCHASED | Direct purchase | Never |
| SUBSCRIPTION | Subscription included | Each billing cycle |
| DT_PURCHASED | Real money (TND) | Purchase ledger |

#### 4.2 Consumption Order

**Source**: `wallet.py:212-217`

```
SUBSCRIPTION → SCHOOL_ALLOCATED → TRIAL → PURCHASED
```

`DT_PURCHASED` is NOT used for AI — only for real-money purchases.

#### 4.3 AI Pattern: Debit Before Call, Refund on Failure

Every AI endpoint follows: rate limit → estimate cost → 402 if insufficient → `consume_credits()` → AI call in try → refund each debit on exception.

**Acceptance criteria:**
- ✅ Balance 100, AI cost 10 → balance 90 after success
- ✅ AI failure → balance returns to 100
- ✅ Balance < estimated cost → 402 before any debit
- ✅ Consumption starts with `subscription` then `school_allocated` then `trial` then `purchased`

---

### 5. Purchase & Payment

#### 5.1 Course Purchase Flow

**Source**: `routers/courses.py:309-404`

Verify existence → verify paid → verify no duplicate → verify DT balance → `debit_dt(commit=False)` → create Transaction → calculate commission → create CoursePurchase → create CourseEnrollment → atomic commit → notify author

#### 5.2 Individual Pack Purchase Flow

**Source**: `routers/packs.py:118-242`

Role=student → pack published → level matches → no active pack for same level → school doesn't have school pack for this level → DT balance → atomic debit → PackPurchase

#### 5.3 School Pack Purchase Flow

**Source**: `routers/admin.py:2362-2475`

admin_school only → pack published → duplicate guard (one active school pack per school+niveau) → debit → PackPurchase with `purchaser_type=SCHOOL` → automatically covers all active students of matching niveau

---

### 6. Packs & Dynamic Access

#### 6.1 Live Recalculation

**Source**: `services/course_access.py:67-104`

No static list — access is computed on every request. `has_course_access()` checks `PackPurchase` with `valid_until > now` and `status == "active"`. Expired packs are detected by the hourly scheduler (`course_access.py:125-166`) which sets `status=EXPIRED` — rows are never deleted.

#### 6.2 Individual vs. School Purchase Differences

| Aspect | Individual | School |
|--------|-----------|--------|
| Buyer | Student | admin_school |
| Covers | Only the buyer | All active students of matching niveau |
| Duplicate guard | One per student per niveau | One per school per niveau |
| Blocks if school has pack | Yes (`packs.py:169-181`) | N/A (school pack is the one that blocks) |

---

### 7. Notifications & Events

#### 7.1 Events That Trigger Notifications

**Source**: `services/notification_service.py`

| Event | Function | Recipient |
|-------|----------|-----------|
| Badge earned | `notify_badge_earned()` | Student (direct message) |
| Goal completed/missed | `notify_goal_status()` | Student (direct message) — only completed/missed |
| Course enrollment | `notify_enrollment()` | Teacher (direct message) |
| Course purchase | `notify_purchase()` | Course author (direct message) |
| Broadcast | `NotificationService.broadcast()` | Target audience |

---

### 8. Goals & Pedagogical Tracking

#### 8.1 Automated vs. Manual Horizons

| Horizon | Automated | Manual |
|---------|-----------|--------|
| Daily | ✅ APScheduler 00:05 + ensure_goals_exist() at login | — |
| Weekly | ✅ APScheduler 00:05 + ensure_goals_exist() at login | — |
| Monthly | ✅ APScheduler 1st of month 01:00 | ✅ POST /learner/goals/monthly |
| Quarterly | ❌ | ✅ POST /pedagogical-lead/goals/quarterly |
| Annual | ❌ | ✅ POST /learner/goals/annual |

#### 8.2 Découverte Pack Rule

Students in Découverte (no active pack) receive **NO** auto-generated goals. They can create goals manually only.

#### 8.3 Goal Expiry Notification

**Source**: `goal_scheduler.py:92-136`

Daily at 06:00, checks goals where `period_end` is today or yesterday. Computes status, notifies only for "completed" or "missed". Deduplicates by checking for existing message with matching subject.

---

### 9. RBAC → ABAC Architecture

#### 9.1 Current RBAC State (Implemented)

| Dependency | Roles | Enforcement |
|-----------|-------|-------------|
| `require_admin` | super_admin, admin_school, pedagogical_admin, pedagogical_lead | FastAPI Dependency |
| `require_platform_admin` | super_admin, pedagogical_admin | FastAPI Dependency |
| `require_school_admin_strict` | admin_school only | FastAPI Dependency |
| `require_teacher_or_admin` | super_admin, admin_school, teacher | FastAPI Dependency |
| `require_pedagogical_admin` | pedagogical_admin only | FastAPI Dependency |
| `require_pedagogical_lead` | pedagogical_lead only (must have school_id) | FastAPI Dependency |
| `require_parent` | parent only | FastAPI Dependency |

#### 9.2 ABAC Engine (Planned)

**Source**: Design document — not yet implemented

| Policy Attribute | Values | Impact |
|-----------------|--------|--------|
| `role` | student, teacher, admin_school, super_admin, pedagogical_admin, pedagogical_lead, parent | Base permission set |
| `school` | school_id (nullable) | Tenant isolation scope |
| `subscription_tier` | free, teacher_pro, school, institution | Feature limits |
| `pack_tier` | gratuit, basique, silver, golden | Content access level |
| `time_of_day` | 00:00–23:59 | Optional time-based restrictions |
| `is_partner` | boolean | Partner teacher vs. internal teacher |
| `active_context_role` | role enum | Current active role for multi-role users |

**Decision Flow**:
1. Extract all attributes from request context
2. Evaluate each policy rule against attributes
3. Allow if ANY policy matches; deny if NONE match
4. Log decision to `audit_logs` with attribute snapshot

#### 9.3 Context Switcher (Planned)

| Feature | Detail |
|---------|--------|
| Trigger | User with multiple roles clicks "Switch role" in UI |
| Backend | `PUT /auth/switch-context` — validates role membership, updates `active_context_role` |
| Frontend | Updates `authStore.user.role` — triggers route/permission recalculation |
| Audit | Logged to `audit_logs` with `action="context_switch"` |

#### 9.4 Impersonation (Planned)

| Feature | Detail |
|---------|--------|
| Trigger | Support agent needs to troubleshoot user's issue |
| Backend | `POST /api/support/impersonate/{user_id}` — creates impersonation session |
| Limits | max_duration=30min, require_reason=true, logged to `audit_impersonations` |
| Exit | `POST /api/support/impersonate/stop` — reverts to original session |
| Audit | Full trail: impersonator, target, reason, start_time, end_time |

---

### 10. CMS Lifecycle

#### 10.1 Content Lifecycle States

| State | Owner | Description |
|-------|-------|-------------|
| `brouillon` | Author | Work in progress, not visible to others |
| `soumis` | Author | Submitted for review, locked for editing |
| `validation_ia` | System | AI auto-validation (plagiarism, coherence, completeness) |
| `validation_humaine` | Reviewer | Human reviewer checks quality |
| `publie` | System | Live and accessible to students |
| `archive` | Admin | Retired content, read-only |

#### 10.2 Transitions

| From | To | Actor | Rules |
|------|----|-------|-------|
| brouillon → soumis | Author | Must have title + description + ≥1 lesson |
| soumis → validation_ia | System | Automatic on submit |
| validation_ia → validation_humaine | System | If AI score ≥ threshold |
| validation_ia → brouillon | System | If AI score < threshold (rejection) |
| validation_humaine → publie | Reviewer | Manual approval |
| validation_humaine → brouillon | Reviewer | Revision request |
| publie → archive | Admin | Retirement |
| archive → brouillon | Admin | Reactivation (creates new version) |

#### 10.3 AI Factory Atomization (Planned)

| Endpoint | Input | Output |
|----------|-------|--------|
| `POST /api/ai-factory/generate-lesson` | topic, niveau, matiere | 1 lesson draft (text + quiz) |
| `POST /api/ai-factory/generate-quiz` | topic, difficulty, count | 1 quiz with questions |
| `POST /api/ai-factory/generate-chapter` | topic, lesson_count | Full chapter with N lessons |

Each atom is independently previewable, editable, and publishable.

---

### Notes on Implementation Gaps

#### ⚠️ Designed but Not Implemented
1. **Parent frontend pages**: Backend endpoints exist (`parent.py`) but no React page
2. **Full gamification UI**: Backend exists but frontend is partial
3. **Automatic DT refund**: `eduai_catalog` refund path updates record but doesn't credit DT back
4. **Teacher confirm/annul reorientation**: `NotificationReorientation` is created but no endpoint for teacher action
5. **ABAC Engine**: Planned but not implemented — current RBAC is sufficient for v1
6. **Context Switcher**: Planned — multi-role users currently must logout/login to switch
7. **Impersonation**: Planned — no support session mechanism exists
8. **CMS Lifecycle**: Planned — content currently uses dual-status (operational + pedagogical)
9. **AI Factory Atomization**: Planned — current AI Factory is monolithic 4-step
10. **Versioning / Fork**: Planned — no course versioning exists
11. **Bulk Seats**: Planned — no bulk purchase mechanism
12. **Revenue Share Enhanced**: Basic commission exists; enhanced ledger planned

#### ⚠️ Discrepancies Between Design Docs and Code
1. **PedagogicalStatus**: Code uses `approved_local` instead of `approved_for_platform` from `LIVRABLE_COURSES.md`
2. **Consumption order**: Design says `subscription → school_allocated → trial → purchased` — code implements exactly this (`wallet.py:212-217`)

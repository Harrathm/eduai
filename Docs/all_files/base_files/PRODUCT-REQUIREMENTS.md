# PRODUCT-REQUIREMENTS.md — EDUAI Learning

---

## العربية — وثيقة متطلبات المنتج

### ملخص تنفيذي

EDUAI Learning هو منصة تعليمية إلكترونية متعددة المستأجرين (SaaS) مصممة للسوق التونسي. المنصة تجمع بين إدارة التعلم (LMS)، والتجارة الإلكترونية للدورات، والذكاء الاصطناعي التفاعلي، ونظام مالي موحد — في إطار واحد متكامل للتعليم المدرسي B2B.

### المشكلة والقيمة المضافة

**المشكلة الحقيقية**: المدارس التونسية تعتمد على أنظمة LMS تقليدية (Moodle, Google Classroom) لا تدعم:
- التمويل الذاتي عبر بيع الدورات بين المدارس (B2B)
- نظام مالي موحد يربط بين اشتراكات المدرسة ومحفظة الأستاذ و wallet الطالب
- التعلم التكيفي الذي يحدد مستوى الطالب تلقائياً ويكيّف المسار التعليمي
- الذكاء الاصطناعي المدمج مع بنية RAG خاصة بكل مدرسة

**القيمة المضافة المحددة** (مقارنة بـ LMS عادي):
1. **محفظة مالية موحدة بـ 5 مجمعات** (`WalletPool`): trial، school_allocated، purchased، subscription، dt_purchased — مع دفتر漪isk append-only عبر `WalletTransaction` يضمن عدم تعديل الأرصدة مباشرة
2. **نظام الباقات التعليمية** (`StudyPack`) مع صلاحية محددة وشراء عبر المحفظة — الطالب يشتري باقة حسب مستواه ثم يحصل على وصول ديناميكي للدورات المشمولة
3. **تمييز ملكية الدورات**: دورات المدرسة، دورات الأساتذة المستقلين (مع عمولة EDUAI)، والكتالوج الرسمي — مع تدقيق مزدوج للمحتوى (مدير المدرسة + المدير البيداغوجي)
4. **نظام الـ 3 قطاعات** (Découverte/Excellence/Établissement) المحسوب ديناميكياً من مشتريات الباقة — لا جداول إضافية
5. **مسار تعليمي تكيفي بـ 5 طبقات** مع آلة إعادة التوجيه التلقائية وتدقيق الأستاذ
6. **اختبار توضيحي** يحدد مستوى الطالب ويسجله تلقائياً في المسار المناسب

### الأهداف

#### أهداف ما قبل الإطلاق التجاري (Must-Have)
- ✅ إكمال واجهة الوالدين (الخادم موجود، الواجهة معدومة)
- ✅ تحسين التنقل ليتم تجميعه في 5 أقسام رئيسية بدلاً من 10 عناصر
- ✅ التحقق من عمل شراء الباقة بالكامل (خادم + واجهة + محفظة)
- ✅ التحقق من عمل الاختبار التوضيحي مع التسجيل التلقائي

#### أهداف التطور المستقبلي
- 🔶 التحقق من صلاحية التقويم التونسي (التواريخ الرسمية)
- 🔶 صفحات واجهة Gamification (الخادم موجود، الواجهة تحتاج تطوير)
- 🔶 تحسين تجربة الأستاذ المستقل (صفحة الإيرادات، إدارة الدورات)
- 🔶 تطبيق Flutter (هيكل موجود، وظائف أساسية فقط)
- ❌ نظام الإشعارات بالبريد الإلكتروني
- ❌ تطبيق Flutter كامل

### الجمهور المستهدف والأدوار

**السوق الجغرافي**: تونس (العملة: DT — الدينار التونسي، اللغة الافتراضية: فرنسية، دعم RTL للعربية)

**7 أدوار محددة في الكود** (`UserRole` enum في `models.py`):

| الدور | النطاق | الصلاحيات الفعلية |
|-------|--------|-------------------|
| `super_admin` | شامل (جميع المدارس) | إدارة كاملة: مستخدمون، مدرسة، دورات، محفظة، إعدادات المنصة، أكواد الدعوة، سجل التدقيق |
| `pedagogical_admin` | شامل (جميع المدارس) | مراجعة دورات جميع المدارس، الموافقة B2B، التقارير البيداغوجية، Escalades، AI Factory |
| `admin_school` | مدرسة واحدة (school_id) | إدارة مدرسته: مستخدمون، دورات، فصول، مالية، أساتذة، إعدادات المدرسة |
| `pedagogical_lead` | مدرسة واحدة (school_id) | الموافقة البيداغوجية على دورات المدرسة، الأهداف الدراسية، إعادة التوجيه، تتبع التكيف |
| `teacher` | مدرسة واحدة (school_id) | إنشاء دورات، إدارة الفصول، المتابعة، مراجعة المحتوى، إعادة التوجيه، AI Studio |
| `student` | مدرسة واحدة (school_id) | التعلم، الاختبارات، AI Tutor، Gamification، شراء الباقات، اختبار التوضيح |
| `parent` | مدرسة واحدة (school_id) | قراءة فقط: متابعة تقدم الأبناء (6 endpoints في الخادم، لا واجهة مخصصة) |

### الميزات حسب المجال الوظيفي

#### 1. إدارة المستخدمين والصلاحيات (RBAC + Multi-Tenancy)
| الميزة | الحالة |
|--------|--------|
| 7 أدوار مع صلاحيات محددة | ✅ مُنفَّذ ومُختبر |
| تصفية تلقائي school_id (SQLAlchemy event) | ✅ مُنفَّذ ومُختبر |
| حماية تسجيل الدخول (is_active check) | ✅ مُنفَّذ |
| حماية محاولات التسلل (5 محاولات → قفل 15 دقيقة) | ✅ مُنفَّذ ومُختبر |
| عزل البيانات بين المدارس | ✅ مُختبر (test_tenant_filter.py) |
| أكواد الدعوة للمدارس | ✅ مُنفَّذ (GET /auth/schools/join/{code}) |

#### 2. الدورات والوصول
| الميزة | الحالة |
|--------|--------|
| 3 أنواع ملكية (مدرسة/أستاذ مستقل/كتالوج EDUAI) | ✅ مُنفَّذ |
| 3 مستويات رؤية (private/school_only/public_catalog) | ✅ مُنفَّذ |
| 6 حالات نشر + 6 حالات بيداغوجية | ✅ مُنفَّذ |
| `has_course_access()` — 7 اختبارات وصول | ✅ مُنفَّذ ومُختبر (13 endpoint) |
| `purchase_course()` — خصم من المحفظة + تسجيل | ✅ مُنفَّذ ومُختبر |
| نظام العمولات (教学 30% افتراضي) | ✅ مُنفَّذ |
| استرداد المبالغ | ✅ مُنفَّذ |
| تدقيق مزدوج للمحتوى (lead + admin) | ✅ مُنفَّذ |

#### 3. المحفظة المالية (Wallet)
| الميزة | الحالة |
|--------|--------|
| 5 مجمعات ائتمان (WalletPool enum) | ✅ مُنفَّذ |
| دفتر漪isk Append-Only (WalletTransaction) | ✅ مُنفَّذ ومُختبر |
| Numeric(10,2) للدقة المالية | ✅ مُنفَّذ ومُختبر |
| `debit_dt(commit=False)` + commit موحد | ✅ مُنفَّذ ومُختبر |
| خصم حقيقي عند شراء الدورات | ✅ مُنفَّذ ومُختبر |
| تكامل Stripe للمشتراكات | ✅ مُنفَّذ |
| شراء باقات عبر المحفظة | ✅ مُنفَّذ |

#### 4. الباقات التعليمية (Study Packs)
| الميزة | الحالة |
|--------|--------|
| باقات بمستويات مدرسية مختلفة | ✅ مُنفَّذ |
| صلاحية محددة (validity_duration_days) | ✅ مُنفَّذ |
| شراء عبر المحفظة | ✅ مُنفَّذ |
| وصول ديناميكي حسب الباقة | ✅ مُنفَّذ |
| تصفية المستأجرين (pack فردي vs مدرسي) | ✅ مُنفَّذ |

#### 5. المسار التعليمي التكيفي (Adaptive Pathway)
| الميزة | الحالة |
|--------|--------|
| 5 طبقات (اكتشاف/تأسيس/تطوير/تخصص/إتقان) | ✅ مُنفَّذ |
| Arborescence: 19 مستوى مدرسي، 192 مادة | ✅ مُنفَّذ |
| Profile d'assimilation (Granularité/Chapitre) | ✅ مُنفَّذ |
| آلة إعادة التوجيه (تلقائي + تدقيق أستاذ) | ✅ مُنفَّذ |
| نشر المحتوى (Standard + Remédiation/Avancé) | ✅ مُنفَّذ |
| اختبار التوضيحي مع التسجيل التلقائي | ✅ مُنفَّذ |
| Specialités pédagogiques معRP scope | ✅ مُنفَّذ |

#### 6. الذكاء الاصطناعي
| الميزة | الحالة |
|--------|--------|
| AI Tutor (أسئلة/شروحات/تصحيح) | ✅ مُنفَّذ |
| توليد اختبارات بالذكاء الاصطناعي | ✅ مُنفَّذ |
| RAG مع FAISS + TF-IDF | ✅ مُنفَّذ |
| استيراد PDF إلى RAG | ✅ مُنفَّذ |
| AI Factory (توليد محتوى 4 خطوات) | ✅ مُنفَّذ |
| AI Studio للأساتذة | ✅ مُنفَّذ |
| 9 مزودي ذكاء اصطناعي | ✅ مُنفَّذ |

#### 7. التتبع والقياس
| الميزة | الحالة |
|--------|--------|
| أهداف بـ 5 أفقيات (يوم/أسبوع/شهر/ترimestre/سنة) | ✅ مُنفَّذ ومُختبر |
| Status محسوب ديناميكياً (jamais stocké) | ✅ مُنفَّذ |
| Scheduler (APScheduler) للأهداف اليومية والشهرية | ✅ مُنفَّذ |
|Gamification (badges/streaks/rankings) | ✅ مُنفَّذ في الخادم، 🔶 واجهة محدودة |
| سجل التدقيق (Audit Log) | ✅ مُنفَّذ |

#### 8. الاتصال
| الميزة | الحالة |
|--------|--------|
| بريد داخلي (رسائل مباشرة + broadcast) | ✅ مُنفَّذ |
| إشعارات الأهداف والbadges | ✅ مُنفَّذ |
| دعم 3 لغات (FR/EN/AR) | ✅ مُنفَّذ في الواجهة |

#### 9. Gouvernance et Évolution du Contenu
| الميزة | الحالة | التفاصيل |
|--------|--------|----------|
| **Context Switcher** — multi-rôle | ❌ مُخطَّط | المستخدمون ذوو الأدوار المتعددة يمكنهم التبديل بين الأدوار بدون تسجيل خروج/دخول جديد. يخزّن `active_context_role` في `users` |
| **Impersonation de support** | ❌ مُخطَّط | `super_admin` و `pedagogical_admin` يمكنهم الدخول كحساب مستخدم آخر لتقديم الدعم — يُسجَّل في `audit_impersonations` مع سبب + مدة + تسجيل خروج تلقائي |
| **ABAC Engine** | ❌ مُخطَّط | ترقية من RBAC ثابت إلى ABAC ديناميكي — politiques تعتمد على السياق (`school`, `subscription_tier`, `pack_tier`, `time_of_day`) بدلاً من الأدوار فقط |
| **AI Factory Atomization** | ❌ مُخطَّط | كسر AI Factory إلى ذرّات: `generate-lesson` (درس واحد)، `generate-quiz` (اختبار واحد)، `generate-chapter` (فصل كامل). كل ذرّة تنتج عنصرًا قابلاً للمعاينة والنشر |
| **Versioning / Fork de Cursus** | ❌ مُخطَّط | إنشاء نسخة جديدة من دورة (`version_number`) مع `is_active_version`. Fork يحفظ الأصل كمرجع |
| **Bulk Seats** | ❌ مُخطَّط | شراء مقاعد متعددة دفعة واحدة للمدارس — `bulk_seat_vouchers` مع صلاحية + استخدام |
| **Revenue Share Enhanced** | ❌ مُخطَّط | حساب تلقائي للإيرادات: عائد الأستاذ × نسب الشراكة — `teacher_revenue_ledger` |
| **CMS Lifecycle** | ❌ مُخطَّط | دورة حياة محتوى تعليمي: Brouillon → Soumission → Validation IA → Validation Humaine → Publication → Archivage. مع ختم زمني وتنبيهات تلقائية |

### مقاييس النجاح

#### مقاييس قابلة للقياس حالياً (البيانات متوفرة في الكود)
1. **معدل التحويل**: عدد المستخدمين الذين يشترون باقة / عدد المسجلين — بيانات متوفرة عبر `PackPurchase` + `User`
2. **الإيرادات**: إجمالي DT المدفوعة عبر `WalletTransaction.amount` (pool=purchased)
3. **هامش الربح من AI**: `WalletTransaction` (source=ai_consumption) مقابل تكلفة API — بيانات متوفرة في `admin/analytics`
4. **معدل إتمام الدورات**: عدد `LessonProgress` المكتملة / عدد الدورات المسجلة
5. **معدل استخدام AI**: عدد طلبات `/ai/ask` + `/ai/explain` + `/ai/quiz` — متوفر عبر `AIConversation`
6. **معدل احتفاظ الأساتذة**: عدد الأساتذة النشطين / إجمالي المسجلين

#### مقاييس تتطلب إضافة تتبع غير متوفر حالياً
- **معدل رضا المستخدمين**: NPS أو CSAT — لا يوجد استبيان في الكود
- **الوقت المتوسط لإتمام الدورة**: يحتاج تتبع زمني لكل درس
- **معدل التحويل من Découverte إلى Excellence**: يحتاج تتبع تغيير Tier

### ما هو خارج النطاق (v1)

- ❌ تطبيق Flutter كامل (هيكل أساسي فقط)
- ❌ نظام إشعارات بالبريد الإلكتروني أو Push
- ❌ تكامل مع أنظمة إدارة التعلم الخارجية (LTI)
- ❌ تقارير تحليلية متقدمة (BI dashboard)
- ❌ نظام تقييم الأساتذة
- ❌ التكامل مع بوابات الدفع المحلية التونسية (FDL, etc.)
- ❌ تطبيق offline
- ❌ نظام اشتراكات متعدد المستويات (pricing tiers مفصل)

### معلومات غير موجودة في المستودع (تتطلب إكمال من فريق المنتج)

- **نموذج التسعير الفعلي**: أسعار الباقات والاشتراكات الحقيقية (موجود في الكود كـ defaults فقط)
- **السوق المستهدف بدقة**: هل المدارس الحكومية فقط؟ الخاصة؟ كلاهما؟
- **الم竞争对手**: Moodle، Google Classroom، أو منصات محلية
- **خطة الإطلاق**: MVP في مدرسة واحدة؟ عدة مدارس؟
- **SLA ومستوى الخدمة المطلوب**
- **نظام الدعم الفني**

---

## Français — Document de Spécifications Produit

### Résumé Exécutif

EDUAI Learning est une plateforme éducative SaaS multi-tenants conçue pour le marché tunisien. Elle combine LMS, marketplace de cours, IA tutorielle et portefeuille financier unifié dans une solution intégrée pour l'enseignement scolaire B2B.

### Problème et Proposition de Valeur

**Problème réel** : Les écoles tunisiennes utilisent des LMS traditionnels (Moodle, Google Classroom) qui ne supportent pas :
- La monétisation croisée entre écoles (B2B)
- Un système financier unifiant abonnement école + wallet enseignant + wallet élève
- L'apprentissage adaptatif avec détection automatique du niveau
- L'IA intégrée avec RAG par école

**Valeur ajoutée concrète** (vs. un LMS générique) :
1. **Portefeuille unifié à 5 pools** (`WalletPool`) : trial, school_allocated, purchased, subscription, dt_purchased — avec ledger append-only via `WalletTransaction`
2. **Système de packs d'étude** (`StudyPack`) avec durée de validité et achat via portefeuille
3. **Propriété distinte des cours** : école, enseignant indépendant (commission EDUAI), catalogue officiel
4. **Système à 3 paliers** (Découverte/Excellence/Établissement) calculé dynamiquement depuis les achats de packs
5. **Parcours adaptatif à 5 couches** avec machine de réorientation automatique
6. **Test de positionnement** avec auto-enrollment

### Objectifs

#### Must-have avant lancement commercial
- ✅ Finaliser l'interface parent (backend existant, frontend absent)
- ✅ Regrouper la navigation en 5 sections principales
- ✅ Vérifier le flux complet d'achat de pack (backend + frontend + wallet)
- ✅ Vérifier le fonctionnement du test de positionnement avec auto-enrollment

#### Évolutions futures
- 🔶 Valider le calendrier scolaire tunisien (dates officielles)
- 🔶 Pages Gamification (backend existant, frontend à développer)
- 🔶 Améliorer l'expérience enseignant indépendant
- 🔶 Application Flutter complète
- ❌ Système de notifications email
- ❌ Intégration LTI

### Public Cible et Rôles

**Marché géographique** : Tunisie (devise : DT, langue par défaut : français, RTL pour l'arabe)

**7 rôles définis dans le code** (`UserRole` enum) :

| Rôle | Portée | Permissions réelles |
|------|--------|---------------------|
| `super_admin` | Globale | Gestion complète : users, schools, cours, wallet, settings, invite codes, audit logs |
| `pedagogical_admin` | Globale | Révision cours toutes écoles, approbation B2B, rapports pédagogiques, escalades, AI Factory |
| `admin_school` | École | Gestion complète de son école : users, cours, classes, finances, teachers, settings |
| `pedagogical_lead` | École | Validation cours école, objectifs pédagogiques, réorientations, suivi adaptatif |
| `teacher` | École | Création cours, gestion classes, suivi élèves, révision contenu, AI Studio |
| `student` | École | Apprentissage, quizzes, AI tutor, gamification, achats packs, test positionnement |
| `parent` | École | Lecture seule : progression enfants (6 endpoints backend, pas de frontend dédié) |

### Fonctionnalités par Domaine (avec statut)

#### 1. Gestion Utilisateurs & RBAC
| Fonctionnalité | Statut |
|----------------|--------|
| 7 rôles avec permissions précises | ✅ Implémenté et testé |
| Filtrage automatique school_id | ✅ Implémenté et testé |
| Protection login (is_active) | ✅ Implémenté |
| Account lockout (5 tentatives) | ✅ Implémenté et testé |
| Isolation cross-school | ✅ Testé |
| Codes d'invitation école | ✅ Implémenté |

#### 2. Cours & Accès
| Fonctionnalité | Statut |
|----------------|--------|
| 3 types de propriété cours | ✅ Implémenté |
| 3 niveaux de visibilité | ✅ Implémenté |
| 6 statuts publication + 6 statuts pédagogiques | ✅ Implémenté |
| `has_course_access()` — 7 vérifications | ✅ Implémenté et testé (13 endpoints) |
| `purchase_course()` — débit wallet | ✅ Implémenté et testé |
| Système de commission (30% défaut) | ✅ Implémenté |
| Remboursement | ✅ Implémenté |
| Double validation contenu | ✅ Implémenté |

#### 3. Portefeuille Financier
| Fonctionnalité | Statut |
|----------------|--------|
| 5 pools de crédit | ✅ Implémenté |
| Ledger append-only | ✅ Implémenté et testé |
| Numeric(10,2) précision | ✅ Implémenté et testé |
| `debit_dt(commit=False)` atomique | ✅ Implémenté et testé |
| Débit réel à l'achat cours | ✅ Implémenté et testé |
| Intégration Stripe subscriptions | ✅ Implémenté |
| Achat packs via wallet | ✅ Implémenté |

#### 4. Packs d'Étude
| Fonctionnalité | Statut |
|----------------|--------|
| Packs par niveau scolaire | ✅ Implémenté |
| Durée de validité | ✅ Implémenté |
| Achat via portefeuille | ✅ Implémenté |
| Accès dynamique par pack | ✅ Implémenté |
| Filtrage tenant (individuel vs école) | ✅ Implémenté |

#### 5. Parcours Adaptatif
| Fonctionnalité | Statut |
|----------------|--------|
| 5 couches (Découverte → Maîtrise) | ✅ Implémenté |
| Arborescence (19 niveaux, 192 matières) | ✅ Implémenté |
| Profil d'assimilation (chapitre) | ✅ Implémenté |
| Machine de réorientation | ✅ Implémenté |
| Publication (Standard + Remédiation/Avancé) | ✅ Implémenté |
| Test de positionnement + auto-enroll | ✅ Implémenté |
| Spécialités pédagogiques + RP scope | ✅ Implémenté |

#### 6. Intelligence Artificielle
| Fonctionnalité | Statut |
|----------------|--------|
| AI Tutor (ask/explain/correct) | ✅ Implémenté |
| Génération quiz IA | ✅ Implémenté |
| RAG (FAISS + TF-IDF) | ✅ Implémenté |
| Ingestion PDF vers RAG | ✅ Implémenté |
| AI Factory (4 étapes) | ✅ Implémenté |
| AI Studio enseignant | ✅ Implémenté |
| 9 providers IA supportés | ✅ Implémenté |

#### 7. Suivi & Mesure
| Fonctionnalité | Statut |
|----------------|--------|
| Objectifs 5 horizons | ✅ Implémenté et testé |
| Status toujours recalculé | ✅ Implémenté |
| Scheduler APScheduler | ✅ Implémenté |
| Gamification (badges/streaks) | ✅ Backend / 🔶 Frontend partiel |
| Audit log | ✅ Implémenté |

#### 8. Communication
| Fonctionnalité | Statut |
|----------------|--------|
| Messagerie interne (direct + broadcast) | ✅ Implémenté |
| Notifications objectifs/badges | ✅ Implémenté |
| Support 3 langues (FR/EN/AR) | ✅ Implémenté |

#### 9. Gouvernance et Évolution du Contenu
| Fonctionnalité | Statut | Détails |
|----------------|--------|---------|
| **Context Switcher** — multi-rôle | ❌ Planned | Utilisateurs multi-rôles basculent entre rôles sans reconnexion. `active_context_role` dans `users` |
| **Impersonation de support** | ❌ Planned | `super_admin`/`pedagogical_admin` entrent dans un compte utilisateur — journal `audit_impersonations` |
| **ABAC Engine** | ❌ Planned | RBAC fixe → ABAC dynamique basé sur le contexte (école, tier, pack, heure) |
| **AI Factory Atomization** | ❌ Planned | AI Factory en atomes: `generate-lesson`, `generate-quiz`, `generate-chapter` indépendants |
| **Versioning / Fork de Cours** | ❌ Planned | `version_number` + `is_active_version` — fork avec historique |
| **Bulk Seats** | ❌ Planned | Achat groupé de places pour écoles — `bulk_seat_vouchers` |
| **Revenue Share Enhanced** | ❌ Planned | Calcul automatique revenu enseignant — `teacher_revenue_ledger` |
| **CMS Lifecycle** | ❌ Planned | Brouillon → Soumission → Validation IA → Validation Humaine → Publication → Archivage |

### Métriques de Succès

#### Mesurables avec les données actuelles
1. **Taux de conversion** : users achetant une pack / inscrits — données via `PackPurchase` + `User`
2. **Revenus** : total DT payés via `WalletTransaction.amount` (pool=purchased)
3. **Marge IA** : `WalletTransaction` (source=ai_consumption) vs coût API — via `admin/analytics`
4. **Taux de complétion cours** : `LessonProgress` complétés / inscriptions
5. **Taux d'utilisation AI** : requêtes `/ai/ask` + `/ai/explain` + `/ai/quiz`
6. **Rétention enseignants** : enseignants actifs / total inscrits

#### Nécessitant ajout de tracking
- **Taux de satisfaction utilisateur** (NPS/CSAT) — pas de survey dans le code
- **Temps moyen de complétion d'un cours** — besoin de tracking temporel par leçon
- **Taux de conversion Découverte → Excellence** — besoin de tracking changement Tier

### Hors Périmètre (v1)

- ❌ Application Flutter complète
- ❌ Notifications email/push
- ❌ Intégration LTI
- ❌ Dashboard BI avancé
- ❌ Système d'évaluation des enseignants
- ❌ Passerelles de paiement locales tunisiennes
- ❌ Application offline
- ❌ Système d'abonnement multi-niveaux détaillé

### Informations non trouvées dans le repo (à compléter par l'équipe produit)

- **Modèle de tarification réel** : prix des packs et abonnements (defaults dans le code uniquement)
- **Marché cible précis** : écoles publiques ? privées ? les deux ?
- **Concurrents** : Moodle, Google Classroom, ou plateformes locales
- **Plan de lancement** : MVP dans une école ? plusieurs ?
- **SLA requis**
- **Système de support client**

---

## English — Product Requirements Document

### Executive Summary

EDUAI Learning is a multi-tenant SaaS educational platform designed for the Tunisian market. It combines LMS, course marketplace, AI tutoring, and a unified financial wallet into an integrated solution for B2B school education.

### Problem & Value Proposition

**Real problem**: Tunisian schools use traditional LMS (Moodle, Google Classroom) that don't support:
- Cross-school monetization (B2B)
- Unified financial system combining school subscriptions + teacher wallet + student wallet
- Adaptive learning with automatic level detection
- Integrated AI with per-school RAG

**Specific value proposition** (vs. generic LMS):
1. **Unified wallet with 5 pools** (`WalletPool`): trial, school_allocated, purchased, subscription, dt_purchased — with append-only ledger via `WalletTransaction`
2. **Study pack system** (`StudyPack`) with validity period and wallet-based purchase
3. **Distinct course ownership**: school courses, independent teacher courses (with EDUAI commission), official catalog
4. **3-tier system** (Découverte/Excellence/Établissement) dynamically computed from pack purchases
5. **5-layer adaptive pathway** with automatic reorientation machine
6. **Placement test** with auto-enrollment

### Goals

#### Must-have before commercial launch
- ✅ Complete parent interface (backend exists, frontend missing)
- ✅ Consolidate navigation into 5 main sections
- ✅ Verify full pack purchase flow (backend + frontend + wallet)
- ✅ Verify placement test with auto-enrollment works end-to-end

#### Future evolution
- 🔶 Validate Tunisian school calendar (official dates)
- 🔶 Gamification pages (backend exists, frontend to develop)
- 🔶 Improve independent teacher experience
- 🔶 Complete Flutter application
- ❌ Email notification system
- ❌ LTI integration

### Target Audience & Roles

**Geographic market**: Tunisia (currency: DT, default language: French, RTL for Arabic)

**7 roles defined in code** (`UserRole` enum):

| Role | Scope | Actual permissions |
|------|-------|-------------------|
| `super_admin` | Global | Full management: users, schools, courses, wallet, platform settings, invite codes, audit logs |
| `pedagogical_admin` | Global | Course review across schools, B2B approval, pedagogical reports, escalades, AI Factory |
| `admin_school` | School | Full school management: users, courses, classes, finances, teachers, settings |
| `pedagogical_lead` | School | Pedagogical course approval, learning goals, reorientations, adaptive tracking |
| `teacher` | School | Course creation, class management, student tracking, content review, AI Studio |
| `student` | School | Learning, quizzes, AI tutor, gamification, pack purchases, placement test |
| `parent` | School | Read-only: children's progress (6 backend endpoints, no dedicated frontend) |

### Features by Domain (with Status)

#### 1. User Management & RBAC
| Feature | Status |
|---------|--------|
| 7 roles with precise permissions | ✅ Implemented and tested |
| Automatic school_id filtering | ✅ Implemented and tested |
| Login protection (is_active check) | ✅ Implemented |
| Account lockout (5 attempts) | ✅ Implemented and tested |
| Cross-school isolation | ✅ Tested |
| School invite codes | ✅ Implemented |

#### 2. Courses & Access
| Feature | Status |
|---------|--------|
| 3 course ownership types | ✅ Implemented |
| 3 visibility levels | ✅ Implemented |
| 6 publication + 6 pedagogical statuses | ✅ Implemented |
| `has_course_access()` — 7 access checks | ✅ Implemented and tested (13 endpoints) |
| `purchase_course()` — wallet debit | ✅ Implemented and tested |
| Commission system (30% default) | ✅ Implemented |
| Refund support | ✅ Implemented |
| Double content validation | ✅ Implemented |

#### 3. Financial Wallet
| Feature | Status |
|---------|--------|
| 5 credit pools | ✅ Implemented |
| Append-only ledger | ✅ Implemented and tested |
| Numeric(10,2) precision | ✅ Implemented and tested |
| `debit_dt(commit=False)` atomic | ✅ Implemented and tested |
| Real debit on course purchase | ✅ Implemented and tested |
| Stripe subscription integration | ✅ Implemented |
| Pack purchase via wallet | ✅ Implemented |

#### 4. Study Packs
| Feature | Status |
|---------|--------|
| Packs by school level | ✅ Implemented |
| Validity duration | ✅ Implemented |
| Wallet-based purchase | ✅ Implemented |
| Dynamic access by pack | ✅ Implemented |
| Tenant filtering (individual vs school) | ✅ Implemented |

#### 5. Adaptive Pathway
| Feature | Status |
|---------|--------|
| 5 tiers (Discovery → Mastery) | ✅ Implemented |
| Arborescence (19 levels, 192 subjects) | ✅ Implemented |
| Assimilation profile (per chapter) | ✅ Implemented |
| Reorientation machine | ✅ Implemented |
| Content publication rules | ✅ Implemented |
| Placement test + auto-enroll | ✅ Implemented |
| Pedagogical specialties + RP scope | ✅ Implemented |

#### 6. Artificial Intelligence
| Feature | Status |
|---------|--------|
| AI Tutor (ask/explain/correct) | ✅ Implemented |
| AI quiz generation | ✅ Implemented |
| RAG (FAISS + TF-IDF) | ✅ Implemented |
| PDF ingestion to RAG | ✅ Implemented |
| AI Factory (4-step) | ✅ Implemented |
| Teacher AI Studio | ✅ Implemented |
| 9 AI providers supported | ✅ Implemented |

#### 7. Tracking & Measurement
| Feature | Status |
|---------|--------|
| Goals with 5 horizons | ✅ Implemented and tested |
| Status always recalculated | ✅ Implemented |
| APScheduler for goals | ✅ Implemented |
| Gamification (badges/streaks) | ✅ Backend / 🔶 Partial frontend |
| Audit log | ✅ Implemented |

#### 8. Communication
| Feature | Status |
|---------|--------|
| Internal messaging (direct + broadcast) | ✅ Implemented |
| Goal/badge notifications | ✅ Implemented |
| 3-language support (FR/EN/AR) | ✅ Implemented |

#### 9. Governance & Content Evolution
| Feature | Status | Details |
|---------|--------|---------|
| **Context Switcher** — multi-role | ❌ Planned | Multi-role users switch roles without re-login. `active_context_role` in `users` |
| **Support Impersonation** | ❌ Planned | `super_admin`/`pedagogical_admin` enter user accounts — logged in `audit_impersonations` |
| **ABAC Engine** | ❌ Planned | Static RBAC → dynamic ABAC based on context (school, tier, pack, time) |
| **AI Factory Atomization** | ❌ Planned | AI Factory split into atoms: `generate-lesson`, `generate-quiz`, `generate-chapter` |
| **Course Versioning / Fork** | ❌ Planned | `version_number` + `is_active_version` — fork with history |
| **Bulk Seats** | ❌ Planned | Schools purchase seats in bulk — `bulk_seat_vouchers` |
| **Revenue Share Enhanced** | ❌ Planned | Automatic teacher revenue calculation — `teacher_revenue_ledger` |
| **CMS Lifecycle** | ❌ Planned | Draft → Submit → AI Validation → Human Validation → Publish → Archive |

### Success Metrics

#### Measurable with current data
1. **Conversion rate**: users purchasing a pack / enrolled — data via `PackPurchase` + `User`
2. **Revenue**: total DT paid via `WalletTransaction.amount` (pool=purchased)
3. **AI margin**: `WalletTransaction` (source=ai_consumption) vs API cost — via `admin/analytics`
4. **Course completion rate**: `LessonProgress` completed / enrollments
5. **AI utilization rate**: requests to `/ai/ask` + `/ai/explain` + `/ai/quiz`
6. **Teacher retention**: active teachers / total registered

#### Requiring additional tracking
- **User satisfaction rate** (NPS/CSAT) — no survey in code
- **Average course completion time** — needs per-lesson time tracking
- **Découverte → Excellence conversion rate** — needs Tier change tracking

### Out of Scope (v1)

- ❌ Complete Flutter application
- ❌ Email/push notifications
- ❌ LTI integration
- ❌ Advanced BI dashboard
- ❌ Teacher evaluation system
- ❌ Local Tunisian payment gateways
- ❌ Offline application
- ❌ Detailed multi-tier subscription system

### Information Not Found in Repository (to be completed by product team)

- **Actual pricing model**: real pack and subscription prices (only defaults in code)
- **Precise target market**: public schools? private? both?
- **Competitors**: Moodle, Google Classroom, or local platforms
- **Launch plan**: MVP in one school? multiple?
- **Required SLA**
- **Customer support system**

# خارطة الطريق — EDUAI Learning

---

## 1. الوضع الحالي

المنصة اليوم قادرة على:
- إدارة بيئة تعليمية متعددة المدارس مع 7 أدوار صلاحيات (مشرف عام، مشرف مدرسي، مشرف تعليمي، معلم، طالب، ولي أمر)
- إنشاء وإدارة الدورات مع محتوى غني (فيديو، PDF، نص، اختبارات)
- محافظ مالية موحدة مع 5 أحواض ائتمان وسجل لا يُحذف (append-only ledger)
- دروس تكيّفية بـ 5 طبقات (من الاكتشاف إلى الإتقان) مع ملفات تعريف التعلم لكل فصل
- معلم ذكاء اصطناعي مدمج متوافق مع المنهج التونسي (شرح، تمارين، اختبارات)
- نظام روابط دراسية (packs) للوصول إلى المحتوى حسب المستوى المدرسي
- نظام تتبع الأهداف التعليمية (يومية/أسبوعية/شهرية) مع توليد تلقائي
- تلعيم (badges، سلاسل يومية، تصنيفات)
- واجهة أمامية متكاملة: 41 صفحة مشرف + 8 صفحات معلم + 13 صفحة طالب + 2 صفحة ولي أمر

**حالة التجهيز للإطلاق التجاري:** الجهة الخلفية (backend) والواجهة الأمامية (frontend) مكتملتان تقريباً. لكن هناك 3 عوائق حرجة يجب إصلاحها قبل الإطلاق:
1. **عزل البيانات بين المدارس** — بعض نقاط النهاية لا تحترم فصل المدارس (أمان حرج)
2. **بنية تحتية للهجرة** — نظام Alembic مفقود (لا يمكن نشر تحديثات آمنة)
3. **أمان المعاملات المالية** — فرصة سباق في خدمة استهلاك الأرصدة قد تسبب خسائر مالية

---

## 2. ترقيم الإصدارات

| الإصدار | الحالة | المعنى |
|---------|--------|--------|
| **v0.x** | **الحالية** (v0.1.0) | مرحلة ما قبل الإطلاق — البنية الأساسية مكتملة، الاختبارات جارية، لا يزال هناك إصلاحات حرجة |
| **v1.0** | **التالي** | الإطلاق التجاري الأول — جميع العوائق الحرة معالجة، جاهز للعملاء المدفوعين |
| **v1.x** | **لاحقاً** | تحسينات وتتوسع بعد الإطلاق — ميزات جديدة حسب طلب العملاء |
| **v2.0** | **المستقبل البعيد** | توسعات كبرى — تطبيق محمول، بوابات دفع محلية، BI متقدم |

> المبدأ: v0.x للاختبار والمتابعة، v1.0 للعملاء المدفوعين، v1.x للتحسين، v2.0 للتوسع.

---

## 3. الخطوات القادمة حسب أفق الزمن

### القريب — قبل الإطلاق التجاري

> الهدف: إصلاح العوائق الحرجة وجعل المنصة آمنة وجاهزة للعملاء.

**أمان البيانات بين المدارس**
سيتمكن كل مدرسة من رؤية بياناتها فقط — لا crossover بين المدارس. هذا شرط أساسي للثقة.
→ *التفاصيل التقنية في IMPLEMENTATION-PLAN.md — المرحلة 1*

**بنية تحتية للنشر**
سيتمكن فريق التطوير من نشر تحديثات بأمان عبر نظام هجرة موحد (Alembic). لا مزيد من التحديثات اليدوية الخطيرة.
→ *التفاصيل التقنية في IMPLEMENTATION-PLAN.md — المرحلة 0*

**أمان المعاملات المالية**
سيتم إصلاح فرصة السباق في استهلاك الأرصدة — كل عملية شراء أو خصم ستكون مضمونة النزاهة.
→ *التفاصيل التقنية في IMPLEMENTATION-PLAN.md — المرحلة 2*

---

### المتوسط — الأشهر الأولى بعد الإطلاق

> الهدف: التثبيت والتحسين وتوسيع التجربة حسب طلب العملاء.

**تغطية اختبارات شاملة**
ستتم تغطية جميع الخدمات الحرجة باختبارات آلية — gamification، إشعارات، RAG، تخطيط الأهداف. المنصة ستكون أكثر استقراراً مع كل إصدار.
→ *التفاصيل التقنية في IMPLEMENTATION-PLAN.md — المراحل 3 و 5*

**محرك ABAC ودورة حياة المحتوى**
ترقية من RBAC الثابت إلى سياسات ديناميكية تعتمد على السياق (مدرسة، طبقة اشتراك، باقة، وقت). دورة حياة المحتوى: Brouillon → Soumission → Validation IA → Validation Humaine → Publication.
→ *التفاصيل التقنية في IMPLEMENTATION-PLAN.md — المرحلة 7*

**تبديل السياق (Context Switcher)**
المستخدمون ذوو الأدوار المتعددة يمكنهم التبديل بين الأدوار بدون تسجيل خروج/دخول جديد — تجربة أكثر سلاسة.
→ *التفاصيل التقنية في IMPLEMENTATION-PLAN.md — المرحلة 7*

**دعم Impersonation**
يمكن للمشرفين الدخول كحساب مستخدم آخر لتقديم الدعم — مع تسجيل كامل في سجل التدقيق ومدة أقصى 30 دقيقة.
→ *التفاصيل التقنية في IMPLEMENTATION-PLAN.md — المرحلة 7*

**تجربة المعلم المحسّنة**
سيتمكن المعلمون من إضافة طلاب لصفوفهم مباشرة من الواجهة، وإنشاء دوراتهم بسرعة عبر صفحة مخصصة. تجربة سلسة بدلاً من الحلول البديلة الحالية.
→ *التفاصيل التقنية في IMPLEMENTATION-PLAN.md — المرحلة 4*

**تحسينات الأداء**
سيتم تسريع البحث في المستندات (TF-IDF) وتصنيف الطلاب عبر SQL مباشرة — استجابة أسرع للطلاب والمعلمين.
→ *ال-details التقنية في IMPLEMENTATION-PLAN.md — المرحلة 6*

**إدارة كلمات المرور**
سيتمكن المستخدمون من إعادة تعيين كلمة المرور عبر البريد الإلكتروني — ميزة أساسية مفقودة حالياً.
→ *غير مُحدَّد في IMPLEMENTATION-PLAN.md — ي requires قرار تقني (SMTP/SendGrid)*

---

### البعيد — الرؤية المنتجية

> الأفق: تطورات كبرى دون التزام بتواريخ محددة.

**تطبيق Flutter للهاتف**
تطبيق محمول يتيح للطلاب والمعلمين الوصول إلى المحتوى والتفاعل في أي وقت وأي مكان. الهيكل الأساسية موجودة但الميزات الأساسية غير مكتملة.

**بوابات دفع محلية (تونس)**
ربط المنصة ببوابات الدفع المحلية مثل FDL — تسهيل الدفع للعملاء التونسيين بدلاً من الاعتماد فقط على Stripe.

**لوحة BI متقدمة**
لوحة معلومات تفاعلية للمشرفين لتحليل بيانات التعلم — معدلات الإكمال، أداء الطلاب، تكاليف الذكاء الاصطناعي.

**نظام إشعارات بالبريد الإلكتروني**
إرسال إشعارات تلقائية عبر البريد (تسجيل، شراء، أهداف مكتملة) — الاتصال الأساسي مع المستخدمين.

**تقييم المعلمين**
نظام لتقييم أداء المعلمين بناءً على تفاعل الطلاب وجودة المحتوى.

**دعم متعدد اللغات بشكل أعمق**
ترجمة كاملة للواجهة إلى العربية مع دعم الكتابة من اليمين لليسار (RTL).

---

## 4. ميزات غير مُخططة بعد

> مذكورة في وثائق التصميم لكن لم تُسنَّد بعد إلى مرحلة تنفيذ.

| الميزة | المصدر | الحالة |
|--------|--------|--------|
| تطبيق Flutter للهاتف | PRODUCT-REQUIREMENTS.md | الهيكل موجود، الميزات الأساسية ناقصة — يتطلب مشروعًا منفصلاً |
| بوابات دفع محلية (FDL) | PRODUCT-REQUIREMENTS.md | خارج النطاق حاليًا — يتطلب شراكة تجارية |
| لوحة BI متقدمة | PRODUCT-REQUIREMENTS.md | خارج النطاق حاليًا |
| نظام إشعارات بالبريد الإلكتروني | PRODUCT-REQUIREMENTS.md | مفقود — يتطلب قراراً تقنياً (SMTP/SendGrid/Resend) |
| تقييم المعلمين | PRODUCT-REQUIREMENTS.md | خارج النطاق حاليًا |
| سondages NPS/CSAT | PRODUCT-REQUIREMENTS.md | غير مُنفّذ — يتطلب واجهة + خلفية + بريد |
| تتبع الوقت لكل درس | PRODUCT-REQUIREMENTS.md | غير مُنفّذ |
| تتبع تغير الطبقات (اكتشاف→تميز) | PRODUCT-REQUIREMENTS.md | غير مُنفّذ |
| دعم العمل دون اتصال | PRODUCT-REQUIREMENTS.md | خارج النطاق |

---

## 5. ما لن يتغير

> قرارات هيكلية مستقرة يمكن الاعتماد عليها للعملاء والشركاء.

**المحفظة المالية الموحدة**
سيظل فصل الأرصدة الافتراضية (trial) عن أرصدة الشراء الحقيقي (DT) — هذا التصميم يحمي المستخدمين من الخسائر غير المتوقعة ويضمن الشفافية.

**نموذج RBAC بأدوار 7**
الأدوار السبعة (مشرف عام، مشرف مدرسي، مشرف تعليمي عام، مشرف تعليمي مدرسي، معلم، طالب، ولي أمر) هي الأساس — لن تتغير. أي دور جديد سيُضاف كتوسيع لا كتغيير.

**المنهج التونسي كأساس**
المنصة مبنية حول المنهج التونسي (19 مستوى مدرسي، 192 مادة) — هذا الهيكل قابل للتوسيع لأي منهج عربي آخر لكن الأساس سيظل ثابتاً.

**السجل المالي لا يُحذف**
جميع المعاملات المالية تُسجَّل في سجل لا يتغير (append-only ledger) — هذه ضمانة للنزاهة المالية لا يمكن التخلي عنها.

**الفصل بين AI Tutor والمحتوى التعليمي**
الذكاء الاصطناعي يساعد في الفهم والتمارين لكن لا يُنشئ المحتوى الأساسي للدورة — هذا يحمي جودة المحتوى ويمنع التلوث بالبيانات غير الموثوقة.

---

> آخر تحديث: 2026-08-01

---
---

# FEUILLE DE ROUTE — EDUAI Learning

---

## 1. ÉTAT ACTUEL

La plateforme permet aujourd'hui :
- Gestion d'un environnement éducatif multi-écoles avec 7 rôles RBAC (super admin, admin école, responsable pédagogique, enseignant, élève, parent)
- Création et gestion de cours avec contenu riche (vidéo, PDF, texte, quiz)
- Portefeuille financier unifié avec 5 pools de crédit et un ledger append-only
- Parcours pédagogique adaptatif à 5 niveaux (Découverte → Maîtrise) avec profils d'assimilation par chapitre
- Tuteur IA intégré compatible avec le programme tunisien (explication, exercices, quiz)
- Système de packs d'étude pour l'accès au contenu par niveau scolaire
- Suivi d'objectifs pédagogiques (daily/weekly/monthly) avec génération automatique
- Gamification (badges, streaks quotidiens, classements)
- Frontend complet : 41 pages admin + 8 pages enseignant + 13 pages élève + 2 pages parent

**État de préparation au lancement commercial :** Le backend et le frontend sont quasiment complets. Cependant, 3 blocages critiques doivent être résolus avant le lancement :
1. **Isolation des données entre écoles** — certaines endpoints ne respectent pas la séparation des écoles (faille de sécurité critique)
2. **Infrastructure de migration** — le système Alembic est absent (impossible de déployer des mises à jour sûres)
3. **Sécurité des transactions financières** — race condition dans le service de consommation de crédits pouvant causer des pertes financières

---

## 2. NUMÉROTATION DES VERSIONS

| Version | État | Signification |
|---------|------|---------------|
| **v0.x** | **Actuelle** (v0.1.0) | Pré-lancement — socle fonctionnel complet, tests en cours, corrections critiques restantes |
| **v1.0** | **Prochain** | Lancement commercial — tous les blocages résolus, prêt pour les clients payants |
| **v1.x** | **Post-lancement** | Consolidation et améliorations — nouvelles fonctionnalités selon la demande client |
| **v2.0** | **Futur lointain** | Évolutions majeures — app mobile, paiements locaux, BI avancée |

> Principe : v0.x pour le test et le suivi, v1.0 pour les clients payants, v1.x pour l'amélioration, v2.0 pour l'expansion.

---

## 3. PROCHAINES ÉTAPES PAR HORIZON

### Court terme — avant le lancement commercial

> Objectif : résoudre les blocages critiques et rendre la plateforme sûre et prête pour les clients.

**Isolation des données entre écoles**
Chaque école ne verra que ses propres données — aucune fuite inter-écoles. C'est la condition fondamentale de la confiance.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phase 1*

**Infrastructure de déploiement**
L'équipe pourra déployer des mises à jour en toute sécurité via un système de migration unifié (Alembic). Fin des mises à jour manuelles risquées.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phase 0*

**Sécurité des transactions financières**
La race condition dans la consommation de crédits sera corrigée — chaque achat ou débit sera garanti d'être intègre.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phase 2*

---

### Moyen terme — premiers mois après le lancement

> Objectif : consolidation, amélioration et expansion selon la demande client.

**Couverture de tests complète**
Tous les services critiques seront couverts par des tests automatisés — gamification, notifications, RAG, suivi d'objectifs. La plateforme sera plus stable à chaque version.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phases 3 et 5*

**Moteur ABAC & CMS Lifecycle**
Migration du RBAC fixe vers des politiques dynamiques basées sur le contexte (école, tier, pack, heure). Cycle de vie du contenu : Brouillon → Soumission → Validation IA → Validation Humaine → Publication.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phase 7*

**Context Switcher**
Les utilisateurs multi-rôles basculent entre rôles sans reconnexion — expérience plus fluide.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phase 7*

**Impersonation de support**
Les administrateurs peuvent entrer dans un compte utilisateur pour le support — journal complet dans audit_impersonations, durée max 30min.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phase 7*

**Expérience enseignant améliorée**
Les enseignants pourront ajouter des élèves à leurs classes directement depuis l'interface, et créer leurs cours via une page dédiée. Une expérience fluide au lieu des solutions de contournement actuelles.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phase 4*

**Optimisations performances**
La recherche de documents (TF-IDF) et le classement des élèves seront accélérés — temps de réponse plus rapide pour les élèves et enseignants.
→ *Détails techniques dans IMPLEMENTATION-PLAN.md — Phase 6*

**Gestion du mot de passe oublié**
Les utilisateurs pourront réinitialiser leur mot de passe par email — fonctionnalité de base manquante actuellement.
→ *Non planifié dans IMPLEMENTATION-PLAN.md — nécessite une décision technique (SMTP/SendGrid)*

---

### Long terme — vision produit

> Horizon : évolutions majeures sans engagement de date.

**Application Flutter mobile**
Application mobile permettant aux élèves et enseignants d'accéder au contenu et d'interagir à tout moment. La structure squelette existe mais les fonctionnalités de base sont incomplètes.

**Passerelles de paiement locales (Tunisie)**
Intégration de passerailles de paiement locales comme FDL — faciliter les paiements pour les clients tunisiens au lieu de se limiter à Stripe.

**Tableau de bord BI avancé**
Dashboard interactif pour les administrateurs permettant d'analyser les données d'apprentissage — taux de complétion, performance des élèves, coûts IA.

**Système de notifications par email**
Envoi automatique d'emails de notification (inscription, achat, objectifs atteints) — le canal de communication principal avec les utilisateurs.

**Évaluation des enseignants**
Système d'évaluation de la performance des enseignants basé sur l'implication des élèves et la qualité du contenu.

**Support multilingue approfondi**
Traduction complète de l'interface en arabe avec support RTL (droite à gauche).

---

## 4. FONCTIONNALITÉS ENVISAGÉES NON ENCORE PLANIFIÉES

> Mentionnées dans les documents de conception mais pas encore assignées à une phase d'exécution.

| Fonctionnalité | Source | État |
|----------------|--------|------|
| Application Flutter mobile | PRODUCT-REQUIREMENTS.md | Squelette existant, fonctionnalités de base manquantes — nécessite un projet dédié |
| Passerailles de paiement locales (FDL) | PRODUCT-REQUIREMENTS.md | Hors périmètre actuel — nécessite partenariat commercial |
| Tableau de bord BI avancé | PRODUCT-REQUIREMENTS.md | Hors périmètre actuel |
| Système de notifications par email | PRODUCT-REQUIREMENTS.md | Absent — nécessite décision technique (SMTP/SendGrid/Resend) |
| Évaluation des enseignants | PRODUCT-REQUIREMENTS.md | Hors périmètre actuel |
| Sondages NPS/CSAT | PRODUCT-REQUIREMENTS.md | Non implémenté — nécessite UI + backend + email |
| Suivi du temps par leçon | PRODUCT-REQUIREMENTS.md | Non implémenté |
| Suivi des changements de palier | PRODUCT-REQUIREMENTS.md | Non implémenté |
| Mode hors-ligne | PRODUCT-REQUIREMENTS.md | Hors périmètre |

---

## 5. CE QUI NE CHANGERA PAS

> Décisions structurelles stables sur lesquelles les clients et partenaires peuvent compter.

**Portefeuille financier unifié avec séparation des pools**
La séparation entre crédits d'essai (trial) et crédits d'achat réels (DT) sera maintenue — ce design protège les utilisateurs contre les pertes imprévues et garantit la transparence.

**Modèle RBAC à 7 rôles**
Les 7 rôles (super admin, admin école, responsable pédagogique plateforme, responsable pédagogique école, enseignant, élève, parent) sont le fondement — ils ne changent pas. Tout nouveau rôle sera une extension, pas un remplacement.

**Programme tunisien comme base**
La plateforme est construite autour du programme tunisien (19 niveaux scolaires, 192 matières) — cette structure est extensible à tout autre programme arabe mais la base restera stable.

**Ledger financier append-only**
Toutes les transactions financières sont enregistrées dans un ledger immuable — c'est une garantie d'intégrité financière à laquelle on ne peut pas renoncer.

**Séparation IA Tutor / contenu pédagogique**
L'intelligence artificielle aide à la compréhension et aux exercices mais ne crée pas le contenu fondamental des cours — cela protège la qualité du contenu et empêche la contamination par des données non fiables.

---

> Dernière mise à jour : 2026-08-01

---
---

# ROADMAP — EDUAI Learning

---

## 1. CURRENT STATE

The platform today enables:
- Multi-school educational environment with 7 RBAC roles (super admin, school admin, pedagogical admin, pedagogical lead, teacher, student, parent)
- Course creation and management with rich content (video, PDF, text, quizzes)
- Unified financial wallet with 5 credit pools and an append-only ledger
- 5-layer adaptive learning pathway (Discovery → Mastery) with per-chapter assimilation profiles
- Built-in AI Tutor aligned with the Tunisian curriculum (explanation, exercises, quizzes)
- Study pack system for content access by school level
- Learning goal tracking (daily/weekly/monthly) with automatic generation
- Gamification (badges, daily streaks, rankings)
- Complete frontend: 41 admin pages + 8 teacher pages + 13 student pages + 2 parent pages

**Commercial launch readiness:** Backend and frontend are nearly complete. However, 3 critical blockers must be resolved before launch:
1. **School data isolation** — some endpoints don't enforce school separation (critical security flaw)
2. **Migration infrastructure** — Alembic system is missing (impossible to deploy safe updates)
3. **Financial transaction security** — race condition in the credit consumption service that could cause financial loss

---

## 2. VERSION NUMBERING

| Version | Status | Meaning |
|---------|--------|---------|
| **v0.x** | **Current** (v0.1.0) | Pre-launch — functional core complete, testing in progress, critical fixes remaining |
| **v1.0** | **Next** | Commercial launch — all blockers resolved, ready for paying customers |
| **v1.x** | **Post-launch** | Consolidation and improvements — new features based on customer demand |
| **v2.0** | **Far future** | Major evolutions — mobile app, local payments, advanced BI |

> Principle: v0.x for testing and tracking, v1.0 for paying customers, v1.x for improvement, v2.0 for expansion.

---

## 3. NEXT STEPS BY TIME HORIZON

### Short term — before commercial launch

> Objective: resolve critical blockers and make the platform safe and ready for customers.

**School data isolation**
Each school will see only its own data — no cross-school leakage. This is the fundamental condition of trust.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phase 1*

**Deployment infrastructure**
The team will be able to deploy updates safely through a unified migration system (Alembic). No more risky manual updates.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phase 0*

**Financial transaction security**
The race condition in credit consumption will be fixed — every purchase or debit will be guaranteed to be integrity-proof.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phase 2*

---

### Medium term — first months after launch

> Objective: consolidation, improvement, and expansion based on customer demand.

**Comprehensive test coverage**
All critical services will be covered by automated tests — gamification, notifications, RAG, goal tracking. The platform will be more stable with each release.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phases 3 and 5*

**ABAC Engine & CMS Lifecycle**
Migration from static RBAC to dynamic attribute-based policies (school, tier, pack, time). Content lifecycle: Draft → Submit → AI Validation → Human Validation → Publish.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phase 7*

**Context Switcher**
Multi-role users switch roles without re-login — smoother experience.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phase 7*

**Support Impersonation**
Administrators can enter user accounts for support — full audit trail in audit_impersonations, max 30min duration.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phase 7*

**Improved teacher experience**
Teachers will be able to add students to their classes directly from the interface, and create their courses through a dedicated page. A smooth experience instead of the current workarounds.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phase 4*

**Performance optimizations**
Document search (TF-IDF) and student rankings will be accelerated — faster response times for students and teachers.
→ *Technical details in IMPLEMENTATION-PLAN.md — Phase 6*

**Password reset flow**
Users will be able to reset their password via email — a basic feature currently missing.
→ *Not planned in IMPLEMENTATION-PLAN.md — requires technical decision (SMTP/SendGrid)*

---

### Long term — product vision

> Horizon: major evolutions without firm date commitments.

**Flutter mobile app**
Mobile application enabling students and teachers to access content and interact anytime, anywhere. The skeleton structure exists but core features are incomplete.

**Local payment gateways (Tunisia)**
Integration of local payment gateways like FDL — making payments easier for Tunisian customers instead of relying solely on Stripe.

**Advanced BI dashboard**
Interactive dashboard for administrators to analyze learning data — completion rates, student performance, AI costs.

**Email notification system**
Automatic email notifications (registration, purchase, completed goals) — the primary communication channel with users.

**Teacher evaluation system**
Teacher performance evaluation system based on student engagement and content quality.

**Deeper multilingual support**
Complete interface translation into Arabic with RTL (right-to-left) support.

---

## 4. UNPLANNED FEATURES

> Mentioned in design documents but not yet assigned to an execution phase.

| Feature | Source | Status |
|---------|--------|--------|
| Flutter mobile app | PRODUCT-REQUIREMENTS.md | Skeleton exists, core features missing — requires dedicated project |
| Local payment gateways (FDL) | PRODUCT-REQUIREMENTS.md | Currently out of scope — requires commercial partnership |
| Advanced BI dashboard | PRODUCT-REQUIREMENTS.md | Currently out of scope |
| Email notification system | PRODUCT-REQUIREMENTS.md | Missing — requires technical decision (SMTP/SendGrid/Resend) |
| Teacher evaluation | PRODUCT-REQUIREMENTS.md | Currently out of scope |
| NPS/CSAT surveys | PRODUCT-REQUIREMENTS.md | Not implemented — requires UI + backend + email |
| Per-lesson time tracking | PRODUCT-REQUIREMENTS.md | Not implemented |
| Tier change tracking | PRODUCT-REQUIREMENTS.md | Not implemented |
| Offline mode | PRODUCT-REQUIREMENTS.md | Out of scope |

---

## 5. STABILITY COMMITMENTS

> Structural decisions that are stable — customers and partners can rely on these.

**Unified wallet with pool separation**
The separation between trial credits and real purchase credits (DT) will be maintained — this design protects users against unexpected losses and ensures transparency.

**7-role RBAC model**
The 7 roles (super admin, school admin, platform pedagogical admin, school pedagogical lead, teacher, student, parent) are foundational — they won't change. Any new role will be an extension, not a replacement.

**Tunisian curriculum as base**
The platform is built around the Tunisian curriculum (19 school levels, 192 subjects) — this structure is extensible to any other Arab curriculum but the foundation will remain stable.

**Append-only financial ledger**
All financial transactions are recorded in an immutable ledger — this is an integrity guarantee that cannot be compromised.

**AI Tutor / pedagogical content separation**
AI assists with understanding and exercises but does not create core course content — this protects content quality and prevents contamination by unreliable data.

---

> Last updated: 2026-08-01

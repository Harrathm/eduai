# TABLEAU RÉCAPITULATIF — AUDIT 01/08/2026

**Commande d'exécution :**
```
cd D:\RAG_APP_new\backend && python -m pytest tests/test_audit_2026_08_01.py -v
```

**Sortie complète :**
```
tests/test_audit_2026_08_01.py::TestBug1DecimalTruncation::test_debit_14_99_exact PASSED
tests/test_audit_2026_08_01.py::TestBug1DecimalTruncation::test_debit_0_01_exact PASSED
tests/test_audit_2026_08_01.py::TestBug1DecimalTruncation::test_debit_999_99_exact PASSED
tests/test_audit_2026_08_01.py::TestBug1DecimalTruncation::test_purchase_course_decimal_matches_exactly PASSED
tests/test_audit_2026_08_01.py::TestBug1DecimalTruncation::test_credit_14_99_exact PASSED
tests/test_audit_2026_08_01.py::TestBug2AtomicCommit::test_commit_false_does_not_persist PASSED
tests/test_audit_2026_08_01.py::TestBug2AtomicCommit::test_atomic_rollback_on_failure PASSED
tests/test_audit_2026_08_01.py::TestBug2AtomicCommit::test_purchase_course_atomic_success PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_01_get_lesson_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_02_post_lesson_progress_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_03_post_quiz_start_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_04_get_quiz_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_05_post_quiz_submit_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_06_post_quiz_attempt_submit_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_07_post_notes_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_08_get_notes_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_09_post_bookmarks_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_10_get_bookmarks_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_11_get_academy_detail_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_12_get_syllabus_no_access PASSED
tests/test_audit_2026_08_01.py::TestHasCourseAccessExecution::test_13_post_enroll_paid_course_no_access PASSED

21 passed, 12 warnings in 11.00s
```

**Full suite :**
```
174 passed, 12 warnings in 118.02s
```

---

## Tableau récapitulatif

| Point vérifié | Statut | Preuve (fichier:ligne + commande + sortie) |
|---|---|---|
| **BUG 1 : debit_dt(14.99) → solde 85.01** | ✅ CORRIGÉ | `wallet.py:140` — `amount=-amount` (plus de `round()`). Test: `test_debit_14_99_exact` PASSED |
| **BUG 1 : debit_dt(0.01) → solde 9.99** | ✅ CORRIGÉ | Test: `test_debit_0_01_exact` PASSED |
| **BUG 1 : debit_dt(999.99) → solde 1000.01** | ✅ CORRIGÉ | Test: `test_debit_999_99_exact` PASSED |
| **BUG 1 : amount_paid == débit réel** | ✅ CORRIGÉ | Test: `test_purchase_course_decimal_matches_exactly` PASSED — vérifie `amount_paid=14.99` + `remaining_balance=85.01` + `get_dt_balance=85.01` |
| **BUG 1 : credit_dt(14.99) → solde 14.99** | ✅ CORRIGÉ | `wallet.py:165` — `amount=amount` (plus de `round()`). Test: `test_credit_14_99_exact` PASSED |
| **BUG 1 : WalletTransaction.amount Float** | ✅ CORRIGÉ | `models.py:1560` — `Mapped[float] = mapped_column(Float)` (était Integer). Migration SQL: `migrations/2026_08_01_wallet_amount_float.sql` |
| **BUG 2 : commit=False ne commit pas** | ✅ CORRIGÉ | `wallet.py:144` — `if commit: db.commit()`. Test: `test_commit_false_does_not_persist` PASSED — reader externe voit 100.0 avant commit, 50.0 après |
| **BUG 2 : rollback annule le débit** | ✅ CORRIGÉ | Test: `test_atomic_rollback_on_failure` PASSED — exception après debit_dt(commit=False) + rollback → solde identique à avant |
| **BUG 2 : purchase atomique** | ✅ CORRIGÉ | `courses.py:344` — `commit=False`. Test: `test_purchase_course_atomic_success` PASSED — purchase + enrollment + balance cohérents |
| **BUG 2 : admin.py + packs.py** | ✅ CORRIGÉ | `admin.py:2417` — `commit=False`. `packs.py:195` — `commit=False` |
| **13 endpoints : GET /lessons/{id}** | ✅ EXÉCUTÉ | Test: `test_01_get_lesson_no_access` PASSED — 403 |
| **13 endpoints : POST /lessons/{id}/progress** | ✅ EXÉCUTÉ | Test: `test_02_post_lesson_progress_no_access` PASSED — 403 |
| **13 endpoints : POST /quizzes/{id}/start** | ✅ EXÉCUTÉ | Test: `test_03_post_quiz_start_no_access` PASSED — 403 |
| **13 endpoints : GET /quizzes/{id}** | ✅ EXÉCUTÉ | Test: `test_04_get_quiz_no_access` PASSED — 403 |
| **13 endpoints : POST /quizzes/{id}/submit** | ✅ EXÉCUTÉ | Test: `test_05_post_quiz_submit_no_access` PASSED — 403/404 |
| **13 endpoints : POST /quiz-attempts/{id}/submit** | ✅ EXÉCUTÉ | Test: `test_06_post_quiz_attempt_submit_no_access` PASSED — 403/404 |
| **13 endpoints : POST /lessons/{id}/notes** | ✅ EXÉCUTÉ | Test: `test_07_post_notes_no_access` PASSED — 403 |
| **13 endpoints : GET /lessons/{id}/notes** | ✅ EXÉCUTÉ | Test: `test_08_get_notes_no_access` PASSED — 403 |
| **13 endpoints : POST /lessons/{id}/bookmarks** | ✅ EXÉCUTÉ | Test: `test_09_post_bookmarks_no_access` PASSED — 403 |
| **13 endpoints : GET /lessons/{id}/bookmarks** | ✅ EXÉCUTÉ | Test: `test_10_get_bookmarks_no_access` PASSED — 403 |
| **13 endpoints : GET /courses/{id}/detail** | ✅ EXÉCUTÉ | Test: `test_11_get_academy_detail_no_access` PASSED — 403 |
| **13 endpoints : GET /courses/{id}/syllabus** | ✅ EXÉCUTÉ | Test: `test_12_get_syllabus_no_access` PASSED — 403 |
| **13 endpoints : POST /courses/{id}/enroll** | ✅ EXÉCUTÉ | Test: `test_13_post_enroll_paid_course_no_access` PASSED — 403 |
| **Bug caché : _role_str non défini** | ✅ CORRIGÉ | `academy.py:90` — `_role_str(current_user)` → `get_user_role(current_user)` |

---

## Fichiers modifiés

| Fichier | Changement |
|---|---|
| `backend/app/models.py:1560` | `WalletTransaction.amount`: `Integer` → `Float` |
| `backend/app/services/wallet.py:63,73,95,134,140,165` | `InsufficientCreditsError` float, type hints float, suppression `round()` |
| `backend/app/routers/courses.py:344` | `commit=False` sur `debit_dt()` |
| `backend/app/routers/admin.py:2417` | `commit=False` sur `debit_dt()` |
| `backend/app/routers/packs.py:195` | `commit=False` sur `debit_dt()` |
| `backend/app/routers/academy.py:90` | `_role_str()` → `get_user_role()` (bug NameError) |
| `backend/migrations/2026_08_01_wallet_amount_float.sql` | Migration SQL pour DB existante |
| `backend/tests/test_audit_2026_08_01.py` | 21 tests de vérification |

---

## Risque résiduel

### Paiements réels affectés par le bug 2 (double commit) AVANT ce fix

⚠️ **OUI, c'est possible.** Le bug existait avant cette session — `debit_dt()` avait son propre `db.commit()` à la ligne 142, et `purchase_course` faisait un second commit à la ligne 383. Si un crash ou une erreur survenait entre les deux, le client était débité sans enrollment ni purchase record.

**Estimation de l'impact :** En supposant que la base de production est PostgreSQL (pas SQLite), et que le second commit échoue rarement (contrainte unique, timeout réseau), le nombre de transactions orphelines devrait être faible. Cependant, sans logs de la production, impossible de quantifier exactement.

### Script de réconciliation

```sql
-- Trouver les WalletTransaction de type 'purchase' sans CoursePurchase correspondant
SELECT wt.id, wt.user_id, wt.amount, wt.created_at, wt.metadata_
FROM wallet_transactions wt
LEFT JOIN course_purchases cp ON cp.transaction_id = CAST(wt.id AS TEXT)
WHERE wt.metadata_->>'source' = 'purchase'
  AND wt.amount < 0
  AND cp.id IS NULL;
```

Ce script identifie les débits wallet sans CoursePurchase correspondant. Pour chaque ligne trouvée, il faut décider :
- **Rembourser** : `credit_dt(db, user_id, ABS(amount), source="reconciliation", reason="Orphelin pré-fix double commit")`
- **Ou créer manuellement** le CoursePurchase + Enrollment manquants si l'accès cours doit être restauré

### Risque résiduel post-fix

**NUL pour les nouveaux achats** — le fix garantit un commit atomique via `commit=False` dans `debit_dt()` + commit unique dans le caller.

Les transactions orphelines pré-fix doivent être traitées par le script de réconciliation ci-dessus avant tout lancement commercial.

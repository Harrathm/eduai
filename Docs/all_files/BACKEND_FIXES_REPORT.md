# BACKEND FIXES REPORT — EDUAI Learning

**Date**: 04/08/2026
**Audit Source**: `rapport_backend_04_08_2026.md`
**Fixes Applied**: 10 (Phase 1: 4 Critical, Phase 2: 6 Important)

---

## Summary

| Phase | Fix | Severity | Status | Tests |
|-------|-----|----------|--------|-------|
| 1.1 | Password reset token leakage | CRITICAL | FIXED | 4/4 |
| 1.2 | IDOR on student scores | CRITICAL | FIXED | 3/3 |
| 1.3 | Float→Decimal monetary fields | CRITICAL | FIXED | 6/6 |
| 1.4 | .env secrets review | CRITICAL | VERIFIED | - |
| 2.1 | Rate limit /auth/forgot-password | HIGH | FIXED | 5/5 |
| 2.2 | Mask email in login logs | MEDIUM | FIXED | 7/7 |
| 2.3 | Remove `school_id or 1` fallback | MEDIUM | FIXED | 3/3 |
| 2.4 | Konnect webhook | MEDIUM | ALREADY DONE | - |
| 2.5 | Teacher profile school_id check | MEDIUM | FIXED | 2/2 |
| 2.6 | Wallet RBAC | MEDIUM | ALREADY DONE | - |
| 2.7 | Document legacy System B | LOW | DONE | - |

**Total new tests**: 30

---

## Phase 1 — Critical Fixes

### 1.1 Password Reset Token Leakage

**Risk**: Token returned in HTTP response body after password reset request.

**Before** (`auth.py:488-503`):
```python
return {"message": "Un lien de réinitialisation a été envoyé par email.", "token": token}
```

**After**:
```python
# Token removed from response — sent only via email
return {"message": "Un lien de réinitialisation a été envoyé par email."}
```

**New file**: `app/services/email_service.py` — SMTP email service (stdlib `smtplib`, sync-safe).
**Config added**: `smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_use_tls`, `email_from_address`, `email_from_name`, `frontend_reset_url` in `core/config.py`.
**Test**: `tests/test_phase_1_1_reset_token.py` (4 tests)

---

### 1.2 IDOR on Student Scores

**Risk**: Student could submit scores for another student by manipulating `eleve_id`.

**Before** (`adaptive_pathway.py:213-216`):
```python
if current_user.role not in ("teacher", "admin_school", "super_admin", "pedagogical_admin"):
    if current_user.id != eleve_id:
        raise HTTPException(status_code=403, detail="...")
```
Problem: student role short-circuits the check.

**After**:
```python
if current_user.role == "student":
    if current_user.id != eleve_id:
        raise HTTPException(status_code=403, detail="...")
elif current_user.role not in ("teacher", "admin_school", "super_admin", "pedagogical_admin"):
    raise HTTPException(status_code=403, detail="...")
```

**Test**: `tests/test_phase_1_2_idor_scores.py` (3 tests)

---

### 1.3 Float→Decimal Migration

**Risk**: Floating-point arithmetic on monetary fields causes precision loss (e.g., `0.1 + 0.2 != 0.3`).

**Fields converted** (5 total):

| Model | Field | Before | After |
|-------|-------|--------|-------|
| Transaction | amount | `Float` | `Numeric(10,2)` |
| TokenPackage | price_dt | `Float` | `Numeric(10,2)` |
| Course | price_dt | `Float` | `Numeric(10,2)` |
| Plan | price | `Float` | `Numeric(10,2)` |
| AIUsageLog | cost_usd | `Float` | `Numeric(10,4)` |

**Migration**: `alembic/versions/2026_08_04_0006_float_to_numeric_monetary.py`
**Test**: `tests/test_phase_1_3_decimal.py` (6 tests)

---

### 1.4 .env Secrets Review

**Findings**:
- `.env` in `.gitignore` (line 4) ✅
- `.env` never committed to git ✅
- `backend/.env.example` has all placeholders (updated with `REDIS_URL`, `ALLOWED_ORIGINS`)
- `frontend/.env.production` has only `VITE_API_URL` (public) — safe

**Action**: Updated `backend/.env.example` with missing `REDIS_URL` and `ALLOWED_ORIGINS` placeholders.

---

## Phase 2 — Important Fixes

### 2.1 Rate Limit on /auth/forgot-password

**Risk**: No rate limit on password reset endpoint — brute-force possible.

**Before** (`main.py:193`):
```python
RATE_LIMITS = {
    "/auth/login": (10, 60),
    "/auth/register": (5, 60),
    # /auth/forgot-password MISSING
}
```

**After**:
```python
RATE_LIMITS = {
    "/auth/login": (10, 60),
    "/auth/register": (5, 60),
    "/auth/forgot-password": (3, 60),  # 3 requests per minute
}
```

**Test**: `tests/test_phase_2_1_rate_limit.py` (5 tests)

---

### 2.2 Mask Email in Login Logs

**Risk**: Full email logged in plaintext — PII exposure in log files.

**Before** (`auth.py:332`):
```python
logger.warning(f"LOGIN ATTEMPT: email={form_data.username}")
```

**After**:
```python
def _mask_email(email: str) -> str:
    """Mask email for safe logging: j***@example.com."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***" if local else "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"

logger.warning(f"LOGIN ATTEMPT: email={_mask_email(form_data.username)}")
```

Also masked in `log_security_event("failed_login", ...)` and `log_security_event("account_locked", ...)`.

**Test**: `tests/test_phase_2_2_mask_email.py` (7 tests)

---

### 2.3 Remove `school_id or 1` Fallback

**Risk**: Silent fallback to school_id=1 creates orphan transactions in wrong school context.

**Before** (`packs.py:201`):
```python
transaction = Transaction(
    school_id=user.school_id or 1,  # DANGEROUS: silent fallback
)
```

**After**:
```python
if not user.school_id:
    raise HTTPException(status_code=400, detail="Aucun établissement associé à votre compte")

transaction = Transaction(
    school_id=user.school_id,
)
```

Also fixed in `courses.py:387` and `admin_courses.py:273`.

**Test**: `tests/test_phase_2_3_no_fallback_1.py` (3 tests)

---

### 2.4 Konnect Webhook

**Status**: Already fully implemented with HMAC-SHA256 verification, idempotent credit, atomic wallet update.

**File**: `app/routers/payments/konnect.py:133-197`

No fix needed.

---

### 2.5 Teacher Profile School_id Check

**Risk**: Teacher could create assimilation profiles for students in other schools.

**Before** (`adaptive_pathway.py:79-81`):
```python
if current_user.role not in ("teacher", "admin_school", ...):
    raise HTTPException(status_code=403, detail="...")
# No school scope check
```

**After**:
```python
if current_user.role not in ("teacher", "admin_school", ...):
    raise HTTPException(status_code=403, detail="...")

# School scope check for teachers
if current_user.role == "teacher" and current_user.school_id:
    student = db.query(User).filter(User.id == profil_in.eleve_id).first()
    if not student or student.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Cet élève n'appartient pas à votre établissement")
```

**Test**: `tests/test_phase_2_5_teacher_school.py` (2 tests)

---

### 2.6 Wallet RBAC

**Status**: Already in place. All wallet endpoints use `get_current_user` or `require_platform_admin`.

No fix needed.

---

### 2.7 Document Legacy System B

**Action**: Added `DEPRECATED` comments to `StudyPack`, `PackPurchase`, and `PackPurchaseStatus` models in `models.py`.

```python
# DEPRECATED — System B (StudyPack / PackPurchase)
# These models are LEGACY. The active subscription system uses
# PackDefinition + Abonnement (System A). Keep for backward compat only.
```

---

## Test Coverage

```
tests/test_phase_1_1_reset_token.py       4 passed
tests/test_phase_1_2_idor_scores.py       3 passed
tests/test_phase_1_3_decimal.py           6 passed
tests/test_phase_2_1_rate_limit.py        5 passed
tests/test_phase_2_2_mask_email.py        7 passed
tests/test_phase_2_3_no_fallback_1.py     3 passed
tests/test_phase_2_5_teacher_school.py    2 passed
-----------------------------------------------
Total new tests:                         30 passed
```

---

## Files Modified

| File | Changes |
|------|---------|
| `app/auth.py` | Token removed from reset response, `_mask_email()` helper, masked logs |
| `app/models.py` | 5 fields Float→Numeric, DEPRECATED comments on System B |
| `app/routers/adaptive_pathway.py` | IDOR fix (record_score), school_id check (create_profil) |
| `app/routers/packs.py` | `school_id or 1` → explicit 400 |
| `app/routers/courses.py` | `school_id or 1` → explicit 400 |
| `app/routers/admin_courses.py` | `school_id or 1` → explicit 400 |
| `app/main.py` | Added `/auth/forgot-password` rate limit |
| `app/services/email_service.py` | NEW — SMTP email service |
| `app/core/config.py` | SMTP settings added |
| `backend/.env.example` | Updated with SMTP, REDIS_URL, ALLOWED_ORIGINS |
| `alembic/versions/2026_08_04_0006_float_to_numeric_monetary.py` | NEW — Float→Numeric migration |

---

## Remaining Items (Not Fixable Without Business Decision)

1. **Konnect webhook for DT purchases** — currently Konnect only credits wallet; no automatic pack purchase flow. Needs business decision on user flow.
2. **Legacy System B removal** — `StudyPack`/`PackPurchase` tables still exist. Full removal requires migration + data migration. Marked as DEPRECATED.
3. **Redis distributed rate limiter** — in-memory fallback is sufficient for single-instance. Multi-instance deployment needs Redis.

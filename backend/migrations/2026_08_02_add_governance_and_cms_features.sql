-- ============================================================
-- MIGRATION: Governance & CMS Features
-- Date: 2026-08-02
-- Description: Add multi-role, context switcher, versioning,
--              ABAC targeting, bulk seats, revenue share,
--              and impersonation audit tables.
-- ============================================================

-- ============================================================
-- 1. ALTER TABLE users — Multi-role, Context Switcher, Partner
-- ============================================================

-- roles: JSON array of all user roles (e.g. ["admin_school", "pedagogical_lead"])
ALTER TABLE users ADD COLUMN roles JSONB NOT NULL DEFAULT '[]'::jsonb;

-- active_context_role: currently active role for Context Switcher
ALTER TABLE users ADD COLUMN active_context_role VARCHAR(30);

-- is_partner: activated after 1st global course validation
ALTER TABLE users ADD COLUMN is_partner BOOLEAN NOT NULL DEFAULT FALSE;


-- ============================================================
-- 2. ALTER TABLE courses — Versioning & ABAC Targeting
-- ============================================================

-- version_number: incremental version counter
ALTER TABLE courses ADD COLUMN version_number INTEGER NOT NULL DEFAULT 1;

-- is_active_version: whether this version is the published one
ALTER TABLE courses ADD COLUMN is_active_version BOOLEAN NOT NULL DEFAULT TRUE;

-- category_cible: target category (Scolaire, Soft_Skill, Teacher_Training)
ALTER TABLE courses ADD COLUMN category_cible VARCHAR(30) NOT NULL DEFAULT 'Scolaire';

-- tag_pack_requis: required pack tier for ABAC engine (Basic, Silver, Golden)
ALTER TABLE courses ADD COLUMN tag_pack_requis VARCHAR(20) NOT NULL DEFAULT 'Basic';


-- ============================================================
-- 3. CREATE TABLE bulk_seat_vouchers — B2B Bulk Seats
-- ============================================================

CREATE TABLE bulk_seat_vouchers (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    formation_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'unused',
    consumed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_bulk_seat_vouchers_school ON bulk_seat_vouchers(school_id);
CREATE INDEX ix_bulk_seat_vouchers_formation ON bulk_seat_vouchers(formation_id);
CREATE UNIQUE INDEX ix_bulk_seat_vouchers_code ON bulk_seat_vouchers(code);


-- ============================================================
-- 4. CREATE TABLE teacher_revenue_ledger — Revenue Share
-- ============================================================

CREATE TABLE teacher_revenue_ledger (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
    consumption_count INTEGER NOT NULL DEFAULT 0,
    revenue_amount NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    period_month DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_teacher_revenue_ledger_teacher ON teacher_revenue_ledger(teacher_id);
CREATE INDEX ix_teacher_revenue_ledger_lesson ON teacher_revenue_ledger(lesson_id);
CREATE INDEX ix_teacher_revenue_ledger_period ON teacher_revenue_ledger(period_month);
CREATE UNIQUE INDEX uq_teacher_lesson_period ON teacher_revenue_ledger(teacher_id, lesson_id, period_month);


-- ============================================================
-- 5. CREATE TABLE audit_impersonations — Support IT Audit
-- ============================================================

CREATE TABLE audit_impersonations (
    id SERIAL PRIMARY KEY,
    support_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45)
);

CREATE INDEX ix_audit_impersonations_support ON audit_impersonations(support_user_id);
CREATE INDEX ix_audit_impersonations_target ON audit_impersonations(target_user_id);
CREATE INDEX ix_audit_impersonations_started ON audit_impersonations(started_at);


-- ============================================================
-- BACKWARD COMPATIBILITY: Migrate existing role to roles array
-- ============================================================

UPDATE users SET roles = json_build_array(role)::jsonb WHERE roles = '[]'::jsonb;

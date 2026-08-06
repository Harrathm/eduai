-- Migration: Add type_matiere column to matieres table
-- Date: 2026-08-06
-- Description: Categorize matieres as 'langue' or 'specialite' for frontend pack purchase flow

ALTER TABLE matieres ADD COLUMN IF NOT EXISTS type_matiere VARCHAR(20) DEFAULT 'specialite';

-- Backfill: Mark common languages as 'langue'
UPDATE matieres SET type_matiere = 'langue' WHERE nom IN (
    'العربية', 'الفرنسية', 'الانقليزية', 'الإسبانية', 'الألمانية'
);

-- All other matieres remain 'specialite' (the default)

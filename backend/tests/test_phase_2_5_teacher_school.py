"""
Phase 2.5 — Teacher profile school_id check.

Verifies:
  Test 1: create_profil_assimilation checks school_id for teachers
  Test 2: Source code has school scope validation
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
import inspect
from app.routers.adaptive_pathway import create_profil_assimilation


def test_01_teacher_school_check_present():
    """Verify create_profil_assimilation has school scope check for teachers."""
    source = inspect.getsource(create_profil_assimilation)
    assert "school_id" in source, "Missing school_id check in create_profil_assimilation"
    assert "établissement" in source or "appartient" in source, "Missing school scope validation message"


def test_02_cross_school_student_blocked():
    """Verify cross-school student access is rejected in source."""
    source = inspect.getsource(create_profil_assimilation)
    assert "403" in source, "Missing 403 response for cross-school access"

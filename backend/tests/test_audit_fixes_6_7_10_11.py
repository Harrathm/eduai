"""
Tests preuve-based : Corrections #6, #7, #10, #11.

#6  Vérification email non bloquante :
    - /auth/register renvoie email_verification_token et le persiste ;
    - POST /auth/verify-email consomme le token (single-use) ;
    - le compte reste actif/loggable AVANT vérification.
#7  POST /api/admin/users crédite 100 DT TRIAL (30 j) pour les élèves créés
    par un admin (alignement sur l'auto-inscription) ; autres rôles : rien.
#10 learner.update_lesson_progress : COMMIT UNIQUE en fin de fonction
    (progression + pourcentage + certificat atomiques).
#11 Numéro de certificat haute entropie + colonne unique ET indexée.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import inspect
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import (
    User, School, Course, Module, Lesson,
    Certificate, WalletTransaction, WalletPool,
)
from app.core.security import get_password_hash
from app.routers.learner import update_lesson_progress

from tests.conftest import TEST_PASSWORD

STRONG_PASSWORD = "Str0ng!Passw0rd"


@pytest.fixture(scope="function")
def fx_db(_base_session):
    db = _base_session

    school = School(name="Ecole Audit", slug="ecole-audit")
    db.add(school)
    db.commit()
    db.refresh(school)

    def mk(email, role, niveau=None):
        u = User(
            email=email, hashed_password=get_password_hash(TEST_PASSWORD),
            full_name=email.split("@")[0], role=role, is_active=True,
            is_approved=True, school_id=school.id, niveau_scolaire=niveau,
        )
        db.add(u)
        return u

    teacher = mk("audit_teacher@test.com", "teacher")
    super_admin = mk("audit_admin@test.com", "super_admin")
    s1 = mk("audit_s1@test.com", "student", niveau="9eme de base")
    s2 = mk("audit_s2@test.com", "student", niveau="9eme de base")
    db.commit()
    for u in (teacher, super_admin, s1, s2):
        db.refresh(u)

    def make_course(slug):
        c = Course(
            title=f"Course {slug}", slug=slug,
            school_id=school.id, author_id=teacher.id,
            price=0, price_dt=0, price_tokens=0,
            visibility="public_catalog",
            status="published", is_published=True,
            niveau_scolaire="9eme de base",
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        m1 = Module(title="M1", course_id=c.id, order=1)
        m2 = Module(title="M2", course_id=c.id, order=2)
        db.add_all([m1, m2])
        db.commit()
        db.refresh(m1)
        db.refresh(m2)
        lessons = []
        for i, mid in enumerate((m1.id, m2.id), start=1):
            les = Lesson(
                title=f"L{i}", module_id=mid, order=i,
                is_free=True, lesson_type="text",
                content_html="<p>x</p>", school_id=school.id,
            )
            db.add(les)
            db.commit()
            db.refresh(les)
            lessons.append(les)
        return c, lessons

    course_a, lessons_a = make_course("audit-course-a")
    course_b, lessons_b = make_course("audit-course-b")

    yield {
        "db": db, "school": school,
        "teacher": teacher, "super_admin": super_admin,
        "s1": s1, "s2": s2,
        "course_a": course_a, "lessons_a": lessons_a,
        "course_b": course_b, "lessons_b": lessons_b,
    }


@pytest.fixture(scope="function")
def client(fx_db):
    return TestClient(app)


def _login_headers(client, email):
    resp = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _complete(client, headers, lesson_id):
    return client.post(
        f"/api/learner/lessons/{lesson_id}/progress",
        json={"status": "completed"},
        headers=headers,
    )


# -------------------------------------------------------------------
# #10 — Atomicité du endpoint progression
# -------------------------------------------------------------------
class TestSingleCommit:
    def test_exactly_one_commit_and_flush_present(self):
        src = inspect.getsource(update_lesson_progress)
        assert src.count("db.commit()") == 1
        assert "db.flush()" in src
        # le commit unique est la DERNIÈRE opération avant le return
        assert src.rstrip().endswith('return {"success": True, "progress_percent": progress_percent}')
        assert src.index("db.commit()") > src.index("Certificate(")

    def test_progress_percent_and_certificate_persisted_together(self, client, fx_db):
        headers = _login_headers(client, fx_db["s1"].email)
        lessons = fx_db["lessons_a"]
        assert _complete(client, headers, lessons[0].id).status_code == 200
        resp = _complete(client, headers, lessons[1].id)
        assert resp.status_code == 200, resp.text
        assert resp.json()["progress_percent"] == 100

        db = fx_db["db"]
        cert = db.query(Certificate).filter(Certificate.course_id == fx_db["course_a"].id).first()
        assert cert is not None


# -------------------------------------------------------------------
# #11 — Numéro de certificat : entropie + unicité + index
# -------------------------------------------------------------------
class TestCertificateNumber:
    def test_model_column_unique_and_indexed(self):
        col = Certificate.__table__.c.certificate_number
        assert col.unique is True
        assert col.index is True

    def test_unique_index_created_in_db(self, fx_db):
        engine = sa_inspect(fx_db["db"].get_bind())
        idx = [i for i in engine.get_indexes("certificates")
               if i["column_names"] == ["certificate_number"]]
        assert idx, "aucun index sur certificates.certificate_number"

    def test_format_and_uniqueness_across_students(self, client, fx_db):
        h1 = _login_headers(client, fx_db["s1"].email)
        h2 = _login_headers(client, fx_db["s2"].email)
        for les in fx_db["lessons_a"]:
            assert _complete(client, h1, les.id).status_code == 200
        for les in fx_db["lessons_b"]:
            assert _complete(client, h2, les.id).status_code == 200

        db = fx_db["db"]
        certs = db.query(Certificate).all()
        assert len(certs) == 2
        pattern = re.compile(r"^CERT-[0-9A-F]{12}$")
        for c in certs:
            assert pattern.match(c.certificate_number), c.certificate_number
        assert certs[0].certificate_number != certs[1].certificate_number


# -------------------------------------------------------------------
# #6 — Vérification email non bloquante
# -------------------------------------------------------------------
class TestEmailVerification:
    def test_register_returns_token_and_persists_it(self, client, fx_db):
        resp = client.post("/auth/register", json={
            "email": "verify_me@test.com",
            "password": STRONG_PASSWORD,
            "full_name": "Verify Me",
            "school_name": "Ecole Audit",
            "niveau_scolaire": "9eme de base",
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        token = body.get("email_verification_token")
        assert isinstance(token, str) and len(token) >= 32

        user = fx_db["db"].query(User).filter(User.email == "verify_me@test.com").first()
        assert user is not None
        assert user.email_verified is False
        assert user.email_verification_token == token

    def test_login_works_before_verification(self, client, fx_db):
        client.post("/auth/register", json={
            "email": "unverified@test.com",
            "password": STRONG_PASSWORD,
            "full_name": "Unverified",
            "school_name": "Ecole Audit",
            "niveau_scolaire": "9eme de base",
        })
        # Non bloquant : login OK sans vérification préalable
        resp = client.post("/auth/login", data={
            "username": "unverified@test.com", "password": STRONG_PASSWORD,
        })
        assert resp.status_code == 200, resp.text

    def test_verify_email_success_then_token_consumed(self, client, fx_db):
        body = client.post("/auth/register", json={
            "email": "consume@test.com",
            "password": STRONG_PASSWORD,
            "full_name": "Consume",
            "school_name": "Ecole Audit",
            "niveau_scolaire": "9eme de base",
        }).json()
        token = body["email_verification_token"]

        resp = client.post("/auth/verify-email", json={"token": token})
        assert resp.status_code == 200, resp.text
        assert resp.json()["verified"] is True

        user = fx_db["db"].query(User).filter(User.email == "consume@test.com").first()
        fx_db["db"].refresh(user)
        assert user.email_verified is True
        assert user.email_verification_token is None

        # Single-use : le même token est refusé ensuite
        resp2 = client.post("/auth/verify-email", json={"token": token})
        assert resp2.status_code == 400

    def test_verify_email_bad_token(self, client, fx_db):
        resp = client.post("/auth/verify-email", json={"token": "inexistant"})
        assert resp.status_code == 400


# -------------------------------------------------------------------
# #7 — Crédits TRIAL pour élèves créés via /api/admin/users
# -------------------------------------------------------------------
class TestAdminCreatedStudentWallet:
    def test_student_gets_trial_credits(self, client, fx_db):
        headers = _login_headers(client, fx_db["super_admin"].email)
        resp = client.post(
            "/api/admin/users",
            params={
                "email": "admin_made_student@test.com",
                "password": STRONG_PASSWORD,
                "full_name": "Admin Made Student",
                "role": "student",
                "school_id": fx_db["school"].id,
            },
            headers=headers,
        )
        assert resp.status_code in (200, 201), resp.text

        new_user = fx_db["db"].query(User).filter(
            User.email == "admin_made_student@test.com"
        ).first()
        assert new_user is not None

        # Le crédit TRIAL est une ligne du ledger (pool dédié), pas un solde DT
        txns = fx_db["db"].query(WalletTransaction).filter(
            WalletTransaction.user_id == new_user.id,
            WalletTransaction.pool == WalletPool.TRIAL,
        ).all()
        assert len(txns) == 1
        assert txns[0].amount == 100
        assert txns[0].expires_at is not None

    def test_teacher_gets_no_credits(self, client, fx_db):
        headers = _login_headers(client, fx_db["super_admin"].email)
        resp = client.post(
            "/api/admin/users",
            params={
                "email": "admin_made_teacher@test.com",
                "password": STRONG_PASSWORD,
                "full_name": "Admin Made Teacher",
                "role": "teacher",
                "school_id": fx_db["school"].id,
            },
            headers=headers,
        )
        assert resp.status_code in (200, 201), resp.text

        new_user = fx_db["db"].query(User).filter(
            User.email == "admin_made_teacher@test.com"
        ).first()
        assert new_user is not None
        txns = fx_db["db"].query(WalletTransaction).filter(
            WalletTransaction.user_id == new_user.id
        ).all()
        assert txns == []

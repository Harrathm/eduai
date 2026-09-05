"""
Tests — Priorite 1 : Securite du rattachement ecole a l'inscription.
Verifie qu'une inscription SANS school_name ne rattache JAMAIS l'eleve
a une ecole cliente existante.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import User, School, Course, CourseStatus
from app.core.security import get_password_hash

TEST_PASSWORD = "password123"


@pytest.fixture(scope="function")
def setup():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()

    # Creer une VRAIE ecole cliente (pas une ecole de demo)
    real_school = School(name="Ecole Client ABC", slug="ecole-client-abc", subscription_tier="free")
    db.add(real_school)
    db.commit()
    db.refresh(real_school)

    # Creer un cours school_only dans cette ecole
    teacher = User(
        email="teacher@test.com", hashed_password=get_password_hash(TEST_PASSWORD),
        full_name="Enseignant Test", role="teacher", school_id=real_school.id, is_active=True,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    course = Course(
        title="Cours Confidentiel Ecole ABC", slug="cours-confidentiel-abc",
        school_id=real_school.id, author_id=teacher.id,
        price=50.0, price_dt=50.0, price_tokens=0,
        visibility="school_only", status=CourseStatus.PUBLISHED, is_published=True,
        niveau_scolaire="9eme de base",
    )
    db.add(course)
    db.commit()

    yield db, real_school, course

    app.dependency_overrides.clear()


def _register(client, email, school_name=None, niveau_scolaire="9eme de base"):
    """Helper pour inscrire un eleve."""
    payload = {
        "email": email,
        "password": TEST_PASSWORD,
        "full_name": f"Eleve {email}",
        "niveau_scolaire": niveau_scolaire,
    }
    if school_name is not None:
        payload["school_name"] = school_name
    return client.post("/auth/register", json=payload)


def _login(client, email):
    resp = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    return resp.json().get("access_token")


class TestSchoolAttachmentSecurity:
    """Tests de securite pour le rattachement ecole a l'inscription."""

    def test_register_without_school_rejects(self, setup):
        """Une inscription SANS school_name doit etre REJETEE (HTTP 400)."""
        db, real_school, course = setup
        client = TestClient(app)

        resp = _register(client, "no-school@test.com", school_name=None)

        assert resp.status_code == 400, f"Attendu 400, recu {resp.status_code}: {resp.text}"
        detail = resp.json()["detail"].lower()
        assert ("school" in detail) or ("école" in detail) or ("inconnue" in detail), (
            f"Message inattendu: {detail}"
        )

    def test_register_without_school_does_not_attach_to_existing(self, setup):
        """Apres un rejet, aucun user ne doit exister avec l'ecole cliente."""
        db, real_school, course = setup
        client = TestClient(app)

        _register(client, "no-school@test.com", school_name=None)

        user = db.query(User).filter(User.email == "no-school@test.com").first()
        assert user is None, "Le user ne doit PAS etre cree sans school_name"

    def test_register_with_unknown_school_name_rejected(self, setup):
        """SECURITY FIX #1 : une inscription avec un school_name INCONNU est
        REJETEE (HTTP 400) — /register ne cree plus JAMAIS d'ecole.
        La creation d'ecole passe exclusivement par /auth/register-school."""
        db, real_school, course = setup
        client = TestClient(app)

        schools_before = db.query(School).count()

        resp = _register(client, "new-school@test.com", school_name="Ma Nouvelle Ecole")
        assert resp.status_code in (400, 404), f"Attendu 400/404, recu {resp.status_code}: {resp.text}"

        user = db.query(User).filter(User.email == "new-school@test.com").first()
        assert user is None, "Le user ne doit PAS etre cree pour une ecole inconnue"
        assert db.query(School).count() == schools_before, (
            "Aucune ecole ne doit etre creee par /auth/register"
        )

    def test_register_with_existing_domain_finds_correct_school(self, setup):
        """Une inscription avec un domain existant trouve la bonne ecole."""
        db, real_school, course = setup
        client = TestClient(app)

        # Definir un domain sur l'ecole existante
        real_school.domain = "ecole-abc"
        db.commit()

        resp = _register(client, "domain-test@test.com", school_name="ecole-abc")
        assert resp.status_code == 200

        user = db.query(User).filter(User.email == "domain-test@test.com").first()
        assert user.school_id == real_school.id

    def test_new_user_cannot_access_school_only_content_of_real_school(self, setup):
        """Un eleve inscrit dans une AUTRE ecole (existante, active) ne peut PAS
        voir le contenu school_only de l'ecole cliente."""
        db, real_school, course = setup
        client = TestClient(app)

        # Creer une seconde ecole ACTIVE existante, puis s'y inscrire par son nom
        other_school = School(name="Autre Ecole", slug="autre-ecole", subscription_tier="free")
        db.add(other_school)
        db.commit()

        resp = _register(client, "other-school@test.com", school_name="Autre Ecole")
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Tenter d'acceder au cours school_only de l'ecole cliente
        resp = client.get(f"/api/learner/courses/{course.id}", headers=headers)
        # Doit etre 403 (pas de access) car le cours est school_only dans une autre ecole
        assert resp.status_code in (403, 404), (
            f"Un eleve d'une autre ecole ne doit PAS acceder au cours school_only. "
            f"Recu: {resp.status_code}"
        )

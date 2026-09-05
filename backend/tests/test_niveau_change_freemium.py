"""
Tests preuve-based : Garantie Freemium au changement de niveau.

Cause racine diagnostiquée (student3@eduai.edu) : PUT /api/users/me avec un
nouveau niveau_scolaire invalidait TOUS les abonnements actifs sans
remplacement → élève sans aucun accès (mon-parcours/dashboard vides).

Correctif : après invalidation, ensure_free_abonnement() re-crée un
Abonnement "gratuit" actif sur le nouveau niveau.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.models import User, School, PackDefinition, Abonnement
from app.core.security import get_password_hash

from tests.conftest import TEST_PASSWORD


@pytest.fixture(scope="function")
def fr_db(_base_session):
    db = _base_session

    school = School(name="Ecole FR", slug="ecole-fr")
    db.add(school)
    db.commit()
    db.refresh(school)

    student = User(
        email="fr_student@test.com", hashed_password=get_password_hash(TEST_PASSWORD),
        full_name="FR Student", role="student", is_active=True, is_approved=True,
        school_id=school.id, niveau_scolaire="Niveau A",
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    free_a = PackDefinition(nom="Gratuit A", tier="gratuit", niveau_scolaire="Niveau A", est_actif=True)
    free_b = PackDefinition(nom="Gratuit B", tier="gratuit", niveau_scolaire="Niveau B", est_actif=True)
    silver_a = PackDefinition(nom="Silver A", tier="silver", niveau_scolaire="Niveau A", prix_tnd=30, est_actif=True)
    db.add_all([free_a, free_b, silver_a])
    db.commit()
    db.refresh(free_a)
    db.refresh(free_b)
    db.refresh(silver_a)

    yield {
        "db": db, "school": school, "student": student,
        "free_a": free_a, "free_b": free_b, "silver_a": silver_a,
    }


@pytest.fixture(scope="function")
def client(fr_db):
    return TestClient(app)


def _login(client, email):
    resp = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _actives(db, user_id):
    return db.query(Abonnement).filter(
        Abonnement.user_id == user_id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).all()


class TestChangeNiveauFreemium:
    def test_paid_invalidated_then_free_recreated(self, client, fr_db):
        """Changement de niveau avec abonnement payant :
        l'ancien passe à 'invalide' ET un gratuit actif est recréé sur le
        nouveau niveau — l'élève n'est JAMAIS sans abonnement actif."""
        db, student = fr_db["db"], fr_db["student"]

        paid = Abonnement(
            user_id=student.id, pack_id=fr_db["silver_a"].id,
            statut="actif",
            debut=datetime.now(timezone.utc),
            fin=datetime.now(timezone.utc) + timedelta(days=90),
        )
        db.add(paid)
        db.commit()

        headers = _login(client, student.email)
        resp = client.put("/api/users/me", json={"niveau_scolaire": "Niveau B"}, headers=headers)
        assert resp.status_code == 200, resp.text

        db.refresh(paid)
        assert paid.statut == "invalide", "L'ancien abonnement payant doit être invalidé"

        actives = _actives(db, student.id)
        assert len(actives) == 1, f"Un seul abonnement actif attendu, trouvé {len(actives)}"
        assert actives[0].pack_id == fr_db["free_b"].id
        assert actives[0].statut == "actif"
        # Cohérence pack ↔ nouveau niveau de l'élève
        db.refresh(student)
        assert actives[0].pack.niveau_scolaire == student.niveau_scolaire == "Niveau B"

    def test_matching_pack_not_invalidated(self, client, fr_db):
        """Si le pack correspond déjà au nouveau niveau, rien n'est invalidé."""
        db, student = fr_db["db"], fr_db["student"]
        # L'élève est sur "Niveau A" ; on le fait passer à "Niveau A" (aucun changement réel)
        # puis on vérifie qu'un abonnement gratuit reste intact après re-PUT du même niveau.
        free = Abonnement(
            user_id=student.id, pack_id=fr_db["free_a"].id,
            statut="actif",
            debut=datetime.now(timezone.utc),
            fin=datetime.now(timezone.utc) + timedelta(days=365),
        )
        db.add(free)
        db.commit()

        headers = _login(client, student.email)
        resp = client.put("/api/users/me", json={"niveau_scolaire": "Niveau A"}, headers=headers)
        assert resp.status_code == 200

        db.refresh(free)
        assert free.statut == "actif"
        assert _actives(db, student.id)[0].id == free.id

    def test_no_duplicate_free_on_repeat_change(self, client, fr_db):
        """Changer deux fois de niveau ne cumule pas les abonnements gratuits."""
        db, student = fr_db["db"], fr_db["student"]
        headers = _login(client, student.email)

        r1 = client.put("/api/users/me", json={"niveau_scolaire": "Niveau B"}, headers=headers)
        assert r1.status_code == 200
        r2 = client.put("/api/users/me", json={"niveau_scolaire": "Niveau A"}, headers=headers)
        assert r2.status_code == 200

        actives = _actives(db, student.id)
        assert len(actives) == 1
        assert actives[0].pack_id == fr_db["free_a"].id

    def test_register_still_attaches_free_abonnement(self, client, fr_db):
        """Régression : l'inscription attache toujours le gratuit (service partagé)."""
        resp = client.post("/auth/register", json={
            "email": "newkid@test.com",
            "password": "Str0ng!Passw0rd",
            "full_name": "New Kid",
            "school_name": "Ecole FR",
            "niveau_scolaire": "Niveau A",
        })
        assert resp.status_code == 200, resp.text

        db = fr_db["db"]
        user = db.query(User).filter(User.email == "newkid@test.com").first()
        assert user is not None
        actives = _actives(db, user.id)
        assert len(actives) == 1
        assert actives[0].pack_id == fr_db["free_a"].id
